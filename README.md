# Job Hunter Agent for Nour 🕵️‍♂️💼

An automated, premium job search and compatibility grading system styled with a modern light-green glassmorphism web dashboard.

## Features

- **Automated Cron Scanning**: Scans Welcome to the Jungle, APEC, and matches from other sources 4 times a day (every 6 hours) on Vercel or locally.
- **Smart CV Grading**: Utilizes Google Gemini AI (or OpenAI) to grade job description fit against your CV from 1 to 10.
- **Tailored CV Recommendations**: Pinpoints matching skills, alerts you of missing skills, and explains how to modify your CV for specific roles.
- **AI Cover Letter Generator**: Prepares tailored cover letters highlighting your skills relative to the job requirements.
- **Gmail Application Dispatch**: Direct integration using secure Gmail SMTP App Passwords to email cover letters and attachments immediately from the web interface.
- **Stat Tracking**: Visual statistics on matched jobs, high matches (grade 8+), and sent applications.

---

## Local Setup & Development

### 1. Requirements
Ensure you have **Python 3.9+** installed on your machine.

### 2. Install Dependencies
Navigate to the project directory and install the requirements:
```bash
pip install -r api/requirements.txt
```

### 3. Start Local Server
Run the FastAPI application locally:
```bash
python -m uvicorn api.index:app --reload
```
Once running, open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

### 4. Database Setup (Automatic)
The backend automatically configures a local SQLite database (`jobs.db`) in the root directory on launch. When deployed to Vercel, it dynamically connects to Postgres if the `POSTGRES_URL` environment variable is defined.

---

## Configuration Settings

You can update settings directly in the **Agent Settings** panel of the dashboard:

1. **CV Text**: Paste your detailed curriculum vitae text.
2. **SMTP Gmail User & App Password**:
   - Go to your Google Account Settings > Security.
   - Turn on **2-Step Verification**.
   - Create an **App Password** (Select 'Mail' and 'Other (Custom Name)' like *Job Hunter*).
   - Paste the generated 16-character code into the setting field.
3. **AI API Key**:
   - Provide your **Google Gemini API Key** (or OpenAI Key) to activate AI-powered grading and letter generation.
   - If left blank, the system automatically falls back to a smart, deterministic keyword-overlap heuristic algorithm so the application remains fully functional.

---

## Deploying to Vercel

The application contains standard Vercel configurations inside [vercel.json](vercel.json).

### Steps:
1. Run `./deploy.sh` to initialize Git and commit local files.
2. Install Vercel CLI: `npm install -g vercel`.
3. Run `vercel` in the project root to link and create a Vercel project.
4. Set up environment variables in your Vercel Dashboard if preferred:
   - `POSTGRES_URL` (optional: for Neon/Vercel Postgres integration).
   - `GEMINI_API_KEY` (optional: to pre-load Gemini access).
5. Build and deploy to production: `vercel --prod`.
6. Enable Vercel Cron jobs by navigating to the **Settings > Git** tab and validating your cron schedules (defined in `vercel.json` as `0 */6 * * *`).

---

## Project Structure

```
├── api/
│   ├── database.py       # DB abstraction layer (SQLite/PostgreSQL)
│   ├── grader.py         # Gemini AI & fallback grading system
│   ├── index.py          # FastAPI application router
│   ├── mailer.py         # Gmail SMTP transport
│   ├── scraper.py        # WTTJ and APEC scraper implementation
│   └── requirements.txt  # Python requirements
├── public/
│   ├── app.js            # Frontend logic and DOM rendering
│   ├── index.html        # Glassmorphic layout
│   └── style.css         # Theme styles & layout sheets
├── deploy.sh             # Deployment assistant script
├── vercel.json           # Vercel configuration & Cron job registry
└── README.md             # This instruction manual
```
