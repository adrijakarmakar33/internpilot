# agent/matcher.py

def calculate_match(resume_data, job_data):

    resume_skills = set(resume_data.get("skills", []))
    job_skills = set(job_data.get("skills", []))

    matched = list(resume_skills.intersection(job_skills))
    missing = list(job_skills - resume_skills)

    if len(job_skills) == 0:
        score = 0
    else:
        score = int((len(matched) / len(job_skills)) * 100)

    return {
        "score": score,
        "matched": matched,
        "missing": missing
    }