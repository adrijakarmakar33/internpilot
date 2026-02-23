from services.ai_service import (
    analyze_resume,
    analyze_job,
    calculate_match,
    detect_skill_gap,
    generate_improvement_suggestions
)


class InternshipAgent:

    def run_analysis(self, resume_text: str, job_text: str):

        # Step 1: Analyze Resume
        resume_data = analyze_resume(resume_text)

        # Step 2: Analyze Job
        job_data = analyze_job(job_text)

        # Step 3: Calculate Match
        match_score = calculate_match(
            resume_data["skills"],
            job_data["required_skills"]
        )

        # Step 4: Detect Missing Skills
        missing_skills = detect_skill_gap(
            resume_data["skills"],
            job_data["required_skills"]
        )

        # Step 5: Generate Suggestions
        suggestions = generate_improvement_suggestions(missing_skills)

        return {
            "resume_analysis": resume_data,
            "job_analysis": job_data,
            "match_score": match_score,
            "missing_skills": missing_skills,
            "improvement_suggestions": suggestions
        }