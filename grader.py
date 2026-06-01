import os
import json
import re

def grade_job_with_llm(cv_text, job_title, company, description, api_key, provider="gemini"):
    """
    Grades a job offer against the user's CV using Gemini or OpenAI.
    Returns a dictionary with grade, explanation, skills_matched, skills_missing, cv_suggestions, and cover_letter.
    """
    if not api_key:
        return get_heuristic_grade(cv_text, job_title, company, description)

    prompt = f"""
    You are an expert technical recruiter and career coach. Your task is to analyze the following job description and compare it with the candidate's CV.
    
    Candidate CV:
    \"\"\"{cv_text}\"\"\"
    
    Job Offer Details:
    - Title: {job_title}
    - Company: {company}
    - Description: \"\"\"{description}\"\"\"
    
    Perform the following tasks:
    1. Grade the compatibility of the CV with this job description on a scale from 1 to 10 (1 = completely incompatible, 10 = perfect match).
    2. Extract a list of skills from the job description that the candidate possesses (skills_matched).
    3. Extract a list of key skills or requirements from the job description that are missing or weak in the candidate's CV (skills_missing).
    4. Provide a detailed, concise explanation of the compatibility score (why this score, strengths, and weaknesses).
    5. Give actionable suggestions on how the candidate can adapt their CV specifically for this job (e.g. highlight specific projects, reword experience, emphasize certain tools).
    6. Write a professional, tailored cover letter (about 250-350 words) from the candidate to the hiring manager at {company} for the position of {job_title}. Use standard placeholders like [Date], [Candidate Name], [Candidate Contact Info] where appropriate. The cover letter must highlight the matching skills and explain how they can help {company}. Keep the tone professional, engaging, and personalized.

    Your output MUST be a valid JSON object ONLY. Do not write markdown blocks (no ```json or ```). It must match this exact format:
    {{
        "grade": 8,
        "explanation": "Explain why in a few sentences...",
        "skills_matched": ["Python", "SQL", "Git"],
        "skills_missing": ["Docker", "Kubernetes"],
        "cv_suggestions": "Actionable suggestions to improve the CV...",
        "cover_letter": "Dear Hiring Manager,\\n\\n..."
    }}
    """

    try:
        if provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Request JSON output specifically
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            result = json.loads(response.text.strip())
            return sanitize_llm_result(result)
            
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a recruitment assistant who outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return sanitize_llm_result(result)
            
    except Exception as e:
        print(f"Error grading with AI ({provider}): {e}. Falling back to heuristic grading.")
        return get_heuristic_grade(cv_text, job_title, company, description)

def sanitize_llm_result(result):
    """
    Ensures the LLM result has all required keys in the correct format.
    """
    required_keys = ["grade", "explanation", "skills_matched", "skills_missing", "cv_suggestions", "cover_letter"]
    
    # Ensure all keys exist
    for key in required_keys:
        if key not in result:
            if key == "grade":
                result[key] = 5
            elif key in ["skills_matched", "skills_missing"]:
                result[key] = []
            else:
                result[key] = ""
                
    # Force grade to be integer 1-10
    try:
        grade = int(result["grade"])
        result["grade"] = max(1, min(10, grade))
    except Exception:
        result["grade"] = 5
        
    # Force lists
    if not isinstance(result["skills_matched"], list):
        result["skills_matched"] = [str(result["skills_matched"])] if result["skills_matched"] else []
    if not isinstance(result["skills_missing"], list):
        result["skills_missing"] = [str(result["skills_missing"])] if result["skills_missing"] else []
        
    return result

def get_heuristic_grade(cv_text, job_title, company, description):
    """
    Determistic backup grading function based on keyword overlaps.
    Runs when no API keys are loaded or LLM calls fail.
    """
    # Normalize strings
    cv_lower = cv_text.lower() if cv_text else ""
    desc_lower = description.lower()
    
    # A list of technical skills to scan for
    tech_keywords = [
        "python", "javascript", "typescript", "react", "vue", "angular", "node", "express",
        "fastapi", "django", "flask", "ruby", "rails", "php", "java", "spring", "c#", "dotnet",
        "c++", "golang", "rust", "sql", "postgresql", "mysql", "mongodb", "redis", "docker",
        "kubernetes", "aws", "gcp", "azure", "terraform", "git", "ci/cd", "agile", "scrum",
        "machine learning", "data science", "spark", "airflow", "analytics", "product management"
    ]
    
    matched_skills = []
    missing_skills = []
    
    # Scan job description for tech skills, and check if they are in CV
    for skill in tech_keywords:
        # Match word boundaries or simple occurrences
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, desc_lower):
            if cv_text and re.search(pattern, cv_lower):
                matched_skills.append(skill.capitalize())
            else:
                missing_skills.append(skill.capitalize())
                
    # Calculate grade
    total_found = len(matched_skills) + len(missing_skills)
    if total_found == 0:
        grade = 5 # Default midpoint
    else:
        # Base grade is ratio of matches, scaled from 1 to 10
        ratio = len(matched_skills) / total_found
        grade = int(1 + ratio * 8) # maps [0, 1] to [1, 9]
        
        # Adjust grade based on job title keyword matches
        title_keywords = job_title.lower().split()
        title_matches = sum(1 for kw in title_keywords if cv_text and kw in cv_lower and len(kw) > 3)
        if title_matches > 0:
            grade = min(10, grade + 1)
            
    # Format a fallback explanation
    if not cv_text:
        explanation = "We graded this job a 5/10. Please upload or paste your CV in the Settings panel to get a precise, customized compatibility score!"
        cv_suggestions = "Paste your CV in the Settings panel to receive custom tailor-fit recommendations."
        cover_letter = f"Dear Hiring Manager,\n\nI am writing to express my interest in the {job_title} position at {company}. (Paste your CV in the Settings panel to auto-generate a full tailored cover letter here!)."
    else:
        explanation = f"Based on a keyword scan, your CV matches {len(matched_skills)} skills required for this job (including {', '.join(matched_skills[:4]) if matched_skills else 'none'}). However, you are missing {len(missing_skills)} key skills ({', '.join(missing_skills[:4]) if missing_skills else 'none'}) which led to a compatibility score of {grade}/10."
        
        cv_suggestions = f"To optimize your CV for this role:\n"
        if missing_skills:
            cv_suggestions += f"1. Try to highlight any academic or personal projects that involve {', '.join(missing_skills[:3])}.\n"
        cv_suggestions += f"2. Ensure your experience list specifically emphasizes your achievements with {', '.join(matched_skills[:3]) if matched_skills else 'relevant technical tools'}."
        
        # Standard professional cover letter template
        skills_paragraph = ""
        if matched_skills:
            skills_paragraph = f"Throughout my career, I have developed strong competencies in {', '.join(matched_skills[:-1])} and {matched_skills[-1]}. "
        else:
            skills_paragraph = "I have a diverse technical background and adapt quickly to new technologies and frameworks. "
            
        cover_letter = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my enthusiastic interest in the position of {job_title} at {company}, "
            f"which I discovered through my automated job search portal.\n\n"
            f"With my background in software engineering, I am confident that I can make a significant contribution "
            f"to your team. {skills_paragraph}I am particularly drawn to this role at {company} because of your focus "
            f"on innovation and excellence in engineering.\n\n"
            f"Thank you for your time and consideration. I look forward to the possibility of discussing how my skills "
            f"and experience align with your team's current needs.\n\n"
            f"Sincerely,\n"
            f"[Your Name]\n"
            f"[Contact Details]"
        )
        
    return {
        "grade": grade,
        "explanation": explanation,
        "skills_matched": matched_skills,
        "skills_missing": missing_skills,
        "cv_suggestions": cv_suggestions,
        "cover_letter": cover_letter
    }
