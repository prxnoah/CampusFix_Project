# LPU Manila CampusFix – University Portal Edition

A Flask + SQLite/MySQL university portal and CampusFix maintenance management system redesigned around the visual language of Lyceum of the Philippines University – Manila.

## What was upgraded

- LPU Manila-inspired red / gold / gray / white visual system
- University-style navigation, quick links, footer and admissions/academic sections
- LPU Manila information based on public official university pages
- Real LPU Manila address and a live OpenStreetMap campus locator centered on the campus
- Google Maps handoff for navigation
- LPU academic colleges/program examples
- Campus facilities and official office references
- CampusFix reporting, workflow, notifications and role-based dashboards retained
- ReactBits-inspired interaction layer implemented in framework-free JavaScript so the Flask/Jinja project remains easy to run
- Cursor spotlight, magnetic buttons, 3D tilt cards, scroll reveals, animated counters, marquee, scroll progress and page loading animation
- Optional Three.js hero object loaded from CDN for a lightweight 3D background effect
- Reduced-motion support
- Responsive mobile navigation and layouts

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Demo accounts

- student@campusfix.local / password123
- faculty@campusfix.local / password123
- maintenance@campusfix.local / password123
- supervisor@campusfix.local / password123
- admin@campusfix.local / password123

## Important note

This is a school/project implementation inspired by LPU Manila's publicly visible branding and information. It is **not an official LPU Manila system**, and official transactions should be completed through LPU Manila's official website.

The public university information was checked against LPU Manila's official website, including its university profile, admissions, academics, campus tour and contact information. The map uses OpenStreetMap with the LPU Manila campus centered at approximately 14.5916, 120.97783.

## Image / map attribution

The LPU campus photo used in the demo is a Wikimedia Commons image (`Lyceum of the Philippines.jpg`) licensed CC BY-SA 3.0. The page credits the source in the UI destination context. The map is embedded from OpenStreetMap.

## Reporting-first upgrade

The latest CampusFix version is intentionally centered on the maintenance-reporting workflow rather than a general university information portal.

### Reporting experience
- Four-step guided report wizard: issue type → location/severity → description/evidence → review.
- Photo evidence upload with browser preview and drag-and-drop interaction.
- Additional details field for safety risks, sounds, smells, affected equipment, and other useful context.
- Automatic Report ID and priority calculation.
- Duplicate detection based on active reports in the same building/category.
- Timestamped workflow: Reported → Under Review → Assigned → In Progress → Resolved → Closed.
- User report portal with active/resolved/high-priority summaries.
- Maintenance operations queue and report assignment/status updates.
- Report detail pages show timeline, evidence, additional details, priority, location, and assignment.

### Quality-management features represented in the UI
The interface incorporates the supplied project quality-plan priorities: checking report completeness and accuracy, testing the reporting flow, monitoring status, correcting issues, and using user feedback for improvement. Requirements such as reporting, photos/details, and status tracking are treated as core features.

### Interaction layer
- ReactBits-inspired framework-free effects for the Flask/Jinja app.
- Mouse-reactive 3D tilt cards, magnetic buttons, cursor spotlight, scroll reveals, progress indicators, particle background, and animated report preview.
- Reduced-motion support for accessibility.
- LPU Manila visual direction, campus map, and public university information remain as contextual branding; CampusFix is a student/project prototype and is not an official LPU system.


## Latest visual/AI upgrade
- Uses real LPU Manila campus imagery from public Wikimedia Commons files and the LPU institutional logo reference.
- Removed News and Campus Life from the main navigation to keep CampusFix reporting-focused.
- Added high-contrast night mode styling.
- Added a real AI Campus Assistant backed by the OpenAI Responses API. The AI button is hidden unless `OPENAI_API_KEY` is configured, so the site never pretends a rule-based helper is a real AI.
- Optional environment variables: `OPENAI_API_KEY`, `OPENAI_MODEL` (defaults to `gpt-6-luna`). If no API key is configured, the AI assistant is removed from the UI. Never commit the API key to GitHub. The current OpenAI Responses API is used for the assistant.

## Real AI assistant / Render deployment

CampusFix uses the OpenAI Responses API for its real conversational assistant. The assistant is only shown when `OPENAI_API_KEY` is configured, so there is no fake AI fallback.

### Local
Set the key before starting Flask:
- Windows CMD: `set OPENAI_API_KEY=YOUR_KEY`
- PowerShell: `$env:OPENAI_API_KEY="YOUR_KEY"`
- Optional model: `OPENAI_MODEL=gpt-6-luna`

Then run `python app.py`.

### Render
The included `render.yaml` uses `gunicorn app:app`. In Render, add the secret environment variable `OPENAI_API_KEY` in the service Environment settings. Keep the key out of GitHub and out of HTML/JavaScript.
