import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

const escapeHtml = (value = "") =>
  String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const isHttpUrl = (value = "") => /^https?:\/\//i.test(String(value).trim());

const buildResumeDocumentHtml = (reference) => {
  const skillsGrouped = reference.skills_grouped || {};
  const technical = skillsGrouped.technical || [];
  const core = skillsGrouped.core || [];
  const experience = reference.experience || [];
  const projects = reference.projects || [];
  const education = reference.education || [];

  const bulletItems = (items = []) =>
    items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  const docLink = (url, label) =>
    isHttpUrl(url)
      ? `<a href="${escapeHtml(url)}">${escapeHtml(label)}</a>`
      : escapeHtml(`${label}: add URL`);

  return `
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${escapeHtml(reference.name || "Model Resume")}</title>
    <style>
      body { font-family: Calibri, Arial, sans-serif; margin: 34px; color: #111827; }
      h1 { margin: 0; font-size: 28px; }
      h2 { margin: 18px 0 8px; font-size: 14px; letter-spacing: 0.08em; border-bottom: 1px solid #d1d5db; padding-bottom: 5px; }
      .contact { margin-top: 4px; color: #374151; font-size: 12px; }
      .headline { margin-top: 6px; font-weight: 700; color: #1f2937; font-size: 13px; }
      p { margin: 0; line-height: 1.45; }
      .summary { line-height: 1.5; font-size: 13px; }
      .meta { font-size: 12px; color: #374151; margin-bottom: 4px; }
      ul { margin: 0; padding-left: 18px; }
      li { margin: 2px 0; line-height: 1.45; font-size: 13px; }
      .row { margin-bottom: 11px; }
      .label { font-weight: 700; }
    </style>
  </head>
  <body>
    <h1>${escapeHtml(reference.name || "Your Name")}</h1>
    <div class="contact">${escapeHtml(reference.email || "")} | ${escapeHtml(reference.phone || "")} | ${escapeHtml(reference.location || "")}</div>
    <div class="contact">
      ${docLink(reference.linkedin, "LinkedIn")} | ${docLink(reference.github, "GitHub")} | ${docLink(reference.portfolio, "Portfolio")}
    </div>
    <div class="headline">${escapeHtml(reference.headline || "")}</div>

    <h2>SUMMARY</h2>
    <p class="summary">${escapeHtml(reference.summary || "")}</p>

    <h2>SKILLS</h2>
    ${
      technical.length
        ? `<p><span class="label">Technical:</span> ${escapeHtml(technical.join(", "))}</p>`
        : ""
    }
    ${core.length ? `<p><span class="label">Core:</span> ${escapeHtml(core.join(", "))}</p>` : ""}
    ${
      !technical.length && !core.length
        ? `<p>${escapeHtml((reference.skills || []).join(", "))}</p>`
        : ""
    }

    <h2>EXPERIENCE</h2>
    ${experience
      .map(
        (exp) => `
      <div class="row">
        <p class="label">${escapeHtml(exp.role || "")}</p>
        <p class="meta">${escapeHtml(exp.org || "")} | ${escapeHtml(exp.duration || "")}</p>
        <ul>${bulletItems(exp.bullets || [])}</ul>
      </div>
    `
      )
      .join("")}

    <h2>PROJECTS</h2>
    ${projects
      .map(
        (project) => `
      <div class="row">
        <p class="label">${escapeHtml(project.title || "")}</p>
        <ul>${bulletItems(project.bullets || [])}</ul>
      </div>
    `
      )
      .join("")}

    <h2>EDUCATION</h2>
    ${education
      .map(
        (edu) => `
      <div class="row">
        <p class="label">${escapeHtml(edu.degree || "")}</p>
        <p class="meta">${escapeHtml(edu.institute || "")} | ${escapeHtml(edu.year || "")}</p>
      </div>
    `
      )
      .join("")}
  </body>
</html>`;
};

const compactResumeForSinglePage = (reference) => {
  const clone = JSON.parse(JSON.stringify(reference || {}));
  const clampText = (text = "", max = 420) =>
    text.length > max ? `${text.slice(0, max - 3).trim()}...` : text;

  clone.summary = clampText(clone.summary || "", 420);

  if (clone.skills_grouped?.technical) {
    clone.skills_grouped.technical = clone.skills_grouped.technical.slice(0, 10);
  }
  if (clone.skills_grouped?.core) {
    clone.skills_grouped.core = clone.skills_grouped.core.slice(0, 6);
  }
  if (Array.isArray(clone.skills)) {
    clone.skills = clone.skills.slice(0, 14);
  }

  clone.experience = (clone.experience || []).slice(0, 2).map((exp) => ({
    ...exp,
    bullets: (exp.bullets || []).slice(0, 3).map((b) => clampText(b, 180)),
  }));

  clone.projects = (clone.projects || []).slice(0, 2).map((project) => ({
    ...project,
    bullets: (project.bullets || []).slice(0, 3).map((b) => clampText(b, 170)),
  }));

  clone.education = (clone.education || []).slice(0, 2);
  return clone;
};

const estimateResumeDensity = (reference) => {
  const summaryLength = (reference.summary || "").length;
  const experienceBullets = (reference.experience || []).reduce(
    (count, exp) => count + (exp.bullets || []).length,
    0
  );
  const projectBullets = (reference.projects || []).reduce(
    (count, project) => count + (project.bullets || []).length,
    0
  );
  const skillCount =
    (reference.skills_grouped?.technical || []).length +
    (reference.skills_grouped?.core || []).length +
    (!reference.skills_grouped?.technical?.length && !reference.skills_grouped?.core?.length
      ? (reference.skills || []).length
      : 0);

  return (
    summaryLength +
    experienceBullets * 120 +
    projectBullets * 110 +
    skillCount * 20 +
    (reference.experience || []).length * 130 +
    (reference.projects || []).length * 120 +
    (reference.education || []).length * 70
  );
};

const prepareExportResume = (reference) => {
  // Adaptive export:
  // - lighter content => compact one-page style
  // - richer content => keep full detail for multi-page output
  const density = estimateResumeDensity(reference);
  const SHOULD_STAY_COMPACT = density <= 2100;
  return SHOULD_STAY_COMPACT ? compactResumeForSinglePage(reference) : reference;
};

const decodeGoogleJwt = (token) => {
  try {
    const payload = token.split(".")[1];
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = decodeURIComponent(
      atob(normalized)
        .split("")
        .map((char) => `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`)
        .join("")
    );
    return JSON.parse(decoded);
  } catch (error) {
    return null;
  }
};

function App() {
  const [file, setFile] = useState(null);
  const [job, setJob] = useState("");
  const [mode, setMode] = useState("agent");
  const [resumeProfile, setResumeProfile] = useState("");
  const [portfolioContext, setPortfolioContext] = useState("");
  const [interviewStory, setInterviewStory] = useState("");
  const [detectedLinks, setDetectedLinks] = useState(null);

  const [analysisData, setAnalysisData] = useState(null);
  const [analysisKey, setAnalysisKey] = useState("");

  const [interviewQuestions, setInterviewQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [interviewAnswer, setInterviewAnswer] = useState("");
  const [interviewEval, setInterviewEval] = useState(null);

  const [resumeDraft, setResumeDraft] = useState(null);
  const [resumeDraftText, setResumeDraftText] = useState("");
  const [resumeIntel, setResumeIntel] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [showAuthGate, setShowAuthGate] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [pendingDownload, setPendingDownload] = useState(false);
  const [gisReady, setGisReady] = useState(false);
  const [googleClientIdInput, setGoogleClientIdInput] = useState("");
  const [googleClientId, setGoogleClientId] = useState("");
  const [authMethod, setAuthMethod] = useState("google");
  const [otpEmail, setOtpEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);
  const [demoOtpCode, setDemoOtpCode] = useState("");
  const [smtpStatus, setSmtpStatus] = useState(null);
  const googleButtonRef = useRef(null);

  const modeCards = [
    {
      id: "agent",
      title: "Resume Match",
      subtitle: "Upload resume + job description for skill match analysis",
      tone: "tone-blue",
      placeholder: "Paste the target job description here...",
    },
    {
      id: "recruiter",
      title: "Recruiter View",
      subtitle: "Get recruiter decision, missing skills, and roadmap",
      tone: "tone-amber",
      placeholder: "Paste the target job description for recruiter decision...",
    },
    {
      id: "interview",
      title: "Interview Eval",
      subtitle: "Generate mock questions first, then submit your answer",
      tone: "tone-green",
      placeholder: "Paste the target job description to generate mock questions...",
    },
    {
      id: "resume_builder",
      title: "Model Resume",
      subtitle: "Generate a recruiter-style, JD-aligned reference resume",
      tone: "tone-blue",
      placeholder: "Paste the target job description to generate a market-ready model resume...",
    },
  ];

  const currentMode = modeCards.find((card) => card.id === mode) || modeCards[0];

  const getInputKey = () => {
    if (!file) return "";
    return `${job.trim()}|${file.name}|${file.size}|${file.lastModified}`;
  };

  useEffect(() => {
    setAnalysisData(null);
    setAnalysisKey("");
    setInterviewQuestions([]);
    setSelectedQuestion("");
    setInterviewAnswer("");
    setInterviewEval(null);
    setResumeDraft(null);
    setResumeDraftText("");
    setResumeIntel(null);
    setDetectedLinks(null);
  }, [job, file]);

  useEffect(() => {
    const stored = localStorage.getItem("internpilot_google_client_id") || "";
    const initial = GOOGLE_CLIENT_ID || stored;
    setGoogleClientId(initial);
    setGoogleClientIdInput(initial);
  }, []);

  useEffect(() => {
    if (window.google?.accounts?.id) {
      setGisReady(true);
      return;
    }

    const existing = document.getElementById("google-identity-script");
    if (existing) {
      existing.addEventListener("load", () => setGisReady(true), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.id = "google-identity-script";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => setGisReady(true);
    document.body.appendChild(script);
  }, []);

  useEffect(() => {
    if (!showAuthGate || !gisReady || !googleClientId || !googleButtonRef.current) return;
    if (authMethod !== "google") return;
    if (!window.google?.accounts?.id) return;

    setAuthError("");
    window.google.accounts.id.initialize({
      client_id: googleClientId,
      callback: (response) => {
        const payload = decodeGoogleJwt(response.credential || "");
        if (!payload) {
          setAuthError("Google login failed. Please try again.");
          return;
        }

        setAuthUser({
          name: payload.name || "Google User",
          email: payload.email || "",
          picture: payload.picture || "",
        });
        setShowAuthGate(false);
      },
    });

    googleButtonRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(googleButtonRef.current, {
      theme: "outline",
      size: "large",
      shape: "pill",
      text: "continue_with",
      width: 280,
    });
  }, [showAuthGate, gisReady, googleClientId, authMethod]);

  useEffect(() => {
    if (!showAuthGate) return;
    const fetchSmtpStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE}/auth/smtp-status`);
        setSmtpStatus(res.data || null);
      } catch (error) {
        setSmtpStatus(null);
      }
    };
    fetchSmtpStatus();
  }, [showAuthGate]);

  const ensureAnalysis = async () => {
    if (!file) {
      alert("Please attach a resume PDF first.");
      return null;
    }

    if (!job.trim()) {
      alert("Please paste a job description first.");
      return null;
    }

    const currentKey = getInputKey();
    if (analysisData && analysisKey === currentKey) {
      return analysisData;
    }

    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post(`${API_BASE}/upload-and-analyze`, formData, {
      params: { job },
    });

    setAnalysisData(res.data);
    setAnalysisKey(currentKey);
    return res.data;
  };

  const analyze = async () => {
    try {
      setInterviewEval(null);

      if (mode === "resume_builder") {
        if (!job.trim()) {
          alert("Please paste a job description first.");
          return;
        }

        let autoLinks = { linkedin: "", github: "", portfolio: "" };
        if (file) {
          const formData = new FormData();
          formData.append("file", file);
          try {
            const linksRes = await axios.post(`${API_BASE}/extract-resume-links`, formData);
            autoLinks = {
              linkedin: linksRes.data?.linkedin || "",
              github: linksRes.data?.github || "",
              portfolio: linksRes.data?.portfolio || "",
            };
            setDetectedLinks(autoLinks);
          } catch (e) {
            console.log("Could not auto-detect links from PDF:", e);
          }
        }

        const res = await axios.post(`${API_BASE}/generate-resume-reference`, null, {
          params: {
            job,
            profile: resumeProfile,
            portfolio: portfolioContext,
            interview_story: interviewStory,
            linkedin: autoLinks.linkedin || "",
            github: autoLinks.github || "",
            portfolio_url: autoLinks.portfolio || "",
          },
        });

        setResumeDraft(res.data.resume_reference || null);
        setResumeDraftText(res.data.resume_text || "");
        setResumeIntel(res.data || null);
        return;
      }

      if (mode === "interview") {
        if (interviewQuestions.length === 0) {
          const data = await ensureAnalysis();
          if (!data) return;

          const questions = data.interview_questions || [];
          if (!questions.length) {
            alert("No interview questions could be generated.");
            return;
          }

          setInterviewQuestions(questions);
          setSelectedQuestion(questions[0]);
          setInterviewAnswer("");
          return;
        }

        if (!interviewAnswer.trim()) {
          alert("Please type your answer before evaluation.");
          return;
        }

        const combinedAnswer = selectedQuestion
          ? `Question: ${selectedQuestion}\nAnswer: ${interviewAnswer}`
          : interviewAnswer;

        const evalRes = await axios.post(`${API_BASE}/evaluate-answer`, null, {
          params: { answer: combinedAnswer },
        });

        setInterviewEval(evalRes.data);
        return;
      }

      await ensureAnalysis();
    } catch (err) {
      console.log(err);
      alert("Backend request failed. Check backend terminal and API URL.");
    }
  };

  const performResumeDownload = () => {
    if (!resumeDraft) {
      alert("Generate a resume reference first.");
      return;
    }

    const exportReadyResume = prepareExportResume(resumeDraft);
    const html = buildResumeDocumentHtml(exportReadyResume);
    const blob = new Blob(["\ufeff", html], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "internpilot_model_resume.doc";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadResumeReference = () => {
    if (!resumeDraft) {
      alert("Generate a resume reference first.");
      return;
    }

    if (!authUser) {
      setPendingDownload(true);
      setShowAuthGate(true);
      setAuthMessage("");
      setAuthError("");
      return;
    }

    performResumeDownload();
  };

  useEffect(() => {
    if (authUser && pendingDownload) {
      performResumeDownload();
      setPendingDownload(false);
    }
  }, [authUser, pendingDownload]);

  const requestOtp = async () => {
    if (!otpEmail.trim()) {
      setAuthError("Enter your email first.");
      return;
    }
    try {
      setOtpLoading(true);
      setAuthError("");
      setAuthMessage("");
      const res = await axios.post(`${API_BASE}/auth/request-otp`, null, {
        params: { email: otpEmail.trim() },
      });
      if (!res.data?.ok) {
        setAuthError(res.data?.message || "Failed to request OTP.");
        return;
      }
      setOtpRequested(true);
      setDemoOtpCode(res.data?.demo_code || "");
      setAuthMessage(res.data?.message || "OTP sent.");
    } catch (error) {
      setAuthError("Failed to request OTP. Try again.");
    } finally {
      setOtpLoading(false);
    }
  };

  const verifyOtp = async () => {
    if (!otpEmail.trim() || !otpCode.trim()) {
      setAuthError("Enter both email and OTP code.");
      return;
    }
    try {
      setOtpLoading(true);
      setAuthError("");
      setAuthMessage("");
      const res = await axios.post(`${API_BASE}/auth/verify-otp`, null, {
        params: { email: otpEmail.trim(), code: otpCode.trim() },
      });
      if (!res.data?.ok) {
        setAuthError(res.data?.message || "OTP verification failed.");
        return;
      }
      setAuthUser({
        name: res.data?.user?.name || "User",
        email: res.data?.user?.email || otpEmail.trim(),
        picture: "",
      });
      setShowAuthGate(false);
      setAuthMessage("");
      setOtpRequested(false);
      setOtpCode("");
      setDemoOtpCode("");
    } catch (error) {
      setAuthError("OTP verification failed. Try again.");
    } finally {
      setOtpLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="sidebar">
        <img src="/internpilot-icon.svg" alt="InternPilot icon" className="sidebar-logo" />
        <button
          className={`rail-btn ${mode === "agent" ? "active" : ""}`}
          onClick={() => setMode("agent")}
          aria-label="Resume match mode"
          title="Resume match mode"
        >
          M
        </button>
        <button
          className={`rail-btn ${mode === "recruiter" ? "active" : ""}`}
          onClick={() => setMode("recruiter")}
          aria-label="Recruiter mode"
          title="Recruiter mode"
        >
          R
        </button>
        <button
          className={`rail-btn ${mode === "interview" ? "active" : ""}`}
          onClick={() => setMode("interview")}
          aria-label="Interview mode"
          title="Interview mode"
        >
          I
        </button>
        <button
          className={`rail-btn ${mode === "resume_builder" ? "active" : ""}`}
          onClick={() => setMode("resume_builder")}
          aria-label="Resume builder mode"
          title="Resume builder mode"
        >
          B
        </button>
      </div>

      <div className="canvas">
        <div className="orb" />
        <img
          src="/internpilot-logo.svg"
          alt="InternPilot logo"
          className="brand-logo"
        />

        <h1 className="headline">
          Hey! InternPilot
          <br />
          What can I help with?
        </h1>

        <div className="suggestions">
          {modeCards.map((card) => (
            <button
              key={card.id}
              className={`suggestion-card ${card.tone} ${mode === card.id ? "selected" : ""}`}
              onClick={() => setMode(card.id)}
            >
              <span className="chip">{card.title}</span>
              <span className="desc">{card.subtitle}</span>
            </button>
          ))}
        </div>

        <div className="inputBox">
          <p className="input-heading">{currentMode.title}</p>
          {mode === "resume_builder" && authUser && (
            <p className="auth-badge">Signed in as {authUser.email || authUser.name}</p>
          )}
          <textarea
            placeholder={currentMode.placeholder}
            value={job}
            onChange={(e) => setJob(e.target.value)}
          />

          {mode === "resume_builder" && (
            <>
              <textarea
                className="profile-box"
                placeholder="Optional: add your background (experience, projects, education) so the model resume shows what to highlight..."
                value={resumeProfile}
                onChange={(e) => setResumeProfile(e.target.value)}
              />
              <textarea
                className="profile-box"
                placeholder="Optional: paste portfolio evidence (GitHub links, project outcomes, docs) for consistency checking..."
                value={portfolioContext}
                onChange={(e) => setPortfolioContext(e.target.value)}
              />
              <textarea
                className="profile-box"
                placeholder="Optional: add interview/story notes; agent will convert strong lines into resume bullets..."
                value={interviewStory}
                onChange={(e) => setInterviewStory(e.target.value)}
              />
            </>
          )}

          {mode === "interview" && interviewQuestions.length > 0 && (
            <div className="interview-panel">
              <p className="interview-label">Mock Question</p>
              <div className="question-list">
                {interviewQuestions.map((q, idx) => (
                  <button
                    key={`${q}-${idx}`}
                    className={`question-btn ${selectedQuestion === q ? "active" : ""}`}
                    onClick={() => setSelectedQuestion(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>

              <p className="interview-label">Your Answer</p>
              <textarea
                className="answer-box"
                placeholder="Type your answer for the selected question..."
                value={interviewAnswer}
                onChange={(e) => setInterviewAnswer(e.target.value)}
              />
            </div>
          )}

          <div className="input-actions">
            {(mode === "agent" || mode === "recruiter" || mode === "interview" || mode === "resume_builder") && (
              <label className="attach-btn">
                Attach resume PDF {mode === "resume_builder" ? "(for auto links)" : ""}
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </label>
            )}

            {mode === "interview" && interviewQuestions.length > 0 && (
              <button
                className="attach-btn"
                onClick={() => {
                  setInterviewQuestions([]);
                  setSelectedQuestion("");
                  setInterviewAnswer("");
                  setInterviewEval(null);
                }}
              >
                New Questions
              </button>
            )}

            {mode === "resume_builder" && resumeDraft && (
              <button className="attach-btn" onClick={downloadResumeReference}>
                Download Resume (.doc)
              </button>
            )}

            <button className="send-btn" onClick={analyze}>
              {mode === "interview" ? (interviewQuestions.length === 0 ? "Q" : "E") : "^"}
            </button>
          </div>
        </div>

        {mode === "agent" && analysisData && (
          <div className="result">
            <h2>
              {analysisData.match_score}% - {analysisData.hireability_status}
            </h2>
            <p>{analysisData.match_explanation}</p>
            <p>Matched Skills: {(analysisData.matched_skills || []).join(", ") || "None"}</p>
            <p>Missing Skills: {(analysisData.missing_skills || []).join(", ") || "None"}</p>
            <p>
              Suggestions: {(analysisData.improvement_suggestions || []).join(" | ") || "None"}
            </p>
          </div>
        )}

        {mode === "recruiter" && analysisData && (
          <div className="result">
            <h2>
              {analysisData.match_score}% - {analysisData.hireability_status}
            </h2>
            <p>{analysisData.match_explanation}</p>
            <p>Decision: {analysisData.recruiter_decision}</p>
            <p>Matched Skills: {(analysisData.matched_skills || []).join(", ") || "None"}</p>
            <p>Missing Skills: {(analysisData.missing_skills || []).join(", ") || "None"}</p>
            <p>Roadmap: {(analysisData.career_roadmap || []).join(" | ") || "None"}</p>
            <p>Interview Questions: {(analysisData.interview_questions || []).join(" | ") || "None"}</p>
          </div>
        )}

        {mode === "interview" && interviewEval && (
          <div className="result">
            <h2>Interview Score: {interviewEval.score}</h2>
            <p>{interviewEval.feedback}</p>
          </div>
        )}

        {mode === "resume_builder" && resumeDraft && (
          <div className="result">
            <h2>Generated Model Resume</h2>
            {detectedLinks && (
              <p>
                Auto-detected links:{" "}
                {[detectedLinks.linkedin, detectedLinks.github, detectedLinks.portfolio]
                  .filter(Boolean)
                  .join(" | ") || "None found in attached resume"}
              </p>
            )}
            <div className="resume-template">
              <div className="resume-template-header">
                <h3>{resumeDraft.name || "Your Name"}</h3>
                <p>
                  {resumeDraft.email} | {resumeDraft.phone} | {resumeDraft.location}
                </p>
                <p>
                  {isHttpUrl(resumeDraft.linkedin) ? (
                    <a href={resumeDraft.linkedin} target="_blank" rel="noreferrer">
                      LinkedIn
                    </a>
                  ) : (
                    <span>LinkedIn: add URL</span>
                  )}{" "}
                  |{" "}
                  {isHttpUrl(resumeDraft.github) ? (
                    <a href={resumeDraft.github} target="_blank" rel="noreferrer">
                      GitHub
                    </a>
                  ) : (
                    <span>GitHub: add URL</span>
                  )}{" "}
                  |{" "}
                  {isHttpUrl(resumeDraft.portfolio) ? (
                    <a href={resumeDraft.portfolio} target="_blank" rel="noreferrer">
                      Portfolio
                    </a>
                  ) : (
                    <span>Portfolio: add URL</span>
                  )}
                </p>
                <p className="resume-template-headline">{resumeDraft.headline}</p>
              </div>

              <section>
                <h4>Summary</h4>
                <p>{resumeDraft.summary}</p>
              </section>

              <section>
                <h4>Skills</h4>
                {resumeDraft.skills_grouped?.technical?.length > 0 && (
                  <p>
                    <strong>Technical:</strong> {resumeDraft.skills_grouped.technical.join(", ")}
                  </p>
                )}
                {resumeDraft.skills_grouped?.core?.length > 0 && (
                  <p>
                    <strong>Core:</strong> {resumeDraft.skills_grouped.core.join(", ")}
                  </p>
                )}
                {!resumeDraft.skills_grouped?.technical?.length &&
                  !resumeDraft.skills_grouped?.core?.length && (
                    <p>{(resumeDraft.skills || []).join(", ")}</p>
                  )}
              </section>

              <section>
                <h4>Experience</h4>
                {(resumeDraft.experience || []).map((exp, idx) => (
                  <div key={`${exp.role}-${idx}`} className="resume-entry">
                    <p className="resume-entry-title">{exp.role}</p>
                    <p className="resume-entry-meta">
                      {exp.org} | {exp.duration}
                    </p>
                    <ul>
                      {(exp.bullets || []).map((bullet, bIdx) => (
                        <li key={`${bullet}-${bIdx}`}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </section>

              <section>
                <h4>Projects</h4>
                {(resumeDraft.projects || []).map((project, idx) => (
                  <div key={`${project.title}-${idx}`} className="resume-entry">
                    <p className="resume-entry-title">{project.title}</p>
                    <ul>
                      {(project.bullets || []).map((bullet, bIdx) => (
                        <li key={`${bullet}-${bIdx}`}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </section>

              <section>
                <h4>Education</h4>
                {(resumeDraft.education || []).map((edu, idx) => (
                  <div key={`${edu.degree}-${idx}`} className="resume-entry">
                    <p className="resume-entry-title">{edu.degree}</p>
                    <p className="resume-entry-meta">
                      {edu.institute} | {edu.year}
                    </p>
                  </div>
                ))}
              </section>
            </div>

            {resumeIntel?.recruiter_simulation && (
              <div className="intel-panel">
                <h3>Recruiter Simulation</h3>
                <p>
                  Overall: {resumeIntel.recruiter_simulation.overall_score} | Verdict:{" "}
                  {resumeIntel.recruiter_simulation.verdict}
                </p>
                {(resumeIntel.recruiter_simulation.personas || []).map((p, idx) => (
                  <p key={`${p.persona}-${idx}`}>
                    {p.persona}: {p.score} - {p.reason}
                  </p>
                ))}
              </div>
            )}

            {resumeIntel?.bullet_quality && (
              <div className="intel-panel">
                <h3>Bullet Quality Engine</h3>
                <p>Average Score: {resumeIntel.bullet_quality.average_score}</p>
                {(resumeIntel.bullet_quality.bullets || []).slice(0, 6).map((b, idx) => (
                  <p key={`${b.section}-${idx}`}>
                    [{b.rating.toUpperCase()} {b.score}] {b.bullet}
                  </p>
                ))}
              </div>
            )}

            {resumeIntel?.evidence_links && (
              <div className="intel-panel">
                <h3>Evidence-Linked Claims</h3>
                {(resumeIntel.evidence_links || []).slice(0, 6).map((e, idx) => (
                  <p key={`${e.section}-${idx}`}>
                    {e.evidence_type}: {e.claim}{" "}
                    <a href={e.proof_link_placeholder} target="_blank" rel="noreferrer">
                      Proof Link
                    </a>
                  </p>
                ))}
              </div>
            )}

            {resumeIntel?.gap_autopilot && (
              <div className="intel-panel">
                <h3>30/60/90 Gap Autopilot</h3>
                <p>Missing Priorities: {(resumeIntel.gap_autopilot.missing_priorities || []).join(", ")}</p>
                <p>30 Days: {(resumeIntel.gap_autopilot.plan_30_60_90?.["30_days"] || []).join(" | ")}</p>
                <p>60 Days: {(resumeIntel.gap_autopilot.plan_30_60_90?.["60_days"] || []).join(" | ")}</p>
                <p>90 Days: {(resumeIntel.gap_autopilot.plan_30_60_90?.["90_days"] || []).join(" | ")}</p>
              </div>
            )}

            {resumeIntel?.role_variants && (
              <div className="intel-panel">
                <h3>Role Variant Generator</h3>
                {(resumeIntel.role_variants || []).map((v, idx) => (
                  <p key={`${v.variant_name}-${idx}`}>
                    {v.variant_name}: {v.headline} | Focus: {(v.skills_focus || []).join(", ")}
                  </p>
                ))}
              </div>
            )}

            {resumeIntel?.interview_bullets?.length > 0 && (
              <div className="intel-panel">
                <h3>Interview-to-Resume Bullets</h3>
                {(resumeIntel.interview_bullets || []).map((b, idx) => (
                  <p key={`${b}-${idx}`}>{b}</p>
                ))}
              </div>
            )}

            {resumeIntel?.portfolio_consistency && (
              <div className="intel-panel">
                <h3>Portfolio Consistency Checker</h3>
                <p>Consistency Score: {resumeIntel.portfolio_consistency.consistency_score}</p>
                <p>Matched: {(resumeIntel.portfolio_consistency.matched_claims || []).slice(0, 3).join(" | ") || "None"}</p>
                <p>Unverified: {(resumeIntel.portfolio_consistency.unverified_claims || []).slice(0, 3).join(" | ") || "None"}</p>
              </div>
            )}

            {resumeIntel?.benchmark_panel && (
              <div className="intel-panel">
                <h3>Top-Candidate Benchmark</h3>
                <p>
                  Estimated Percentile: {resumeIntel.benchmark_panel.estimated_percentile} | Tier:{" "}
                  {resumeIntel.benchmark_panel.benchmark_tier}
                </p>
                <p>
                  Gaps to Top 10%: {(resumeIntel.benchmark_panel.gaps_to_top_10 || []).join(" | ")}
                </p>
              </div>
            )}
          </div>
        )}

      </div>

      {mode === "resume_builder" && showAuthGate && (
        <div className="auth-overlay">
          <div className="auth-modal">
            <p className="auth-kicker">InternPilot Secure Download</p>
            <h2>Sign In</h2>
            <p>Please login before downloading the resume.</p>
            <div className="auth-methods">
              <button
                className={`attach-btn ${authMethod === "google" ? "auth-method-active" : ""}`}
                onClick={() => setAuthMethod("google")}
              >
                Google
              </button>
              <button
                className={`attach-btn ${authMethod === "otp" ? "auth-method-active" : ""}`}
                onClick={() => setAuthMethod("otp")}
              >
                Email OTP
              </button>
            </div>

            {authMethod === "google" && (
              <>
                {!googleClientId && (
                  <>
                    <p>
                      Missing <code>VITE_GOOGLE_CLIENT_ID</code>. Paste your Google Web Client ID below.
                    </p>
                    <input
                      className="client-id-input"
                      placeholder="Paste Google Web Client ID..."
                      value={googleClientIdInput}
                      onChange={(e) => setGoogleClientIdInput(e.target.value)}
                    />
                    <button
                      className="attach-btn"
                      onClick={() => {
                        const trimmed = googleClientIdInput.trim();
                        if (!trimmed) {
                          setAuthError("Please enter a valid Google Client ID.");
                          return;
                        }
                        localStorage.setItem("internpilot_google_client_id", trimmed);
                        setGoogleClientId(trimmed);
                        setAuthError("");
                      }}
                    >
                      Save Client ID
                    </button>
                  </>
                )}
                <div ref={googleButtonRef} className="google-btn-slot" />
              </>
            )}

            {authMethod === "otp" && (
              <div className="otp-box">
                {smtpStatus && !smtpStatus.configured && (
                  <p>
                    SMTP missing: {(smtpStatus.missing_fields || []).join(", ")}
                  </p>
                )}
                <input
                  className="client-id-input"
                  placeholder="Enter your email"
                  value={otpEmail}
                  onChange={(e) => setOtpEmail(e.target.value)}
                />
                <button className="attach-btn" onClick={requestOtp} disabled={otpLoading}>
                  {otpLoading ? "Requesting..." : "Send OTP"}
                </button>
                {otpRequested && (
                  <>
                    <input
                      className="client-id-input"
                      placeholder="Enter OTP code"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                    />
                    <button className="attach-btn" onClick={verifyOtp} disabled={otpLoading}>
                      {otpLoading ? "Verifying..." : "Verify OTP"}
                    </button>
                  </>
                )}
                {demoOtpCode && (
                  <p>
                    Demo OTP (development mode): <strong>{demoOtpCode}</strong>
                  </p>
                )}
              </div>
            )}

            {authError && <p>{authError}</p>}
            {authMessage && <p>{authMessage}</p>}
            <button
              className="attach-btn"
              onClick={() => {
                setShowAuthGate(false);
                setPendingDownload(false);
                setAuthError("");
                setAuthMessage("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
