class LLMClient:
    """
    Mock LLM client.
    Prepared for Nova integration later.
    """

    TECH_SKILLS = ["Python", "Java", "React", "SQL", "FastAPI", "AWS", "Docker"]
    SOFT_SKILLS = ["Leadership", "Communication", "Teamwork"]
    DOMAIN_SKILLS = ["Digital Marketing", "SEO"]

    async def extract_resume_data(self, resume_text: str):

        skills = []

        for skill in self.TECH_SKILLS + self.SOFT_SKILLS + self.DOMAIN_SKILLS:
            if skill.lower() in resume_text.lower():
                skills.append(skill)

        categorized = self.categorize_skills(skills)

        return {
            "skills": skills,
            "categorized_skills": categorized,
            "summary": "AI-generated professional summary."
        }

    async def extract_job_data(self, job_text: str):

        skills = []

        for skill in self.TECH_SKILLS + self.SOFT_SKILLS + self.DOMAIN_SKILLS:
            if skill.lower() in job_text.lower():
                skills.append(skill)

        categorized = self.categorize_skills(skills)

        return {
            "required_skills": skills,
            "categorized_required_skills": categorized,
            "experience_level": "Entry Level"
        }

    def categorize_skills(self, skills):
        return {
            "technical": [s for s in skills if s in self.TECH_SKILLS],
            "soft": [s for s in skills if s in self.SOFT_SKILLS],
            "domain": [s for s in skills if s in self.DOMAIN_SKILLS]
        }

    async def generate_match_explanation(self, score):

        if score >= 85:
            explanation = "Strong overall alignment across technical, soft, and domain skills."
        elif score >= 60:
            explanation = "Moderate alignment with some important skill gaps."
        elif score > 0:
            explanation = "Limited alignment. Significant skill gaps detected."
        else:
            explanation = "No meaningful alignment with job requirements."

        confidence = round(score / 100, 2)

        return {
            "match_explanation": explanation,
            "confidence": confidence
        }