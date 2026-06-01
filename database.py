import os
import sqlite3
import json
from datetime import datetime

# Path for local SQLite DB
SQLITE_DB_PATH = "/tmp/jobs.db"

def get_connection():
    """
    Returns a database connection.
    Connects to PostgreSQL if POSTGRES_URL or DATABASE_URL environment variables are defined.
    Otherwise, falls back to local SQLite database.
    """
    postgres_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    
    if postgres_url:
        import psycopg2
        # Clean Vercel postgres URL if needed (some libraries expect postgres:// instead of postgresql://)
        if postgres_url.startswith("postgres://"):
            postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(postgres_url)
        return conn, True
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn, False

def init_db():
    """
    Initializes the database schema if it doesn't already exist.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgres:
            # Create settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    job_key VARCHAR(100) UNIQUE,
                    title VARCHAR(255),
                    company VARCHAR(255),
                    location VARCHAR(255),
                    url TEXT,
                    description TEXT,
                    site VARCHAR(100),
                    grade INTEGER,
                    explanation TEXT,
                    skills_matched TEXT,
                    skills_missing TEXT,
                    cv_suggestions TEXT,
                    cover_letter TEXT,
                    status VARCHAR(50) DEFAULT 'Matched',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            # SQLite syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_key TEXT UNIQUE,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    description TEXT,
                    site TEXT,
                    grade INTEGER,
                    explanation TEXT,
                    skills_matched TEXT,
                    skills_missing TEXT,
                    cv_suggestions TEXT,
                    cover_letter TEXT,
                    status TEXT DEFAULT 'Matched',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def save_settings(settings_dict):
    """
    Saves or updates settings keys and values.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.now()
        for key, value in settings_dict.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value) if value is not None else ""
                
            if is_postgres:
                cursor.execute("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at;
                """, (key, value_str, now))
            else:
                cursor.execute("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at;
                """, (key, value_str, now))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_settings():
    """
    Retrieves all settings as a flat dictionary.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT key, value FROM settings;")
        rows = cursor.fetchall()
        settings = {}
        for row in rows:
            key, value = row[0], row[1]
            # Try to load JSON for lists/dicts
            try:
                if value.startswith("{") or value.startswith("["):
                    settings[key] = json.loads(value)
                else:
                    settings[key] = value
            except Exception:
                settings[key] = value
        
        # Set defaults if keys don't exist
        defaults = {
            "cv_text": "",
            "gmail_user": "",
            "gmail_password": "",
            "ai_api_key": "",
            "ai_provider": "gemini", # gemini or openai
            "search_keywords": "Developer, Product Manager, Data Engineer",
            "search_locations": "Paris, Remote",
            "sites": ["Welcome to the Jungle", "APEC", "Indeed", "LinkedIn", "Glassdoor"]
        }
        for k, v in defaults.items():
            if k not in settings:
                settings[k] = v
                
        return settings
    finally:
        cursor.close()
        conn.close()

def save_job(job_dict):
    """
    Inserts a new job or updates an existing one if the job_key matches.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    # Format list fields to json strings if they are lists
    skills_matched = json.dumps(job_dict.get("skills_matched", [])) if isinstance(job_dict.get("skills_matched"), list) else job_dict.get("skills_matched", "[]")
    skills_missing = json.dumps(job_dict.get("skills_missing", [])) if isinstance(job_dict.get("skills_missing"), list) else job_dict.get("skills_missing", "[]")
    
    try:
        if is_postgres:
            cursor.execute("""
                INSERT INTO jobs (
                    job_key, title, company, location, url, description, site, 
                    grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_key) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    url = EXCLUDED.url,
                    description = EXCLUDED.description,
                    site = EXCLUDED.site,
                    grade = EXCLUDED.grade,
                    explanation = EXCLUDED.explanation,
                    skills_matched = EXCLUDED.skills_matched,
                    skills_missing = EXCLUDED.skills_missing,
                    cv_suggestions = EXCLUDED.cv_suggestions,
                    cover_letter = EXCLUDED.cover_letter;
            """, (
                job_dict["job_key"], job_dict["title"], job_dict["company"], job_dict["location"], job_dict["url"], 
                job_dict["description"], job_dict["site"], job_dict["grade"], job_dict["explanation"], 
                skills_matched, skills_missing, job_dict.get("cv_suggestions", ""), job_dict.get("cover_letter", ""),
                job_dict.get("status", "Matched")
            ))
        else:
            cursor.execute("""
                INSERT INTO jobs (
                    job_key, title, company, location, url, description, site, 
                    grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_key) DO UPDATE SET
                    title = excluded.title,
                    company = excluded.company,
                    location = excluded.location,
                    url = excluded.url,
                    description = excluded.description,
                    site = excluded.site,
                    grade = excluded.grade,
                    explanation = excluded.explanation,
                    skills_matched = excluded.skills_matched,
                    skills_missing = excluded.skills_missing,
                    cv_suggestions = excluded.cv_suggestions,
                    cover_letter = excluded.cover_letter;
            """, (
                job_dict["job_key"], job_dict["title"], job_dict["company"], job_dict["location"], job_dict["url"], 
                job_dict["description"], job_dict["site"], job_dict["grade"], job_dict["explanation"], 
                skills_matched, skills_missing, job_dict.get("cv_suggestions", ""), job_dict.get("cover_letter", ""),
                job_dict.get("status", "Matched")
            ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_jobs(status_filter=None):
    """
    Fetches all jobs from the DB, optionally filtering by status, sorted by grade descending.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        if status_filter:
            if is_postgres:
                cursor.execute("""
                    SELECT id, job_key, title, company, location, url, description, site, 
                           grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status, created_at
                    FROM jobs WHERE status = %s ORDER BY grade DESC, created_at DESC;
                """, (status_filter,))
            else:
                cursor.execute("""
                    SELECT id, job_key, title, company, location, url, description, site, 
                           grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status, created_at
                    FROM jobs WHERE status = ? ORDER BY grade DESC, created_at DESC;
                """, (status_filter,))
        else:
            cursor.execute("""
                SELECT id, job_key, title, company, location, url, description, site, 
                       grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status, created_at
                FROM jobs ORDER BY grade DESC, created_at DESC;
            """)
            
        rows = cursor.fetchall()
        jobs = []
        for row in rows:
            # Map elements
            job = {
                "id": row[0],
                "job_key": row[1],
                "title": row[2],
                "company": row[3],
                "location": row[4],
                "url": row[5],
                "description": row[6],
                "site": row[7],
                "grade": row[8],
                "explanation": row[9],
                "status": row[14],
                "created_at": str(row[15])
            }
            
            # Safe JSON parsing for skills list
            try:
                job["skills_matched"] = json.loads(row[10])
            except Exception:
                job["skills_matched"] = [row[10]] if row[10] else []
                
            try:
                job["skills_missing"] = json.loads(row[11])
            except Exception:
                job["skills_missing"] = [row[11]] if row[11] else []
                
            job["cv_suggestions"] = row[12]
            job["cover_letter"] = row[13]
            
            jobs.append(job)
            
        return jobs
    finally:
        cursor.close()
        conn.close()

def get_job(job_id):
    """
    Gets details of a single job by its ID.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgres:
            cursor.execute("""
                SELECT id, job_key, title, company, location, url, description, site, 
                       grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status, created_at
                FROM jobs WHERE id = %s;
            """, (job_id,))
        else:
            cursor.execute("""
                SELECT id, job_key, title, company, location, url, description, site, 
                       grade, explanation, skills_matched, skills_missing, cv_suggestions, cover_letter, status, created_at
                FROM jobs WHERE id = ?;
            """, (job_id,))
            
        row = cursor.fetchone()
        if not row:
            return None
            
        job = {
            "id": row[0],
            "job_key": row[1],
            "title": row[2],
            "company": row[3],
            "location": row[4],
            "url": row[5],
            "description": row[6],
            "site": row[7],
            "grade": row[8],
            "explanation": row[9],
            "status": row[14],
            "created_at": str(row[15])
        }
        
        try:
            job["skills_matched"] = json.loads(row[10])
        except Exception:
            job["skills_matched"] = [row[10]] if row[10] else []
            
        try:
            job["skills_missing"] = json.loads(row[11])
        except Exception:
            job["skills_missing"] = [row[11]] if row[11] else []
            
        job["cv_suggestions"] = row[12]
        job["cover_letter"] = row[13]
        
        return job
    finally:
        cursor.close()
        conn.close()

def update_job_status(job_id, status):
    """
    Updates the status of a job.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgres:
            cursor.execute("UPDATE jobs SET status = %s WHERE id = %s;", (status, job_id))
        else:
            cursor.execute("UPDATE jobs SET status = ? WHERE id = ?;", (status, job_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_job_cover_letter(job_id, cover_letter):
    """
    Updates the cover letter text for a specific job.
    """
    conn, is_postgres = get_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgres:
            cursor.execute("UPDATE jobs SET cover_letter = %s WHERE id = %s;", (cover_letter, job_id))
        else:
            cursor.execute("UPDATE jobs SET cover_letter = ? WHERE id = ?;", (cover_letter, job_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
