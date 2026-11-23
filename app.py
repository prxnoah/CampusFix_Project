from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, re
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['AI_ENABLED'] = bool(os.environ.get('OPENAI_API_KEY'))
# Keep uploads predictable and prevent oversized multipart requests from crashing the app.
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
app.secret_key = os.environ.get("SECRET_KEY", "campusfix-demo-secret")
DB = os.path.join(os.path.dirname(__file__), "campusfix.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

UNIVERSITY_NAME = "Lyceum of the Philippines University – Manila"
CAMPUS_ADDRESS = "Muralla cor. Real Sts., Intramuros, Manila 1002"

ROLE_LABELS = {
    "student": "Student",
    "faculty": "Faculty / Instructor",
    "staff": "Staff",
    "maintenance": "Maintenance Personnel",
    "supervisor": "Maintenance Supervisor",
    "admin": "School Administrator",
}

STATUSES = ["Reported", "Under Review", "In Progress", "Resolved"]
CATEGORIES = ["Electrical", "Plumbing", "HVAC", "Internet / Network", "Furniture",
              "Safety Hazard", "Building Damage", "Classroom Equipment", "Sanitation", "Other"]
BUILDINGS = [
    "Sotero H. Laurel Academic Resource Center (SHL-ARC)",
    "JPL Hall of Freedom",
    "Administration Building",
    "Admissions Information Center – Room 102A",
    "Office of the University Registrar – Room 104A",
    "Mini Theater",
    "Bookstore",
    "College of Technology",
    "College of Arts and Sciences",
    "College of Business Administration",
    "College of International Relations",
    "College of International Tourism and Hospitality Management",
    "College of Law",
    "Graduate School",
    "Campus Grounds / Walkways",
    "Other Campus Area"
]
SEVERITIES = ["Low", "Moderate", "High"]

def db():
    # Give SQLite enough time to finish a short concurrent read/write instead of
    # immediately failing a real report submission with a generic save error.
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
      role TEXT NOT NULL, department TEXT, user_id_code TEXT,
      contact_number TEXT, profile_photo TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reports (
      id INTEGER PRIMARY KEY AUTOINCREMENT, report_code TEXT UNIQUE NOT NULL,
      category TEXT NOT NULL, building TEXT NOT NULL, room_area TEXT,
      severity TEXT NOT NULL, description TEXT NOT NULL, date_noticed TEXT,
      reporter_id INTEGER, assigned_to INTEGER, status TEXT DEFAULT 'Reported',
      priority TEXT DEFAULT 'Medium', duplicate_count INTEGER DEFAULT 0,
      additional_details TEXT, photo_path TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS report_updates (
      id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL,
      user_id INTEGER, old_status TEXT, new_status TEXT, note TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      title TEXT NOT NULL, message TEXT NOT NULL, is_read INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS announcements (
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
      summary TEXT, category TEXT, published_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Lightweight migrations for databases created by earlier CampusFix versions.
    # Older copies of the project may already have campusfix.db, so make sure every
    # column required by the current reporting workflow exists before accepting a POST.
    migrations = {
        "reports": [
            ("assigned_to", "INTEGER"), ("status", "TEXT DEFAULT 'Reported'"),
            ("priority", "TEXT DEFAULT 'Medium'"), ("duplicate_count", "INTEGER DEFAULT 0"),
            ("additional_details", "TEXT"), ("photo_path", "TEXT"),
            ("resolution_note", "TEXT"), ("resolution_photo_path", "TEXT"),
            ("resolved_at", "TEXT"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
        "report_updates": [
            ("old_status", "TEXT"), ("new_status", "TEXT"), ("note", "TEXT"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
        "notifications": [
            ("is_read", "INTEGER DEFAULT 0"),
            ("created_at", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ],
    }
    for table, columns in migrations.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for column, definition in columns:
            if column not in existing:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                except sqlite3.OperationalError as exc:
                    # A concurrent initialization can race harmlessly; the later
                    # schema check will see the column if it was created.
                    if "duplicate column" not in str(exc).lower():
                        raise
    conn.commit()

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        demos = [
            ("Alex Santos","student@campusfix.local","student","Computer Science","2026-001","09170000001"),
            ("Mia Reyes","faculty@campusfix.local","faculty","College of Engineering","EMP-1042","09170000002"),
            ("Chris Dela Cruz","staff@campusfix.local","staff","College of Technology","STF-203","09170000003"),
            ("Jordan Cruz","maintenance@campusfix.local","maintenance","Facilities Management","FM-021","09170000004"),
            ("Sam Rivera","supervisor@campusfix.local","supervisor","Facilities Management","SUP-008","09170000005"),
            ("Taylor Garcia","admin@campusfix.local","admin","Office of the University Administrator","ADM-001","09170000006"),
        ]
        for name,email,role,dept,code,phone in demos:
            conn.execute("INSERT INTO users(full_name,email,password_hash,role,department,user_id_code,contact_number) VALUES(?,?,?,?,?,?,?)",
                         (name,email,generate_password_hash("password123"),role,dept,code,phone))
    if conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
        announcements = [
            ("LPU Manila BSIT Program Earns PICAB Accreditation", "The College of Technology celebrates the accreditation of the Bachelor of Science in Information Technology program by PICAB.", "Academic Excellence"),
            ("LPU Manila Faculty and Staff Earn Microsoft Elevate Recognition", "LPU Manila celebrates faculty and staff recognized as Microsoft Elevate for Educator Experts for AY 2026–2027.", "University News"),
            ("LPU Manila and UCSI University Explore Academic Collaboration", "The universities signed a letter of intent to explore opportunities for academic collaboration and global engagement.", "Global Engagement"),
            ("CampusFix is now live for campus maintenance reports", "Students and faculty can report facility concerns, follow status changes and receive maintenance updates through CampusFix.", "CampusFix"),
        ]
        for a in announcements:
            conn.execute("INSERT INTO announcements(title,summary,category) VALUES(?,?,?)", a)
    conn.commit()
    conn.close()

def current_user():
    uid = session.get("user_id")
    if not uid: return None
    conn=db(); u=conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone(); conn.close()
    return u

@app.context_processor
def inject_globals():
    u=current_user()
    unread=0
    if u:
        conn=db(); unread=conn.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0",(u["id"],)).fetchone()[0]; conn.close()
    return dict(current_user=u, unread_notifications=unread, role_labels=ROLE_LABELS)

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

def make_report_code():
    """Create a human-readable report ID and guarantee it is unique in SQLite."""
    stamp = datetime.now().strftime("%y%m%d%H%M%S%f")
    base = "CF-" + stamp[:14]
    conn = db()
    try:
        code = base
        suffix = 1
        while conn.execute("SELECT 1 FROM reports WHERE report_code=?", (code,)).fetchone():
            code = f"{base}-{suffix}"
            suffix += 1
        return code
    finally:
        conn.close()

def calculate_priority(severity, category, duplicate_count):
    score={"Low":1,"Moderate":2,"High":3}.get(severity,2)
    if category=="Safety Hazard": score += 2
    if category in ["Electrical","Plumbing"]: score += 1
    score += min(duplicate_count,3)
    return "Urgent" if score>=7 else "High" if score>=5 else "Medium" if score>=3 else "Low"

def notify(user_id, title, message, conn=None):
    # Use the caller's connection when available. This avoids SQLite lock conflicts
    # during report creation and keeps notification creation in the same transaction.
    if not user_id:
        return False
    own_conn = conn is None
    work_conn = conn or db()
    try:
        work_conn.execute(
            "INSERT INTO notifications(user_id,title,message) VALUES(?,?,?)",
            (user_id, title, message)
        )
        if own_conn:
            work_conn.commit()
        return True
    except sqlite3.Error as exc:
        app.logger.warning("CampusFix notification could not be created: %s", exc)
        if own_conn:
            work_conn.rollback()
        return False
    finally:
        if own_conn:
            work_conn.close()

@app.route("/")
def home():
    conn=db()
    announcements=conn.execute("SELECT * FROM announcements ORDER BY published_at DESC LIMIT 4").fetchall()
    active=conn.execute("SELECT COUNT(*) FROM reports WHERE status NOT IN ('Resolved','Closed')").fetchone()[0]
    resolved=conn.execute("SELECT COUNT(*) FROM reports WHERE status IN ('Resolved','Closed')").fetchone()[0]
    recent=conn.execute("""SELECT r.*, u.full_name reporter FROM reports r
        LEFT JOIN users u ON r.reporter_id=u.id ORDER BY r.created_at DESC LIMIT 6""").fetchall()
    category_counts=conn.execute("SELECT category, COUNT(*) count FROM reports GROUP BY category ORDER BY count DESC LIMIT 6").fetchall()
    conn.close()
    return render_template("public/home.html", announcements=announcements, active=active, resolved=resolved,
                           recent=recent, category_counts=category_counts, university_name=UNIVERSITY_NAME, campus_address=CAMPUS_ADDRESS)

@app.route("/about")
def about(): return render_template("public/about.html")
@app.route("/admissions")
def admissions(): return render_template("public/admissions.html")
@app.route("/academics")
def academics(): return render_template("public/academics.html")
@app.route("/colleges")
def colleges(): return render_template("public/colleges.html")
@app.route("/news")
def news():
    conn=db(); items=conn.execute("SELECT * FROM announcements ORDER BY published_at DESC").fetchall(); conn.close()
    return render_template("public/news.html", announcements=items)
@app.route("/events")
def events(): return render_template("public/events.html")
@app.route("/facilities")
def facilities(): return render_template("public/facilities.html")
@app.route("/faq")
def faq(): return render_template("public/faq.html")
@app.route("/contact")
def contact(): return render_template("public/contact.html")
@app.route("/help")
def help_page(): return render_template("public/help.html")
@app.route("/resources")
def resources(): return render_template("public/resources.html")
@app.route("/faculty-directory")
def faculty_directory():
    conn=db(); faculty=conn.execute("SELECT * FROM users WHERE role='faculty' ORDER BY full_name").fetchall(); conn.close()
    return render_template("public/faculty.html", faculty=faculty)
@app.route("/campus-map")
def campus_map():
    return render_template("public/campus_map.html", university_name=UNIVERSITY_NAME, campus_address=CAMPUS_ADDRESS)

@app.route("/campus-status")
def campus_status():
    conn=db()
    rows=conn.execute("""SELECT building,
        SUM(CASE WHEN status NOT IN ('Resolved','Closed') THEN 1 ELSE 0 END) active,
        SUM(CASE WHEN status IN ('Resolved','Closed') THEN 1 ELSE 0 END) resolved
        FROM reports GROUP BY building ORDER BY active DESC""").fetchall()
    conn.close()
    return render_template("public/status.html", buildings=rows)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        conn=db(); u=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); conn.close()
        if u and check_password_hash(u["password_hash"], password):
            session["user_id"]=u["id"]
            flash(f"Welcome back, {u['full_name'].split()[0]}!", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("The email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        fields=[request.form.get(x,"").strip() for x in ["full_name","email","password","confirm_password","user_id_code","department","contact_number"]]
        name,email,pw,cpw,code,dept,phone=fields
        selected_role=request.form.get("role","student").strip().lower()
        if selected_role not in ("student","faculty","staff"):
            selected_role="student"
        if not all(fields):
            flash("Please complete all required fields.", "error")
        elif pw != cpw:
            flash("Passwords do not match.", "error")
        elif not re.match(r"^[^@\s]+@campusfix\.local$", email):
            flash("Please use a CampusFix university email ending in @campusfix.local.", "error")
        else:
            try:
                conn=db(); conn.execute("""INSERT INTO users(full_name,email,password_hash,role,department,user_id_code,contact_number)
                    VALUES(?,?,?,?,?,?,?)""",(name,email,generate_password_hash(pw),selected_role,dept,code,phone)); conn.commit()
                uid=conn.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()["id"]; conn.close()
                session["user_id"]=uid; flash("Account created successfully.", "success")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("That university email is already registered.", "error")
    return render_template("auth.html", mode="register")

@app.route("/logout")
def logout():
    session.clear(); flash("You have been signed out.", "info"); return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    u=current_user()
    if u["role"] in ("maintenance","supervisor"): return redirect(url_for("operations"))
    if u["role"]=="admin": return redirect(url_for("admin_dashboard"))
    conn=db()
    reports=conn.execute("""SELECT r.*, u.full_name reporter, a.full_name assignee
        FROM reports r LEFT JOIN users u ON r.reporter_id=u.id LEFT JOIN users a ON r.assigned_to=a.id
        WHERE r.reporter_id=? ORDER BY r.created_at DESC""",(u["id"],)).fetchall()
    stats={
        "total":len(reports),
        "active":sum(r["status"] not in ("Resolved","Closed") for r in reports),
        "resolved":sum(r["status"] in ("Resolved","Closed") for r in reports),
        "high":sum(r["priority"] in ("High","Urgent") for r in reports)
    }
    conn.close()
    return render_template("dashboard/user.html", reports=reports, stats=stats)

@app.route("/operations")
@login_required
def operations():
    u=current_user()
    if u["role"] not in ("maintenance","supervisor","admin"):
        return redirect(url_for("dashboard"))
    conn=db()
    q=request.args.get("q","").strip()
    status_filter=request.args.get("status","").strip()
    priority_filter=request.args.get("priority","").strip()
    clauses=[]; args=[]
    if u["role"]=="maintenance":
        clauses.append("(r.assigned_to=? OR (r.assigned_to IS NULL AND r.status='Reported'))")
        args.append(u["id"])
    if q:
        clauses.append("(r.report_code LIKE ? OR r.category LIKE ? OR r.building LIKE ? OR r.room_area LIKE ? OR r.description LIKE ?)")
        like=f"%{q}%"; args.extend([like]*5)
    if status_filter in STATUSES:
        clauses.append("r.status=?"); args.append(status_filter)
    if priority_filter in ("Urgent","High","Medium","Low"):
        clauses.append("r.priority=?"); args.append(priority_filter)
    where=("WHERE "+" AND ".join(clauses)) if clauses else ""
    reports=conn.execute(f"""SELECT r.*, p.full_name reporter, a.full_name assignee
        FROM reports r LEFT JOIN users p ON r.reporter_id=p.id LEFT JOIN users a ON r.assigned_to=a.id
        {where}
        ORDER BY CASE r.priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                 CASE r.status WHEN 'Reported' THEN 1 WHEN 'Under Review' THEN 2 WHEN 'In Progress' THEN 3 ELSE 4 END,
                 r.created_at DESC""",args).fetchall()
    counts={
        "open":conn.execute("SELECT COUNT(*) FROM reports WHERE status NOT IN ('Resolved','Closed')").fetchone()[0],
        "review":conn.execute("SELECT COUNT(*) FROM reports WHERE status='Reported'").fetchone()[0],
        "urgent":conn.execute("SELECT COUNT(*) FROM reports WHERE priority='Urgent' AND status NOT IN ('Resolved','Closed')").fetchone()[0],
        "unassigned":conn.execute("SELECT COUNT(*) FROM reports WHERE assigned_to IS NULL AND status NOT IN ('Resolved','Closed')").fetchone()[0],
        "done":conn.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'").fetchone()[0],
    }
    staff=conn.execute("SELECT id,full_name FROM users WHERE role='maintenance' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("dashboard/operations.html", reports=reports, counts=counts, staff=staff,
                           query=q, status_filter=status_filter, priority_filter=priority_filter,
                           categories=CATEGORIES, statuses=STATUSES, role=u["role"])

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user()["role"]!="admin": return redirect(url_for("dashboard"))
    conn=db()
    total=conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    open_count=conn.execute("SELECT COUNT(*) FROM reports WHERE status NOT IN ('Resolved','Closed')").fetchone()[0]
    resolved=conn.execute("SELECT COUNT(*) FROM reports WHERE status IN ('Resolved','Closed')").fetchone()[0]
    pending=conn.execute("SELECT COUNT(*) FROM reports WHERE status='Reported'").fetchone()[0]
    unassigned=conn.execute("SELECT COUNT(*) FROM reports WHERE assigned_to IS NULL AND status NOT IN ('Resolved','Closed')").fetchone()[0]
    urgent=conn.execute("SELECT COUNT(*) FROM reports WHERE priority='Urgent' AND status NOT IN ('Resolved','Closed')").fetchone()[0]
    users=conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    overdue=conn.execute("""SELECT COUNT(*) FROM reports
        WHERE status NOT IN ('Resolved','Closed') AND datetime(created_at) <= datetime('now','-3 days')""").fetchone()[0]
    avg_row=conn.execute("""SELECT AVG((julianday(resolved_at)-julianday(created_at))*24)
        FROM reports WHERE resolved_at IS NOT NULL""").fetchone()[0]
    avg_hours=round(avg_row,1) if avg_row is not None else 0
    by_cat=conn.execute("SELECT category,COUNT(*) c FROM reports GROUP BY category ORDER BY c DESC").fetchall()
    by_build=conn.execute("SELECT building,COUNT(*) c FROM reports GROUP BY building ORDER BY c DESC").fetchall()
    recent=conn.execute("""SELECT r.*,u.full_name reporter,a.full_name assignee
        FROM reports r LEFT JOIN users u ON r.reporter_id=u.id LEFT JOIN users a ON r.assigned_to=a.id
        ORDER BY r.created_at DESC LIMIT 10""").fetchall()
    conn.close()
    rate=round((resolved/total*100),1) if total else 0
    return render_template("dashboard/admin.html", total=total,open_count=open_count,resolved=resolved,users=users,rate=rate,
                           pending=pending,unassigned=unassigned,urgent=urgent,overdue=overdue,avg_hours=avg_hours,
                           by_cat=by_cat,by_build=by_build,recent=recent)

@app.route("/reports/new", methods=["GET","POST"])
@login_required
def new_report():
    if request.method=="POST":
        u=current_user()
        category=request.form.get("category", "").strip(); building=request.form.get("building", "").strip(); room=request.form.get("room_area", "").strip()
        severity=request.form.get("severity", "").strip(); desc=request.form.get("description", "").strip(); noticed=request.form.get("date_noticed", "").strip()
        additional=request.form.get("additional_details", "").strip()
        if (category not in CATEGORIES or building not in BUILDINGS or severity not in SEVERITIES
                or len(desc) < 10 or not noticed):
            flash("Please complete the required report details before submitting.", "error")
            return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)
        photo=request.files.get("photo")
        photo_path=None
        saved_photo_abs=None

        # Save evidence safely. A bad/failed upload returns to the form instead
        # of exposing the Flask debugger.
        if photo and photo.filename:
            ext=photo.filename.rsplit('.',1)[-1].lower() if '.' in photo.filename else ''
            mimetype=(photo.mimetype or '').lower()
            allowed_mimes={
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "gif": "image/gif",
                "webp": "image/webp",
            }
            if ext not in ALLOWED_IMAGE_EXTENSIONS or mimetype not in ("", allowed_mimes.get(ext)):
                flash("Please upload a JPG, PNG, GIF, or WEBP image.", "error")
                return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)

            safe=secure_filename(photo.filename)
            if not safe:
                flash("That image filename could not be processed. Please rename the file and try again.", "error")
                return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)

            filename=f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe}"
            saved_photo_abs=os.path.join(UPLOAD_DIR, filename)
            try:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                photo.save(saved_photo_abs)
                if not os.path.isfile(saved_photo_abs) or os.path.getsize(saved_photo_abs) == 0:
                    raise OSError("Uploaded image was not saved correctly.")
                photo_path=f"uploads/{filename}"
            except (OSError, ValueError) as exc:
                app.logger.warning("CampusFix photo upload failed: %s", exc)
                if saved_photo_abs and os.path.exists(saved_photo_abs):
                    try: os.remove(saved_photo_abs)
                    except OSError: pass
                flash("The photo could not be uploaded. Please try another image (JPG, PNG, GIF, or WEBP).", "error")
                return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)

        conn=None
        try:
            conn=db()
            duplicate=conn.execute(
                "SELECT COUNT(*) c FROM reports WHERE building=? AND category=? AND status NOT IN ('Resolved','Closed')",
                (building,category)
            ).fetchone()["c"]
            priority=calculate_priority(severity,category,duplicate)
            code=make_report_code()
            conn.execute(
                "INSERT INTO reports(report_code,category,building,room_area,severity,description,date_noticed,reporter_id,priority,duplicate_count,additional_details,photo_path) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (code,category,building,room,severity,desc,noticed,u["id"],priority,duplicate,additional,photo_path)
            )
            rid=conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO report_updates(report_id,user_id,new_status,note) VALUES(?,?,?,?)",
                (rid,u["id"],"Reported","Report submitted by campus user. Report details validated and queued for review.")
            )
            # Create notifications using this same connection. This prevents SQLite
            # from opening a second writer while the report transaction is active.
            recipients = conn.execute(
                "SELECT id FROM users WHERE role IN ('maintenance','supervisor','admin')"
            ).fetchall()
            for recipient in recipients:
                notify(
                    recipient["id"],
                    f"New CampusFix report {code}",
                    f"A new {category} report was submitted for {building}. Severity: {severity}.",
                    conn=conn
                )
            conn.commit()
        except Exception as exc:
            if conn:
                conn.rollback()
            if saved_photo_abs and os.path.exists(saved_photo_abs):
                try: os.remove(saved_photo_abs)
                except OSError: pass
            app.logger.exception("CampusFix report creation failed: %s", exc)
            flash("The report could not be saved right now. Please try again.", "error")
            return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)
        finally:
            if conn:
                conn.close()

        flash(f"Report {code} submitted successfully.", "success")
        return redirect(url_for("report_detail", report_id=rid))
    return render_template("dashboard/report_form.html", categories=CATEGORIES, buildings=BUILDINGS, severities=SEVERITIES)

@app.route("/reports/<int:report_id>")
@login_required
def report_detail(report_id):
    conn=db()
    r=conn.execute("""SELECT r.*,p.full_name reporter,p.email reporter_email,a.full_name assignee
                      FROM reports r LEFT JOIN users p ON r.reporter_id=p.id LEFT JOIN users a ON r.assigned_to=a.id
                      WHERE r.id=?""",(report_id,)).fetchone()
    if not r: conn.close(); return "Report not found",404
    u=current_user()
    reporter_roles = ("student", "faculty", "staff")
    if u["role"] in reporter_roles and r["reporter_id"] != u["id"]:
        conn.close(); return "Access denied",403
    timeline=conn.execute("""SELECT ru.*,u.full_name FROM report_updates ru LEFT JOIN users u ON ru.user_id=u.id
                             WHERE report_id=? ORDER BY created_at""",(report_id,)).fetchall()
    staff=conn.execute("SELECT id,full_name FROM users WHERE role='maintenance' ORDER BY full_name").fetchall()
    conn.close()
    return render_template("dashboard/report_detail.html",report=r,timeline=timeline,staff=staff,statuses=STATUSES)

@app.route("/reports/<int:report_id>/update", methods=["POST"])
@login_required
def update_report(report_id):
    u=current_user()
    if u["role"] not in ("maintenance","supervisor","admin"):
        return "Forbidden",403
    new_status=request.form.get("status","").strip()
    note=request.form.get("note","").strip()
    assignee=request.form.get("assigned_to") or None
    resolution_note=request.form.get("resolution_note","").strip()
    resolution_photo=request.files.get("resolution_photo")
    if new_status not in STATUSES:
        flash("Invalid report status.","error")
        return redirect(url_for("report_detail",report_id=report_id))
    conn=db(); old=None; saved_resolution_abs=None
    try:
        r=conn.execute("SELECT * FROM reports WHERE id=?",(report_id,)).fetchone()
        if not r: return "Not found",404
        old=r["status"]
        allowed_next={"Reported":{"Reported","Under Review"},"Under Review":{"Under Review","In Progress"},
                      "In Progress":{"In Progress","Resolved"},"Resolved":{"Resolved"}}
        if new_status not in allowed_next.get(old,{old}):
            flash(f"This report is currently {old}. It must move to the next stage before it can be marked {new_status}.","error")
            return redirect(url_for("report_detail",report_id=report_id))
        if new_status in ("In Progress","Resolved") and not assignee:
            assignee=r["assigned_to"]
        if new_status in ("In Progress","Resolved") and not assignee:
            flash("Assign a maintenance personnel before moving this report to In Progress or Resolved.","error")
            return redirect(url_for("report_detail",report_id=report_id))

        resolution_photo_path=r["resolution_photo_path"] if "resolution_photo_path" in r.keys() else None
        if resolution_photo and resolution_photo.filename:
            ext=resolution_photo.filename.rsplit(".",1)[-1].lower() if "." in resolution_photo.filename else ""
            mimetype=(resolution_photo.mimetype or "").lower()
            allowed_mimes={"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg","gif":"image/gif","webp":"image/webp"}
            if ext not in ALLOWED_IMAGE_EXTENSIONS or mimetype not in ("",allowed_mimes.get(ext)):
                flash("Resolution evidence must be a JPG, PNG, GIF, or WEBP image.","error")
                return redirect(url_for("report_detail",report_id=report_id))
            safe=secure_filename(resolution_photo.filename)
            if not safe:
                flash("The resolution photo filename is not valid.","error")
                return redirect(url_for("report_detail",report_id=report_id))
            upload_dir=os.path.join(app.static_folder,"uploads"); os.makedirs(upload_dir,exist_ok=True)
            filename=f"resolution_{report_id}_{uuid.uuid4().hex[:10]}_{safe}"
            saved_resolution_abs=os.path.join(upload_dir,filename)
            resolution_photo.save(saved_resolution_abs)
            resolution_photo_path=f"uploads/{filename}"

        if new_status=="Resolved" and old!="Resolved" and not (resolution_note or note or resolution_photo_path):
            flash("Add a resolution note or upload resolution evidence before marking this report Resolved.","error")
            return redirect(url_for("report_detail",report_id=report_id))

        resolution_note_value=resolution_note or (note if new_status=="Resolved" else (r["resolution_note"] if "resolution_note" in r.keys() else None))
        if new_status=="Resolved":
            conn.execute("""UPDATE reports SET status=?,assigned_to=?,resolution_note=?,resolution_photo_path=?,resolved_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                         (new_status,assignee,resolution_note_value,resolution_photo_path,report_id))
        else:
            conn.execute("""UPDATE reports SET status=?,assigned_to=?,resolution_note=?,resolution_photo_path=?,resolved_at=NULL,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                         (new_status,assignee,resolution_note_value,resolution_photo_path,report_id))
        default_notes={"Under Review":"Report reviewed by authorized CampusFix personnel. The submitted details and evidence are being evaluated.",
                       "In Progress":"Maintenance work has started on this reported concern.",
                       "Resolved":"Maintenance work has been completed and the resolution evidence was recorded."}
        status_note=note or resolution_note or default_notes.get(new_status,f"Report remains {new_status}.")
        conn.execute("INSERT INTO report_updates(report_id,user_id,old_status,new_status,note) VALUES(?,?,?,?,?)",
                     (report_id,u["id"],old,new_status,status_note))
        if r["reporter_id"]:
            notify(r["reporter_id"],f"CampusFix {r['report_code']} updated",f"Your report is now {new_status}.",conn=conn)
        if assignee and assignee != u["id"]:
            notify(assignee,f"Report {r['report_code']} assigned",
                   f"{r['category']} at {r['building']} is now assigned to you. Current status: {new_status}.",conn=conn)
        conn.commit()
    except (sqlite3.Error,OSError) as exc:
        conn.rollback()
        if saved_resolution_abs and os.path.exists(saved_resolution_abs):
            try: os.remove(saved_resolution_abs)
            except OSError: pass
        app.logger.exception("CampusFix report update failed: %s",exc)
        flash("The report update could not be saved right now. Please try again.","error")
    finally:
        conn.close()
    if old is None: return redirect(url_for("report_detail",report_id=report_id))
    flash("Report details saved successfully." if new_status==old else f"Report moved from {old} to {new_status}.","success")
    return redirect(url_for("report_detail",report_id=report_id))

@app.route("/notifications")
@login_required
def notifications():
    u=current_user(); conn=db()
    items=conn.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC",(u["id"],)).fetchall()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",(u["id"],)); conn.commit(); conn.close()
    return render_template("dashboard/notifications.html",items=items)

@app.route("/profile")
@login_required
def profile(): return render_template("dashboard/profile.html", user=current_user())

@app.route("/api/ai-help", methods=["POST"])
def ai_help():
    """Real CampusFix AI endpoint. The UI is only exposed when an OpenAI API key is configured."""
    if not app.config.get("AI_ENABLED"):
        return jsonify({"error": "AI assistant is not configured."}), 503

    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    if not isinstance(messages, list):
        messages = []
    # Keep the request small and only accept normal text messages.
    clean = []
    for item in messages[-12:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            clean.append({"role": role, "content": content[:4000]})
    if not clean:
        clean = [{"role": "user", "content": "Hello. What can you help me with?"}]

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
            instructions=(
                "You are CampusFix AI, the real conversational assistant for a campus maintenance reporting website "
                "for Lyceum of the Philippines University Manila. Answer the user's actual question directly; do not "
                "just repeat reporting tips. You can explain CampusFix features, help identify issue categories, "
                "estimate severity from the information given, improve report wording, suggest useful location details, "
                "and answer general questions when relevant. If the user asks something outside your reliable scope, "
                "say so clearly instead of inventing facts. Never claim you submitted, assigned, or resolved a report. "
                "For emergencies or immediate danger, advise contacting campus security/emergency services instead of "
                "relying on the website. Keep responses friendly, concise, and easy for a student to understand."
            ),
            input=clean
        )
        return jsonify({"reply": response.output_text})
    except Exception as exc:
        app.logger.warning("CampusFix AI unavailable: %s", exc)
        return jsonify({"error": "The AI assistant is temporarily unavailable."}), 503

@app.route("/api/stats")
def api_stats():
    conn=db()
    by_cat=conn.execute("SELECT category,COUNT(*) count FROM reports GROUP BY category").fetchall()
    by_build=conn.execute("SELECT building,COUNT(*) count FROM reports GROUP BY building").fetchall()
    conn.close()
    return jsonify({"categories":[dict(x) for x in by_cat],"buildings":[dict(x) for x in by_build]})

@app.errorhandler(413)
def request_too_large(e):
    return render_template(
        "error.html",
        code=413,
        message="The uploaded file is too large. Please use an image smaller than 8 MB and try again."
    ), 413

@app.errorhandler(404)
def not_found(e): return render_template("error.html", code=404, message="The page you are looking for could not be found."),404

init_db()
if __name__=="__main__":
    app.run(debug=True)
