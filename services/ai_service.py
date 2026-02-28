import re

COMMON_SKILLS = [
    "Python","Java","React","SQL","FastAPI","AWS",
    "Docker","Digital Marketing","SEO",
    "Leadership","Communication","Teamwork",
    "Corporate Law","Legal Research","Contract Drafting","Compliance",
    "Litigation","Negotiation","Due Diligence","Arbitration",
    "Accounting","Financial Analysis","Auditing","Taxation",
    "Sales","Customer Service","Human Resources","Recruitment",
    "Supply Chain","Operations","Project Management","Risk Management"
]

async def analyze_resume(text:str):
    known = [s for s in COMMON_SKILLS if s.lower() in text.lower()]
    inferred = _extract_general_keywords(text, limit=18)
    merged = []
    seen = set()
    for item in known + inferred:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return {"skills": merged[:20]}

async def analyze_job(text:str):
    skills = _extract_role_keywords(text, limit=14)
    if not skills:
        skills = _extract_general_keywords(text, limit=10)
    role_title = _extract_role_title(text)
    role_family = _detect_role_family(text, role_title)
    return {"required_skills": skills, "role_title": role_title, "role_family": role_family}

def calculate_match(resume_data,job_data):
    job_skills = list(dict.fromkeys(job_data["required_skills"]))
    if not job_skills:
        return 0
    matched = get_matched_skills(resume_data, job_data)
    return int(len(matched) / len(job_skills) * 100)

def detect_skill_gap(resume_data,job_data):
    matched = set(get_matched_skills(resume_data, job_data))
    job_skills = list(dict.fromkeys(job_data["required_skills"]))
    return [skill for skill in job_skills if skill not in matched]


def _normalize_skill(skill: str):
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", (skill or "").lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _is_skill_match(resume_skill: str, job_skill: str):
    r = _normalize_skill(resume_skill)
    j = _normalize_skill(job_skill)
    if not r or not j:
        return False
    if r == j:
        return True
    if r in j or j in r:
        return True
    # token-overlap fallback for variants like "Corporate Law" vs "Law"
    r_tokens = set(r.split())
    j_tokens = set(j.split())
    return len(r_tokens.intersection(j_tokens)) > 0


def get_matched_skills(resume_data, job_data):
    resume_skills = resume_data.get("skills", [])
    job_skills = list(dict.fromkeys(job_data.get("required_skills", [])))
    matched = []
    for js in job_skills:
        if any(_is_skill_match(rs, js) for rs in resume_skills):
            matched.append(js)
    return matched

def generate_improvement_suggestions(missing, role_title: str = ""):
    if not missing:
        return ["Your resume matches the job requirements well."]
    intro = f"To improve fit for {role_title}, focus on:" if role_title else "To improve fit, focus on:"
    items = [f"Strengthen {m} with one project or proof point." for m in missing[:5]]
    return [intro] + items

def generate_career_roadmap(missing, role_title: str = ""):
    if not missing:
        return ["Build advanced projects and prepare for interviews."]
    roadmap=[]
    for m in missing:
        roadmap.append(f"Learn {m} fundamentals relevant to {role_title or 'target role'}.")
        roadmap.append(f"Build one portfolio artifact demonstrating {m}.")
    return roadmap

def generate_interview_questions(skills, role_title: str = "", role_family: str = "general"):
    role_prefix = role_title or "this role"
    questions = []
    for s in skills[:4]:
        if role_family in {"legal", "finance", "hr", "marketing", "operations"}:
            questions.append(f"For {role_prefix}, explain how you applied {s} in a real work scenario.")
        else:
            questions.append(f"For {role_prefix}, explain your practical experience with {s}.")

    if role_family == "legal":
        questions.append("Describe a contract review where you identified risk and how you mitigated it.")
        questions.append("How do you stay updated with regulatory changes relevant to this role?")
    elif role_family == "finance":
        questions.append("Walk through a financial analysis you performed and the business decision it informed.")
        questions.append("How do you validate data accuracy before presenting financial insights?")
    elif role_family == "marketing":
        questions.append("Describe a campaign you optimized and which metrics improved.")
        questions.append("How do you approach audience segmentation and messaging testing?")
    elif role_family == "hr":
        questions.append("Explain how you handled a difficult hiring or employee-relations scenario.")
        questions.append("What metrics do you use to evaluate recruitment effectiveness?")
    elif role_family == "software":
        questions.append("Describe a production issue you debugged and the root-cause fix.")
        questions.append("How do you balance code quality, delivery speed, and scalability?")
    elif role_family == "data":
        questions.append("Explain an analysis where your insights changed a business decision.")
        questions.append("How do you choose the right metric and validate it is trustworthy?")

    if not questions:
        questions=["Tell me about yourself."]
    return questions[:6]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has",
    "your", "you", "our", "are", "was", "were", "into", "about", "their",
    "them", "then", "than", "been", "also", "but", "can", "will", "would",
    "could", "should", "using", "used", "use", "explain", "experience"
}

RESUME_KEYWORD_STOPWORDS = STOPWORDS.union(
    {
        "job", "role", "responsibilities", "requirements", "candidate", "apply", "application",
        "ability", "preferred", "plus", "minimum", "years", "year", "work", "working",
        "strong", "excellent", "knowledge", "understanding", "proficiency", "familiarity",
        "responsible", "including", "across", "within", "build", "building", "develop",
        "developing", "internship", "intern", "entry", "level", "looking", "seeking", "hiring",
        "candidate", "profile", "position", "must", "should", "need", "required",
    }
)

SKILL_HINTS = {
    "leadership": {"lead", "led", "manage", "managed", "mentor", "mentored", "ownership", "initiative"},
    "communication": {"communicate", "communication", "present", "presentation", "collaborate", "stakeholder"},
    "teamwork": {"team", "collaborate", "pair", "cross-functional", "support"},
    "sql": {"query", "queries", "join", "joins", "index", "indexes", "schema", "database"},
    "python": {"python", "pandas", "fastapi", "flask", "script", "automation"},
    "digital marketing": {"campaign", "ctr", "cpc", "conversion", "audience", "funnel"},
    "seo": {"keyword", "backlink", "ranking", "serp", "on-page", "organic"},
}


def _tokenize(text: str):
    tokens = re.findall(r"[a-zA-Z0-9\+\#\.]+", text.lower())
    cleaned = []
    for token in tokens:
        normalized = token.strip(".,:;!?()[]{}\"'`")
        normalized = normalized.strip("+-/#")
        if normalized:
            cleaned.append(normalized)
    return [t for t in cleaned if len(t) > 2 and t not in STOPWORDS]


def _extract_general_keywords(text: str, limit: int = 12):
    tokens = _tokenize(text)
    freq = {}
    for token in tokens:
        if token in RESUME_KEYWORD_STOPWORDS:
            continue
        if token.isdigit():
            continue
        if len(token) < 3:
            continue
        freq[token] = freq.get(token, 0) + 1

    ranked_tokens = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    aliases = {
        "apis": "API",
        "api": "API",
        "aws": "AWS",
        "seo": "SEO",
        "sql": "SQL",
        "etl": "ETL",
        "ui": "UI",
        "ux": "UX",
        "hr": "HR",
    }
    output = []
    for token, _ in ranked_tokens:
        cleaned = aliases.get(token, token.capitalize())
        output.append(cleaned)
        if len(output) >= limit:
            break
    return output


def _split_question_and_answer(raw: str):
    q_marker = "question:"
    a_marker = "answer:"
    lowered = raw.lower()

    if q_marker in lowered and a_marker in lowered:
        q_start = lowered.index(q_marker) + len(q_marker)
        a_start = lowered.index(a_marker)
        question = raw[q_start:a_start].strip()
        answer = raw[a_start + len(a_marker):].strip()
        return question, answer

    return "", raw.strip()


def _contains_any(text_lower: str, words):
    return any(w in text_lower for w in words)


def _first_nonempty_line(text: str):
    for line in text.splitlines():
        cleaned = line.strip(" -*:\t")
        if cleaned:
            return cleaned
    return ""


def _extract_role_title(job_text: str):
    lowered = job_text.lower()
    pattern_hiring = re.search(
        r"(?:hiring|looking\s+for|seeking|need(?:ed)?)\s+(?:an?\s+)?([a-z][a-z\s\-&/]{2,60}?)(?:\s+(?:with|for|to|who)\b|[.,;\n]|$)",
        lowered,
        flags=re.IGNORECASE,
    )
    if pattern_hiring:
        phrase = pattern_hiring.group(1).strip(" -")
        if phrase:
            return " ".join(word.capitalize() for word in phrase.split())

    explicit = re.search(
        r"(?:job\s*title|title|position|role)\s*[:\-]\s*([^\n\r,|]+)",
        job_text,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1).strip()

    title_hints = [
        "software engineer", "backend engineer", "frontend engineer", "full stack developer",
        "data analyst", "data scientist", "machine learning engineer", "product manager",
        "business analyst", "digital marketing specialist", "seo specialist", "qa engineer",
        "devops engineer", "cloud engineer", "ui ux designer", "cybersecurity analyst",
        "corporate lawyer", "lawyer", "legal associate", "legal counsel",
        "chartered accountant", "accountant", "financial analyst",
        "hr executive", "human resources executive", "operations manager",
    ]
    for hint in title_hints:
        if hint in lowered:
            return " ".join(w.capitalize() for w in hint.split())

    first_line = _first_nonempty_line(job_text)
    if first_line:
        return first_line.strip(" -|:")
    return "Target Role Candidate"


def _detect_role_family(job_text: str, role_title: str = ""):
    lowered = f"{job_text} {role_title}".lower()
    if any(k in lowered for k in ["law", "lawyer", "legal", "litigation", "compliance", "contract"]):
        return "legal"
    if any(k in lowered for k in ["finance", "account", "audit", "tax", "analyst", "fp&a"]):
        return "finance"
    if any(k in lowered for k in ["marketing", "seo", "campaign", "brand", "growth"]):
        return "marketing"
    if any(k in lowered for k in ["recruit", "human resources", "hr", "talent", "people ops"]):
        return "hr"
    if any(k in lowered for k in ["data scientist", "data analyst", "bi", "analytics", "machine learning"]):
        return "data"
    if any(k in lowered for k in ["engineer", "developer", "software", "backend", "frontend", "devops", "cloud"]):
        return "software"
    if any(k in lowered for k in ["operations", "supply chain", "procurement", "logistics"]):
        return "operations"
    return "general"


def _extract_role_keywords(job_text: str, limit: int = 14):
    # Prefer explicit known skills, then enrich with frequent JD nouns/terms.
    known = [s for s in COMMON_SKILLS if s.lower() in job_text.lower()]

    tokens = _tokenize(job_text)
    freq = {}
    for token in tokens:
        if token in RESUME_KEYWORD_STOPWORDS:
            continue
        if token.isdigit():
            continue
        if len(token) < 3:
            continue
        freq[token] = freq.get(token, 0) + 1

    ranked_tokens = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    aliases = {
        "apis": "API",
        "api": "API",
        "aws": "AWS",
        "seo": "SEO",
        "sql": "SQL",
        "etl": "ETL",
        "ui": "UI",
        "ux": "UX",
    }
    inferred = []
    seen_lower = {k.lower() for k in known}
    known_parts = set()
    for item in known:
        for part in item.lower().split():
            known_parts.add(part)
    for token, _ in ranked_tokens:
        normalized_token = token.strip(".")
        if normalized_token in known_parts:
            continue
        cleaned = aliases.get(normalized_token, normalized_token.capitalize())
        if cleaned.lower() in seen_lower:
            continue
        inferred.append(cleaned)
        seen_lower.add(cleaned.lower())
        if len(inferred) >= max(0, limit - len(known)):
            break

    combined = known + inferred
    return combined[:limit]


def _bucket_skills(keywords):
    technical_markers = {
        "python", "java", "react", "sql", "fastapi", "aws", "docker", "api", "etl",
        "excel", "tableau", "powerbi", "javascript", "typescript", "node", "flask",
        "django", "git", "kubernetes", "spark", "pandas", "numpy",
    }
    core_markers = {
        "communication", "teamwork", "leadership", "stakeholder", "collaboration",
        "analytics", "problem", "ownership", "prioritization", "presentation",
    }

    technical = []
    core = []
    for skill in keywords:
        lowered = skill.lower()
        if any(marker in lowered for marker in technical_markers):
            technical.append(skill)
        elif any(marker in lowered for marker in core_markers):
            core.append(skill)
        else:
            # Keep less-certain terms as technical by default for ATS density.
            technical.append(skill)

    return {
        "technical": technical[:10],
        "core": core[:6],
    }


def _role_focus_sentence(role_title: str):
    lowered = role_title.lower()
    if "data" in lowered or "analyst" in lowered:
        return "translating data into business decisions"
    if "marketing" in lowered or "seo" in lowered:
        return "driving measurable growth through campaign optimization"
    if "product" in lowered:
        return "aligning product priorities with user and business outcomes"
    if "design" in lowered or "ui" in lowered or "ux" in lowered:
        return "crafting user-centered experiences with clear usability outcomes"
    return "delivering reliable, scalable solutions in collaborative teams"


def _extract_first_matching_url(text: str, domain_hint: str = ""):
    matches = re.findall(r"https?://[^\s\]\)>,\"']+", text or "", flags=re.IGNORECASE)
    if not matches:
        return ""
    if domain_hint:
        for url in matches:
            if domain_hint.lower() in url.lower():
                return url
        return ""
    return matches[0]


def evaluate_answer(answer: str):
    question, candidate_answer = _split_question_and_answer(answer)
    answer_word_count = len(candidate_answer.split())

    if answer_word_count < 8:
        return {
            "score": 25,
            "feedback": "Insufficient answer. It is too short to assess the question properly.",
        }

    # 1) Relevance score (0..45): does the answer target the asked topic?
    relevance_score = 20
    relevance_note = " The answer may not be aligned with the selected question."
    if question:
        q_tokens = set(_tokenize(question))
        a_tokens = set(_tokenize(candidate_answer))
        exact_overlap = len(q_tokens.intersection(a_tokens))

        # Allow close variants (e.g., "leadership" vs "led") by prefix/substring similarity.
        fuzzy_overlap = 0
        for qt in q_tokens:
            if qt in a_tokens:
                continue
            for at in a_tokens:
                if qt[:4] == at[:4] or qt in at or at in qt:
                    fuzzy_overlap += 1
                    break

        overlap = exact_overlap + fuzzy_overlap
        denom = max(1, min(len(q_tokens), 8))
        relevance_ratio = overlap / denom

        # Skill-term bonus if the asked skill itself appears in answer.
        question_lower = question.lower()
        answer_lower = candidate_answer.lower()
        skill_bonus = 0
        for skill in COMMON_SKILLS:
            if skill.lower() in question_lower and skill.lower() in answer_lower:
                skill_bonus = 0.2
                break

        # Skill-hint bonus for semantically related wording.
        hint_bonus = 0
        for skill_key, hints in SKILL_HINTS.items():
            if skill_key in question_lower:
                for hint in hints:
                    if hint in answer_lower:
                        hint_bonus = 0.45
                        break
                if hint_bonus:
                    break

        relevance_ratio = min(1.0, relevance_ratio + skill_bonus + hint_bonus)
        relevance_score = int(min(45, round(relevance_ratio * 45)))

        if relevance_ratio < 0.2:
            relevance_note = " The answer is not aligned with the selected question."
        elif relevance_ratio < 0.4:
            relevance_note = " The answer is partially aligned with the selected question."
        else:
            relevance_note = " The answer is aligned with the selected question."

    # 2) Completeness score (0..35): sufficient structure for interview quality.
    answer_lower = candidate_answer.lower()
    context_words = {"project", "role", "team", "situation", "task", "challenge"}
    action_words = {"built", "implemented", "designed", "led", "managed", "created", "improved", "optimized"}
    outcome_words = {"result", "impact", "improved", "reduced", "increased", "delivered", "achieved"}

    completeness_score = 0
    if _contains_any(answer_lower, context_words):
        completeness_score += 10
    if _contains_any(answer_lower, action_words):
        completeness_score += 12
    if _contains_any(answer_lower, outcome_words):
        completeness_score += 8
    if re.search(r"\b\d+(\.\d+)?%?\b", candidate_answer):
        completeness_score += 5

    # 3) Depth score (0..20): enough detail without rewarding length alone.
    if answer_word_count >= 70:
        depth_score = 20
    elif answer_word_count >= 40:
        depth_score = 16
    elif answer_word_count >= 25:
        depth_score = 12
    else:
        depth_score = 8

    score = max(20, min(100, relevance_score + completeness_score + depth_score))

    # Gate the score if relevance is very low.
    if relevance_score < 12:
        score = min(score, 45)

    if score >= 80:
        sufficiency = "Sufficient answer for this question."
        feedback = "Strong response with good alignment, concrete actions, and measurable impact."
    elif score >= 60:
        sufficiency = "Mostly sufficient, but can be improved."
        feedback = "Answer is reasonably aligned. Add clearer outcomes and stronger specifics."
    elif score >= 45:
        sufficiency = "Partially sufficient."
        feedback = "Some relevant content is present, but details and impact are limited."
    else:
        sufficiency = "Not sufficient for this question."
        feedback = "Answer does not adequately address the asked question."

    return {"score": score, "feedback": f"{sufficiency} {feedback}{relevance_note}"}

async def generate_resume_reference(
    job_text: str,
    profile_text: str = "",
    linkedin: str = "",
    github: str = "",
    portfolio: str = "",
):
    role_title = _extract_role_title(job_text)
    role_family = _detect_role_family(job_text, role_title)
    role_keywords = _extract_role_keywords(job_text)
    skill_buckets = _bucket_skills(role_keywords)

    top_keywords = role_keywords[:5]
    role_focus = _role_focus_sentence(role_title)
    summary = (
        f"{role_title} profile with a track record of {role_focus}. "
        f"Demonstrates alignment with target requirements in {', '.join(top_keywords[:3])}. "
        f"Builds outcomes-focused projects and communicates impact with clear, measurable results."
    )
    if profile_text.strip():
        summary = f"{summary} Background context to incorporate: {profile_text.strip()}"

    tech_skills = skill_buckets["technical"] or role_keywords[:8]
    role_core_defaults = {
        "legal": ["Legal Writing", "Client Communication", "Risk Assessment"],
        "finance": ["Analytical Thinking", "Attention to Detail", "Stakeholder Communication"],
        "marketing": ["Campaign Planning", "Audience Insight", "Communication"],
        "hr": ["Stakeholder Management", "Communication", "Conflict Resolution"],
        "operations": ["Process Discipline", "Coordination", "Problem Solving"],
    }
    core_skills = skill_buckets["core"] or role_core_defaults.get(role_family, ["Communication", "Collaboration", "Problem Solving"])

    work_samples_label = "PROJECTS"
    education_hint = "B.S. / B.Tech in Relevant Discipline"
    experience_bullets = []
    projects = []

    if role_family == "legal":
        work_samples_label = "CASEWORK / LEGAL MATTERS"
        education_hint = "LL.B / LL.M / Relevant Legal Qualification"
        experience_bullets = [
            "Drafted and reviewed contracts, identifying legal and commercial risk clauses with clear mitigation notes.",
            "Conducted legal research and prepared concise briefs for internal teams and client communication.",
            "Supported compliance checks and due-diligence documentation with accurate, deadline-driven execution.",
        ]
        projects = [
            {
                "title": "Contract Review and Risk Flagging Dossier",
                "bullets": [
                    "Prepared clause-by-clause contract review summaries for business stakeholders.",
                    "Highlighted liability, indemnity, and termination risks with practical fallback language.",
                    "Maintained issue tracker for negotiation rounds and closure status.",
                ],
            },
            {
                "title": "Regulatory Compliance Tracker",
                "bullets": [
                    "Built periodic compliance checklist mapped to applicable legal requirements.",
                    "Documented non-compliance observations and remediation follow-up actions.",
                    "Presented concise updates for audit/legal leadership reviews.",
                ],
            },
        ]
    elif role_family == "finance":
        work_samples_label = "ANALYSIS HIGHLIGHTS"
        education_hint = "B.Com / M.Com / CA / CFA / Finance Degree"
        experience_bullets = [
            "Performed financial analysis on cost, revenue, and variance trends to support business decisions.",
            "Prepared reconciliations and reporting packs with high accuracy and timeline discipline.",
            "Collaborated with stakeholders to explain assumptions, risks, and financial implications.",
        ]
        projects = [
            {
                "title": "Financial Performance Analysis Pack",
                "bullets": [
                    "Built month-on-month and variance analysis to identify major movement drivers.",
                    "Summarized findings into management-ready insights and recommended actions.",
                    "Improved report consistency using standardized templates and checks.",
                ],
            },
            {
                "title": "Budget vs Actual Monitoring Model",
                "bullets": [
                    "Tracked budget utilization and flagged early risk signals.",
                    "Documented deviations with root-cause notes and mitigation options.",
                    "Supported planning reviews with scenario-based commentary.",
                ],
            },
        ]
    elif role_family == "hr":
        work_samples_label = "HR INITIATIVES"
        education_hint = "MBA HR / BBA / Human Resources Degree"
        experience_bullets = [
            "Managed recruitment coordination, interview scheduling, and candidate communication workflows.",
            "Maintained hiring tracker and improved turnaround visibility for stakeholders.",
            "Supported onboarding and employee engagement activities with structured execution.",
        ]
        projects = [
            {
                "title": "Recruitment Funnel Optimization",
                "bullets": [
                    "Mapped funnel drop-offs and proposed process improvements.",
                    "Improved candidate follow-up consistency through SLA-based tracking.",
                    "Reported role-wise hiring status with actionable bottleneck insights.",
                ],
            },
            {
                "title": "Onboarding Experience Playbook",
                "bullets": [
                    "Standardized onboarding checklist for smoother first-week experience.",
                    "Collected feedback and improved handoff between HR and managers.",
                    "Reduced early-stage confusion through clear documentation.",
                ],
            },
        ]
    elif role_family == "marketing":
        work_samples_label = "CAMPAIGN HIGHLIGHTS"
        education_hint = "Marketing / Business / Communications Degree"
        experience_bullets = [
            "Planned and executed campaign tasks across channels with performance tracking.",
            "Analyzed CTR, conversion, and engagement metrics to optimize messaging.",
            "Worked with creative/content teams to improve campaign output quality and consistency.",
        ]
        projects = [
            {
                "title": "Campaign Optimization Case",
                "bullets": [
                    "Tested audience and messaging variants to improve performance.",
                    "Tracked funnel metrics and summarized learnings for next sprint.",
                    "Documented budget-impact tradeoffs for stakeholder decisions.",
                ],
            },
            {
                "title": "SEO and Content Growth Plan",
                "bullets": [
                    "Performed keyword mapping and on-page recommendations.",
                    "Reviewed ranking trends and updated content priorities accordingly.",
                    "Presented traffic-impact opportunities with execution roadmap.",
                ],
            },
        ]
    elif role_family == "operations":
        work_samples_label = "PROCESS IMPROVEMENT HIGHLIGHTS"
        education_hint = "Operations / Supply Chain / Business Degree"
        experience_bullets = [
            "Mapped workflows and removed bottlenecks to improve turnaround time and quality.",
            "Defined SOP checkpoints and monitored adherence with issue-tracking.",
            "Coordinated cross-team dependencies to improve delivery reliability.",
        ]
        projects = [
            {
                "title": "Workflow Efficiency Improvement",
                "bullets": [
                    "Analyzed process stages and identified delay/root-cause patterns.",
                    "Implemented prioritization and handoff improvements.",
                    "Reported cycle-time improvements with before/after comparison.",
                ],
            },
            {
                "title": "Service Quality Monitoring Sheet",
                "bullets": [
                    "Built KPI tracking for defects, delays, and escalation volumes.",
                    "Defined corrective action log and ownership model.",
                    "Improved follow-through consistency across teams.",
                ],
            },
        ]
    else:
        experience_bullets = [
            f"Executed {role_title.lower()} responsibilities using {tech_skills[0]} and {tech_skills[1] if len(tech_skills) > 1 else tech_skills[0]} to deliver scoped milestones on schedule.",
            "Converted ambiguous requirements into implementation plans, prioritized deliverables, and maintained quality through testing and peer review.",
            "Communicated progress, risks, and tradeoffs with stakeholders, improving delivery predictability and team alignment.",
        ]
        if len(tech_skills) > 2:
            experience_bullets.append(
                f"Used {tech_skills[2]} to improve performance, reliability, or reporting quality and document repeatable best practices."
            )
        projects = [
            {
                "title": f"{role_title} Capstone Project",
                "bullets": [
                    f"Built an end-to-end solution aligned to JD priorities, integrating {tech_skills[0]} and {tech_skills[1] if len(tech_skills) > 1 else tech_skills[0]}.",
                    "Defined success metrics early, then iterated on architecture and implementation to improve measurable outcomes.",
                    "Presented project decisions, business impact, and next-step roadmap in recruiter-friendly case-study format.",
                ],
            },
            {
                "title": "Automation and Impact Tracking Project",
                "bullets": [
                    "Automated repetitive workflows to reduce manual effort and improve turnaround time for recurring tasks.",
                    "Implemented dashboards or reporting views to track quality, adoption, and performance trends.",
                    f"Applied core skills in {', '.join(core_skills[:2])} to collaborate across functions and close delivery gaps.",
                ],
            },
        ]

    guidance = [
        "Replace placeholders with real achievements, including quantifiable metrics (%, time saved, revenue, accuracy, scale).",
        f"Prioritize bullets that mirror JD keywords: {', '.join(top_keywords)}.",
        "Keep each bullet action-first and outcome-focused to maximize recruiter readability and ATS relevance.",
    ]

    detected_links = extract_profile_links(profile_text)
    linkedin_url = linkedin.strip() or detected_links["linkedin"]
    github_url = github.strip() or detected_links["github"]
    portfolio_url = portfolio.strip() or detected_links["portfolio"]
    if portfolio_url and portfolio_url in {linkedin_url, github_url}:
        portfolio_url = ""

    if not linkedin_url:
        linkedin_url = ""
    if not github_url:
        github_url = ""
    if not portfolio_url:
        portfolio_url = ""

    reference = {
        "name": "Your Name",
        "email": "youremail@example.com",
        "phone": "+1 (000) 000-0000",
        "location": "Your City, ST",
        "linkedin": linkedin_url,
        "github": github_url,
        "portfolio": portfolio_url,
        "headline": role_title,
        "summary": summary,
        "skills": role_keywords,
        "skills_grouped": {
            "technical": tech_skills,
            "core": core_skills,
        },
        "work_samples_label": work_samples_label,
        "experience": [
            {
                "role": f"{role_title} Intern / Project Contributor",
                "org": "Company / Lab / Student Organization",
                "duration": "MM/YYYY - Present",
                "bullets": experience_bullets,
            }
        ],
        "projects": projects,
        "education": [
            {
                "degree": education_hint,
                "institute": "Your University",
                "year": "Expected YYYY",
            }
        ],
        "guidance_notes": guidance,
    }
    return reference


def extract_profile_links(text: str):
    linkedin_url = _extract_first_matching_url(text, "linkedin.com")
    github_url = _extract_first_matching_url(text, "github.com")
    portfolio_url = _extract_first_matching_url(text)
    if portfolio_url and portfolio_url in {linkedin_url, github_url}:
        portfolio_url = ""
    return {
        "linkedin": linkedin_url,
        "github": github_url,
        "portfolio": portfolio_url,
    }


def format_resume_reference(reference: dict):
    lines = [
        reference.get("name", "Your Name"),
        reference.get("headline", ""),
        "",
        "CONTACT",
        f"{reference.get('email', '')} | {reference.get('phone', '')} | {reference.get('location', '')}",
        f"{reference.get('linkedin', '')} | {reference.get('github', '')} | {reference.get('portfolio', '')}",
        "",
        "SUMMARY",
        reference.get("summary", ""),
        "",
        "SKILLS",
    ]

    skills_grouped = reference.get("skills_grouped", {})
    technical = skills_grouped.get("technical", [])
    core = skills_grouped.get("core", [])

    if technical:
        lines.append(f"Technical: {', '.join(technical)}")
    if core:
        lines.append(f"Core: {', '.join(core)}")
    if not technical and not core:
        lines.append(", ".join(reference.get("skills", [])))

    lines.extend([
        "",
        "EXPERIENCE",
    ])

    for exp in reference.get("experience", []):
        lines.append(f"{exp.get('role', '')} - {exp.get('org', '')} ({exp.get('duration', '')})")
        for bullet in exp.get("bullets", []):
            lines.append(f"- {bullet}")
        lines.append("")

    lines.append(reference.get("work_samples_label", "PROJECTS"))
    for project in reference.get("projects", []):
        lines.append(project.get("title", ""))
        for bullet in project.get("bullets", []):
            lines.append(f"- {bullet}")
        lines.append("")

    lines.append("EDUCATION")
    for edu in reference.get("education", []):
        lines.append(f"{edu.get('degree', '')} - {edu.get('institute', '')} ({edu.get('year', '')})")

    return "\n".join(lines).strip()


def _collect_resume_bullets(reference: dict):
    bullets = []
    for exp in reference.get("experience", []):
        for bullet in exp.get("bullets", []):
            bullets.append({
                "section": "experience",
                "title": exp.get("role", ""),
                "text": bullet,
            })
    for project in reference.get("projects", []):
        for bullet in project.get("bullets", []):
            bullets.append({
                "section": "projects",
                "title": project.get("title", ""),
                "text": bullet,
            })
    return bullets


def _score_single_bullet(bullet: str, job_keywords):
    lowered = bullet.lower()
    has_action = bool(re.search(r"\b(built|implemented|designed|led|optimized|automated|delivered|improved)\b", lowered))
    has_metric = bool(re.search(r"\b\d+(\.\d+)?%?\b", bullet))
    has_impact = bool(re.search(r"\b(result|impact|reduced|increased|improved|achieved|delivered)\b", lowered))

    keyword_hits = 0
    for keyword in job_keywords[:10]:
        if keyword.lower() in lowered:
            keyword_hits += 1
    keyword_score = min(35, keyword_hits * 7)

    score = 20 + keyword_score
    score += 20 if has_action else 0
    score += 20 if has_impact else 0
    score += 20 if has_metric else 0
    score = min(100, score)

    if score >= 80:
        rating = "strong"
    elif score >= 60:
        rating = "good"
    else:
        rating = "weak"

    suggestion = "Add a measurable outcome and one JD keyword for stronger recruiter impact."
    if rating == "strong":
        suggestion = "Keep this bullet; it is action-oriented and role-aligned."
    elif rating == "good":
        suggestion = "Add one concrete metric to move this bullet to top-tier quality."

    return {
        "score": score,
        "rating": rating,
        "has_action": has_action,
        "has_metric": has_metric,
        "has_impact": has_impact,
        "keyword_hits": keyword_hits,
        "suggestion": suggestion,
    }


def score_resume_bullets(reference: dict, job_text: str):
    job_keywords = _extract_role_keywords(job_text)
    bullet_rows = []
    for row in _collect_resume_bullets(reference):
        scoring = _score_single_bullet(row["text"], job_keywords)
        bullet_rows.append({
            "section": row["section"],
            "title": row["title"],
            "bullet": row["text"],
            **scoring,
        })

    avg_score = int(sum(r["score"] for r in bullet_rows) / len(bullet_rows)) if bullet_rows else 0
    return {
        "average_score": avg_score,
        "bullets": bullet_rows,
    }


def generate_evidence_links(reference: dict):
    evidence_types = [
        ("GitHub commit/PR", "Link to exact commit or pull request"),
        ("Demo/video", "Short demo proving functionality"),
        ("Metrics screenshot", "Dashboard/report showing impact"),
        ("Certificate/document", "Training or credential proof"),
    ]
    output = []
    bullets = _collect_resume_bullets(reference)
    for idx, row in enumerate(bullets):
        evidence_type, hint = evidence_types[idx % len(evidence_types)]
        output.append({
            "claim": row["text"],
            "section": row["section"],
            "evidence_type": evidence_type,
            "suggested_artifact": hint,
            "proof_link_placeholder": f"https://add-your-proof-link/{row['section']}/{idx+1}",
        })
    return output


def generate_gap_autopilot_plan(job_text: str, reference: dict):
    required_keywords = _extract_role_keywords(job_text, limit=12)
    current_skills = {s.lower() for s in reference.get("skills", [])}
    missing = [k for k in required_keywords if k.lower() not in current_skills][:6]

    if not missing:
        missing = ["Advanced system design", "Interview storytelling", "Portfolio evidence packaging"]

    return {
        "missing_priorities": missing,
        "plan_30_60_90": {
            "30_days": [f"Complete focused learning sprint on {missing[0]}.", f"Ship one mini project using {missing[0]} and document outcomes."],
            "60_days": [f"Add production-style project depth with {missing[1] if len(missing) > 1 else missing[0]}.", "Improve resume bullets with quantified impact and proof links."],
            "90_days": [f"Deliver showcase project integrating {missing[2] if len(missing) > 2 else missing[0]} with measurable KPI gains.", "Run mock interviews and refine role-specific resume variants."],
        },
    }


def simulate_recruiter_review(reference: dict, job_text: str):
    resume_text = format_resume_reference(reference).lower()
    job_keywords = _extract_role_keywords(job_text, limit=12)
    keyword_hits = sum(1 for k in job_keywords if k.lower() in resume_text)
    coverage = int((keyword_hits / max(1, len(job_keywords))) * 100)

    bullet_quality = score_resume_bullets(reference, job_text)["average_score"]
    section_bonus = 100 if all(reference.get(section) for section in ["summary", "skills", "experience", "projects", "education"]) else 70

    ats_score = int(0.6 * coverage + 0.4 * section_bonus)
    recruiter_score = int(0.55 * bullet_quality + 0.45 * coverage)
    hiring_manager_score = int(0.6 * bullet_quality + 0.4 * min(100, len(reference.get("projects", [])) * 35 + len(reference.get("experience", [])) * 30))

    overall = int((ats_score + recruiter_score + hiring_manager_score) / 3)
    verdict = "Interview Ready" if overall >= 75 else "Needs Strengthening"

    return {
        "overall_score": overall,
        "verdict": verdict,
        "personas": [
            {"persona": "ATS Parser", "score": ats_score, "reason": f"Keyword coverage: {coverage}% across target JD terms."},
            {"persona": "Recruiter", "score": recruiter_score, "reason": "Assesses readability, relevance, and impact language."},
            {"persona": "Hiring Manager", "score": hiring_manager_score, "reason": "Assesses project depth, execution, and technical signal."},
        ],
    }


def generate_role_variants(reference: dict, job_text: str):
    base_summary = reference.get("summary", "")
    role_title = _extract_role_title(job_text)
    role_family = _detect_role_family(job_text, role_title)
    skills = reference.get("skills", [])
    variants = []

    role_tracks = {
        "legal": [
            ("Corporate Counsel Variant", ["Corporate Law", "Contract Drafting", "Compliance"], "Corporate Counsel"),
            ("Compliance Variant", ["Compliance", "Due Diligence", "Regulatory Affairs"], "Compliance Associate"),
            ("Dispute Resolution Variant", ["Litigation", "Arbitration", "Negotiation"], "Legal Associate"),
        ],
        "finance": [
            ("Financial Analyst Variant", ["Financial Analysis", "Accounting", "Reporting"], "Financial Analyst"),
            ("Audit Variant", ["Auditing", "Compliance", "Risk Management"], "Audit Associate"),
            ("FP&A Variant", ["Financial Analysis", "Forecasting", "Budgeting"], "FP&A Analyst"),
        ],
        "marketing": [
            ("Performance Marketing Variant", ["Campaign", "SEO", "Analytics"], "Performance Marketer"),
            ("Brand Variant", ["Brand", "Content", "Communication"], "Brand Associate"),
            ("Growth Variant", ["Growth", "Funnel", "Conversion"], "Growth Analyst"),
        ],
        "hr": [
            ("Talent Acquisition Variant", ["Recruitment", "Communication", "Stakeholder"], "Talent Acquisition Associate"),
            ("HR Operations Variant", ["Human Resources", "Process", "Compliance"], "HR Operations Associate"),
            ("People Success Variant", ["Engagement", "Communication", "Teamwork"], "People Operations Associate"),
        ],
    }
    default_tracks = [
        ("Backend Variant", ["Python", "FastAPI", "SQL", "API", "AWS"], "Backend Engineer"),
        ("Data Variant", ["Python", "SQL", "Analytics", "Dashboard", "ETL"], "Data Analyst"),
        ("Product Variant", ["Communication", "Stakeholder", "Ownership", "Prioritization"], "Product Associate"),
    ]
    tracks = role_tracks.get(role_family, default_tracks)

    for name, focus, role in tracks:
        focused = [s for s in skills if s.lower() in {f.lower() for f in focus}] or focus[:4]
        variants.append({
            "variant_name": name,
            "headline": f"{role} Candidate ({role_title} alignment)",
            "summary": f"{base_summary} This variant emphasizes {', '.join(focused[:3])} for {role.lower()} opportunities.",
            "skills_focus": focused[:6],
        })
    return variants


def convert_interview_to_bullets(interview_story: str):
    if not interview_story.strip():
        return []
    chunks = re.split(r"[.\n]+", interview_story)
    chunks = [c.strip() for c in chunks if c.strip()]
    bullets = []
    for chunk in chunks[:3]:
        sentence = chunk[0].upper() + chunk[1:] if len(chunk) > 1 else chunk.upper()
        if not re.search(r"\b(improved|increased|reduced|delivered|built|implemented|led)\b", sentence.lower()):
            sentence = f"Delivered impact by {sentence.lower()}."
        if not sentence.endswith("."):
            sentence += "."
        bullets.append(sentence)
    return bullets


def check_portfolio_consistency(reference: dict, portfolio_text: str):
    bullets = _collect_resume_bullets(reference)
    if not portfolio_text.strip():
        return {
            "consistency_score": 45,
            "matched_claims": [],
            "unverified_claims": [b["text"] for b in bullets[:5]],
            "risk_note": "No portfolio evidence provided; resume claims are not currently verifiable.",
        }

    portfolio_lower = portfolio_text.lower()
    matched = []
    missing = []
    for row in bullets:
        key_tokens = [t for t in _tokenize(row["text"]) if len(t) > 4][:4]
        if key_tokens and any(t in portfolio_lower for t in key_tokens):
            matched.append(row["text"])
        else:
            missing.append(row["text"])

    score = int((len(matched) / max(1, len(bullets))) * 100)
    return {
        "consistency_score": score,
        "matched_claims": matched[:6],
        "unverified_claims": missing[:6],
        "risk_note": "Align portfolio artifacts to each critical resume claim to improve recruiter trust.",
    }


def benchmark_against_top_candidates(reference: dict, job_text: str):
    bullet_scores = score_resume_bullets(reference, job_text)
    avg_bullet = bullet_scores.get("average_score", 0)
    keyword_coverage = simulate_recruiter_review(reference, job_text)["personas"][0]["score"]
    proof_count = len(generate_evidence_links(reference))
    project_count = len(reference.get("projects", []))

    percentile = min(99, int(0.4 * avg_bullet + 0.35 * keyword_coverage + 0.15 * min(100, proof_count * 8) + 0.10 * min(100, project_count * 35)))
    tier = "Top 10%" if percentile >= 90 else "Above Average" if percentile >= 70 else "Developing"
    return {
        "estimated_percentile": percentile,
        "benchmark_tier": tier,
        "gaps_to_top_10": [
            "Increase quantified outcomes per bullet.",
            "Attach direct evidence links to major claims.",
            "Show deeper project complexity tied to JD priorities.",
        ] if percentile < 90 else ["Maintain evidence-backed impact language and interview readiness."],
    }


async def build_resume_intelligence(
    job_text: str,
    profile_text: str = "",
    portfolio_text: str = "",
    interview_story: str = "",
    linkedin: str = "",
    github: str = "",
    portfolio: str = "",
):
    reference = await generate_resume_reference(
        job_text,
        profile_text,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
    )
    story_bullets = convert_interview_to_bullets(interview_story)
    if story_bullets:
        reference.setdefault("experience", [])
        if reference["experience"]:
            reference["experience"][0].setdefault("bullets", [])
            reference["experience"][0]["bullets"] = story_bullets + reference["experience"][0]["bullets"]

    resume_text = format_resume_reference(reference)
    bullet_quality = score_resume_bullets(reference, job_text)
    evidence = generate_evidence_links(reference)
    gap_plan = generate_gap_autopilot_plan(job_text, reference)
    recruiter_simulation = simulate_recruiter_review(reference, job_text)
    variants = generate_role_variants(reference, job_text)
    consistency = check_portfolio_consistency(reference, portfolio_text)
    benchmark = benchmark_against_top_candidates(reference, job_text)

    return {
        "resume_reference": reference,
        "resume_text": resume_text,
        "evidence_links": evidence,
        "gap_autopilot": gap_plan,
        "recruiter_simulation": recruiter_simulation,
        "bullet_quality": bullet_quality,
        "role_variants": variants,
        "interview_bullets": story_bullets,
        "portfolio_consistency": consistency,
        "benchmark_panel": benchmark,
    }


async def generate_explanation(score):
    if score>=80:
        text="Strong match."
    elif score>=50:
        text="Moderate match."
    else:
        text="Low match."
    return {"match_explanation":text,"confidence":round(score/100,2)}
