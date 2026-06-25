/**
 * HireSense AI — frontend logic.
 * No build step / framework: vanilla JS talking to the Flask JSON API.
 */
(() => {
  "use strict";

  const els = {
    statusDot: document.getElementById("statusDot"),
    statusText: document.getElementById("statusText"),

    form: document.getElementById("matchForm"),
    runBtn: document.getElementById("runBtn"),
    runHint: document.getElementById("runHint"),

    tabs: document.querySelectorAll(".tab"),
    tabPanels: document.querySelectorAll(".tab-panel"),

    resumeDropzone: document.getElementById("resumeDropzone"),
    resumeFile: document.getElementById("resumeFile"),
    resumeFilename: document.getElementById("resumeFilename"),
    resumeText: document.getElementById("resumeText"),

    jobText: document.getElementById("jobText"),
    jobCharCount: document.getElementById("jobCharCount"),

    heroDialFill: document.getElementById("heroDialFill"),
    heroDialNumber: document.getElementById("heroDialNumber"),

    resultsSection: document.getElementById("resultsSection"),
    ringFill: document.getElementById("ringFill"),
    scoreNumber: document.getElementById("scoreNumber"),
    fitCategory: document.getElementById("fitCategory"),
    semanticScore: document.getElementById("semanticScore"),
    skillScore: document.getElementById("skillScore"),
    suggestionSummary: document.getElementById("suggestionSummary"),
    suggestionSource: document.getElementById("suggestionSource"),

    matchedSkillsList: document.getElementById("matchedSkillsList"),
    matchedCount: document.getElementById("matchedCount"),
    matchedEmpty: document.getElementById("matchedEmpty"),

    missingSkillsList: document.getElementById("missingSkillsList"),
    missingCount: document.getElementById("missingCount"),
    missingEmpty: document.getElementById("missingEmpty"),

    keywordsList: document.getElementById("keywordsList"),

    suggestionList: document.getElementById("suggestionList"),
    rewriteExampleWrap: document.getElementById("rewriteExampleWrap"),
    rewriteExample: document.getElementById("rewriteExample"),

    errorBanner: document.getElementById("errorBanner"),
    errorMessage: document.getElementById("errorMessage"),

    findSimilarBtn: document.getElementById("findSimilarBtn"),
    similarList: document.getElementById("similarList"),
  };

  const RING_CIRCUMFERENCE = 553; // 2 * pi * 88, matches SVG r=88
  const HERO_CIRCUMFERENCE = 603; // 2 * pi * 96, matches SVG r=96

  // ---------------------------------------------------------------- status

  async function checkEngineStatus() {
    try {
      const res = await fetch("/api/ready");
      const data = await res.json();
      if (res.ok && data.status === "ready") {
        els.statusDot.classList.add("online");
        els.statusText.textContent = "engine ready";
      } else {
        els.statusDot.classList.add("offline");
        els.statusText.textContent = "engine warming up";
      }
    } catch {
      els.statusDot.classList.add("offline");
      els.statusText.textContent = "engine unreachable";
    }
  }

  // -------------------------------------------------------------------- tabs

  els.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      els.tabs.forEach((t) => {
        t.classList.remove("active");
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");

      const target = tab.dataset.target;
      els.tabPanels.forEach((p) => p.classList.toggle("active", p.id === target));
    });
  });

  // ---------------------------------------------------------------- dropzone

  els.resumeDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    els.resumeDropzone.classList.add("dragover");
  });
  els.resumeDropzone.addEventListener("dragleave", () => {
    els.resumeDropzone.classList.remove("dragover");
  });
  els.resumeDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    els.resumeDropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      els.resumeFile.files = e.dataTransfer.files;
      updateFilename();
    }
  });
  els.resumeFile.addEventListener("change", updateFilename);

  function updateFilename() {
    const file = els.resumeFile.files[0];
    els.resumeFilename.textContent = file ? file.name : "";
  }

  // -------------------------------------------------------------- char count

  els.jobText.addEventListener("input", () => {
    els.jobCharCount.textContent = els.jobText.value.length;
  });

  // ------------------------------------------------------------------ submit

  els.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const activeTab = document.querySelector(".tab.active").dataset.target;
    const hasFile = activeTab === "resume-upload" && els.resumeFile.files.length > 0;
    const hasPastedText = activeTab === "resume-paste" && els.resumeText.value.trim().length > 0;
    const jobValue = els.jobText.value.trim();

    if (!hasFile && !hasPastedText) {
      showError("Add a résumé — either upload a file or paste text — before running a match.");
      return;
    }
    if (jobValue.length < 30) {
      showError("Job description is too short. Paste the full posting for an accurate score.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      if (hasFile) {
        formData.append("resume_file", els.resumeFile.files[0]);
      } else {
        formData.append("resume_text", els.resumeText.value.trim());
      }
      formData.append("job_text", jobValue);

      const res = await fetch("/api/match", { method: "POST", body: formData });
      const data = await res.json();

      if (!res.ok) {
        showError(data.message || "Something went wrong while scoring this match.");
        return;
      }

      renderResults(data);
    } catch (err) {
      showError("Could not reach the matching engine. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    els.runBtn.disabled = isLoading;
    els.runBtn.querySelector(".run-btn-label").textContent = isLoading ? "Scoring…" : "Run match";
    els.runHint.textContent = isLoading
      ? "Embedding résumé and job text, computing overlap…"
      : "Add a résumé and a job description to begin.";
  }

  function showError(message) {
    els.errorMessage.textContent = message;
    els.errorBanner.hidden = false;
    els.errorBanner.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function hideError() {
    els.errorBanner.hidden = true;
  }

  // --------------------------------------------------------------- render

  function renderResults(data) {
    els.resultsSection.hidden = false;

    // Score ring
    const score = clamp(data.match_score, 0, 100);
    const offset = RING_CIRCUMFERENCE - (score / 100) * RING_CIRCUMFERENCE;
    requestAnimationFrame(() => {
      els.ringFill.style.strokeDashoffset = offset;
    });
    els.scoreNumber.textContent = Math.round(score);
    els.ringFill.style.stroke = scoreColor(score);

    // Hero dial mirrors the same score for a persistent ambient readout
    const heroOffset = HERO_CIRCUMFERENCE - (score / 100) * HERO_CIRCUMFERENCE;
    requestAnimationFrame(() => {
      els.heroDialFill.style.strokeDashoffset = heroOffset;
    });
    els.heroDialNumber.textContent = Math.round(score);

    els.fitCategory.textContent = data.job_fit_category || "—";
    els.semanticScore.textContent = `${data.semantic_similarity}%`;
    els.skillScore.textContent = `${data.skill_coverage_pct}%`;

    const sugg = data.suggestions || {};
    els.suggestionSummary.textContent = sugg.summary || "No summary available.";
    els.suggestionSource.textContent =
      sugg.source === "gemini" ? "Generated by Gemini" : "Generated by rule-based engine (no Gemini key configured)";

    renderChipList(els.matchedSkillsList, data.matched_skills, els.matchedEmpty, els.matchedCount);
    renderChipList(els.missingSkillsList, data.missing_skills, els.missingEmpty, els.missingCount);
    renderChipList(els.keywordsList, data.recommended_keywords, null, null);

    els.suggestionList.innerHTML = "";
    (sugg.improvement_suggestions || []).forEach((s) => {
      const li = document.createElement("li");
      li.textContent = s;
      els.suggestionList.appendChild(li);
    });

    if (sugg.rewrite_example) {
      els.rewriteExampleWrap.hidden = false;
      els.rewriteExample.textContent = sugg.rewrite_example;
    } else {
      els.rewriteExampleWrap.hidden = true;
    }

    els.resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderChipList(listEl, items, emptyEl, countEl) {
    listEl.innerHTML = "";
    const safeItems = items || [];
    if (countEl) countEl.textContent = safeItems.length;

    if (safeItems.length === 0) {
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;

    safeItems.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      listEl.appendChild(li);
    });
  }

  function scoreColor(score) {
    if (score >= 70) return "#6fcf97";
    if (score >= 45) return "#ffb13c";
    return "#e8694a";
  }

  function clamp(n, min, max) {
    return Math.min(Math.max(n, min), max);
  }

  // ----------------------------------------------------------- similar search

  els.findSimilarBtn.addEventListener("click", async () => {
    const activeTab = document.querySelector(".tab.active").dataset.target;
    const text =
      activeTab === "resume-upload" ? "" : els.resumeText.value.trim();

    if (!text || text.length < 30) {
      showError("Paste résumé text in the 'Paste text' tab to search the similarity index.");
      return;
    }
    hideError();

    els.findSimilarBtn.disabled = true;
    els.findSimilarBtn.textContent = "Searching…";

    try {
      const res = await fetch("/api/similar-resumes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, top_k: 5 }),
      });
      const data = await res.json();

      if (!res.ok) {
        showError(data.message || "Similarity search failed.");
        return;
      }

      els.similarList.innerHTML = "";
      (data.results || []).forEach((r) => {
        const li = document.createElement("li");
        const score = document.createElement("span");
        score.className = "similar-score";
        score.textContent = r.similarity_score.toFixed(3);
        const category = document.createElement("span");
        category.className = "similar-category";
        category.textContent = r.category;
        const snippet = document.createElement("span");
        snippet.className = "similar-snippet";
        snippet.textContent = r.snippet;
        li.append(score, category, snippet);
        els.similarList.appendChild(li);
      });
    } catch {
      showError("Could not reach the similarity search endpoint.");
    } finally {
      els.findSimilarBtn.disabled = false;
      els.findSimilarBtn.textContent = "Search with current résumé text";
    }
  });

  // ------------------------------------------------------------------- init

  checkEngineStatus();
})();
