import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import json

# Import backend modules
from api import database
from api import scraper
from api import grader
from api import mailer

app = FastAPI(title="Job Hunter Agent API")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    database.init_db()

# Models
class SettingsModel(BaseModel):
    cv_text: str
    gmail_user: str
    gmail_password: str
    ai_api_key: str
    ai_provider: str
    search_keywords: str
    search_locations: str
    sites: List[str]

class ApplyModel(BaseModel):
    recipient_email: str
    subject: str
    cover_letter: str

class StatusModel(BaseModel):
    status: str

class CoverLetterModel(BaseModel):
    cover_letter: str

# API Endpoints
@app.get("/api/jobs")
def get_jobs(status: Optional[str] = None):
    try:
        jobs = database.get_jobs(status_filter=status)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/jobs/{job_id}")
def get_job(job_id: int):
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/{job_id}/apply")
def apply_job(job_id: int, payload: ApplyModel):
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    settings = database.get_settings()
    gmail_user = settings.get("gmail_user")
    gmail_password = settings.get("gmail_password")
    
    if not gmail_user or not gmail_password:
        raise HTTPException(status_code=400, detail="Gmail credentials are not configured in settings.")
        
    # Get CV text as fallback attachment if needed, or we can send it without attachment if not provided.
    # In a full app we could save the CV pdf bytes, but here we can write the CV text to a temp file
    # or attach it as a clean text file CV.txt.
    cv_text = settings.get("cv_text", "")
    cv_bytes = cv_text.encode('utf-8') if cv_text else None
    cv_filename = "Nour_CV.txt" if cv_text else None
    
    success, msg = mailer.send_application_email(
        gmail_user=gmail_user,
        gmail_password=gmail_password,
        to_email=payload.recipient_email,
        subject=payload.subject,
        body=payload.cover_letter,
        cv_content=cv_bytes,
        cv_filename=cv_filename
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=msg)
        
    # Mark job as Applied
    database.update_job_status(job_id, "Applied")
    return {"message": "Application email sent successfully!"}

@app.post("/api/jobs/{job_id}/status")
def update_job_status(job_id: int, payload: StatusModel):
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    database.update_job_status(job_id, payload.status)
    return {"message": f"Job status updated to {payload.status}"}

@app.post("/api/jobs/{job_id}/cover-letter")
def update_job_cover_letter(job_id: int, payload: CoverLetterModel):
    job = database.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    database.update_job_cover_letter(job_id, payload.cover_letter)
    return {"message": "Cover letter updated successfully"}

@app.get("/api/settings")
def get_settings():
    settings = database.get_settings()
    # Mask password for safety
    if settings.get("gmail_password"):
        settings["gmail_password_masked"] = "••••••••••••••••"
    else:
        settings["gmail_password_masked"] = ""
    # Mask AI key
    if settings.get("ai_api_key"):
        settings["ai_api_key_masked"] = "••••••••••••" + settings["ai_api_key"][-4:] if len(settings["ai_api_key"]) > 4 else "••••••••••••"
    else:
        settings["ai_api_key_masked"] = ""
    return settings

@app.post("/api/settings")
def save_settings(payload: SettingsModel):
    settings = database.get_settings()
    
    # Don't overwrite password/keys if they were sent masked or empty
    updated_data = payload.dict()
    if updated_data["gmail_password"] == "••••••••••••••••" or not updated_data["gmail_password"]:
        updated_data["gmail_password"] = settings.get("gmail_password", "")
    if updated_data["ai_api_key"].startswith("••••••••••••") or not updated_data["ai_api_key"]:
        updated_data["ai_api_key"] = settings.get("ai_api_key", "")
        
    database.save_settings(updated_data)
    return {"message": "Settings updated successfully"}

def run_job_search_and_grade():
    """
    Background worker that runs the full scraping, grading, and DB saving workflow.
    """
    print("Background task started: Job Search & Grading")
    try:
        settings = database.get_settings()
        cv_text = settings.get("cv_text", "")
        api_key = settings.get("ai_api_key", "")
        provider = settings.get("ai_provider", "gemini")
        keywords = settings.get("search_keywords", "Developer")
        locations = settings.get("search_locations", "Paris")
        sites = settings.get("sites", ["Welcome to the Jungle", "APEC"])
        
        # 1. Scrape matching jobs
        jobs = scraper.search_all_sites(keywords, locations, sites)
        print(f"Scraped {len(jobs)} total jobs.")
        
        # 2. Grade and save each job
        new_jobs_count = 0
        for job in jobs:
            # Check if job already exists in DB to avoid double grading
            conn, is_postgres = database.get_connection()
            cursor = conn.cursor()
            try:
                if is_postgres:
                    cursor.execute("SELECT id FROM jobs WHERE job_key = %s", (job["job_key"],))
                else:
                    cursor.execute("SELECT id FROM jobs WHERE job_key = ?", (job["job_key"],))
                row = cursor.fetchone()
                if row:
                    # Job exists, skip AI grading to save quota and time
                    continue
            finally:
                cursor.close()
                conn.close()
                
            # Grade new job using LLM/Heuristic
            print(f"Grading job: {job['title']} at {job['company']}")
            grade_result = grader.grade_job_with_llm(
                cv_text=cv_text,
                job_title=job["title"],
                company=job["company"],
                description=job["description"],
                api_key=api_key,
                provider=provider
            )
            
            # Combine details
            job_details = {**job, **grade_result}
            
            # Save to Database
            database.save_job(job_details)
            new_jobs_count += 1
            
        print(f"Job search finished. Added and graded {new_jobs_count} new jobs.")
        return new_jobs_count
    except Exception as e:
        print(f"Error in background scan: {e}")
        return 0

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    """
    Triggers manual scraping and AI analysis in the background.
    """
    background_tasks.add_task(run_job_search_and_grade)
    return {"message": "Job scraper and grading engine started in the background. Results will appear shortly."}

@app.get("/api/cron")
def vercel_cron_endpoint():
    """
    Synchronous endpoint intended for Vercel Cron jobs.
    Runs the job search and grading process.
    """
    new_jobs = run_job_search_and_grade()
    return {
        "status": "success",
        "message": f"Vercel Cron executed successfully. Added {new_jobs} new jobs."
    }

# Mount static files for the SPA frontend
# Ensure that the public folder exists
public_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
if os.path.exists(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="public")
else:
    @app.get("/")
    def read_index():
        return {"message": "Frontend assets not found. Place your index.html in the public folder."}
