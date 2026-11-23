CREATE DATABASE IF NOT EXISTS campusfix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campusfix;

CREATE TABLE users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 full_name VARCHAR(150) NOT NULL,
 email VARCHAR(180) UNIQUE NOT NULL,
 password_hash VARCHAR(255) NOT NULL,
 role VARCHAR(40) NOT NULL,
 department VARCHAR(150),
 user_id_code VARCHAR(80),
 contact_number VARCHAR(40),
 profile_photo VARCHAR(255),
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reports (
 id INT AUTO_INCREMENT PRIMARY KEY,
 report_code VARCHAR(30) UNIQUE NOT NULL,
 category VARCHAR(80) NOT NULL,
 building VARCHAR(120) NOT NULL,
 room_area VARCHAR(120),
 severity VARCHAR(30) NOT NULL,
 description TEXT NOT NULL,
 date_noticed DATE,
 reporter_id INT,
 assigned_to INT,
 status VARCHAR(40) DEFAULT 'Reported',
 priority VARCHAR(30) DEFAULT 'Medium',
 duplicate_count INT DEFAULT 0,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (reporter_id) REFERENCES users(id),
 FOREIGN KEY (assigned_to) REFERENCES users(id)
);

CREATE TABLE report_updates (
 id INT AUTO_INCREMENT PRIMARY KEY,
 report_id INT NOT NULL,
 user_id INT,
 old_status VARCHAR(40),
 new_status VARCHAR(40),
 note TEXT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (report_id) REFERENCES reports(id),
 FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE notifications (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 title VARCHAR(180) NOT NULL,
 message TEXT NOT NULL,
 is_read BOOLEAN DEFAULT FALSE,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE announcements (
 id INT AUTO_INCREMENT PRIMARY KEY,
 title VARCHAR(180) NOT NULL,
 summary TEXT,
 category VARCHAR(60),
 published_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
