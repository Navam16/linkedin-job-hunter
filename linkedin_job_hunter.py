import streamlit as st
import requests
import re
import json
import time
from datetime import datetime
import pandas as pd
from io import BytesIO
from groq import Groq

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Candidate Hunter",
    page_icon="🔭",
    layout="wide",
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Syne:wght@400;500;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
.main { background: #080b12; }

h1, h2, h3 { font-family: 'IBM Plex Mono', monospace !important; }

.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(120deg, #f97316, #fb923c, #fbbf24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -1px;
}
.hero-sub { color: #64748b; font-size: 0.95rem; margin-bottom: 2rem; }

.card {
    background: #0f1623;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: #f97316; }

.skill-badge {
    display: inline-block;
    background: #1e293b;
    color: #f97316;
    border: 1px solid #f97316;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    padding: 2px 9px;
    border-radius: 4px;
    margin: 2px;
}
.exp-badge {
    display: inline-block;
    background: linear-gradient(120deg, #f97316, #fbbf24);
    color: #080b12;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 4px;
    margin: 2px;
}
.candidate-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.05rem;
    color: #f1f5f9;
    font-weight: 700;
}
.role-text { color: #94a3b8; font-size: 0.85rem; }
.meta-text { color: #64748b; font-size: 0.8rem; }

.stat-box {
    background: #0f1623;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.stat-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(120deg, #f97316, #fbbf24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label { color: #64748b; font-size: 0.78rem; }

.stButton > button {
    background: linear-gradient(120deg, #f97316, #fbbf24) !important;
    color: #080b12 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.5px !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; }

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextArea > div > div > textarea {
    background: #0f1623 !important;
    border: 1px solid #1e293b !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
}
.stSlider > div { color: #f97316; }

div[data-testid="stExpander"] {
    background: #0f1623;
    border: 1px solid #1e293b;
    border-radius: 10px;
}

.log-line {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.73rem;
    color: #f97316;
    padding: 1px 0;
}
.warn-line {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.73rem;
    color: #fbbf24;
}
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.3rem;
}
.mode-pill {
    display: inline-block;
    background: #1e293b;
    color: #94a3b8;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    padding: 2px 10px;
    border-radius: 20px;
    margin-right: 4px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">🔭 LinkedIn Candidate Hunter</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Search LinkedIn public profiles to find potential candidates for hiring · '
    'Powered by Google CSE + Groq AI</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    google_api_key = st.text_input("Google Custom Search API Key", type="password", placeholder="AIza...")
    search_engine_id = st.text_input("Search Engine ID (cx)", placeholder="a1b2c3d4e...")
    groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown("---")
    st.markdown("### ⚙️ Search Settings")
    max_results = st.slider("Results per search query", 5, 10, 10)
    delay_between = st.slider("Delay between calls (sec)", 0.3, 2.0, 0.5, step=0.1)

    st.markdown("---")
    st.markdown("### 📖 Setup Guide")
    with st.expander("How to get API keys"):
        st.markdown("""
**Google Custom Search API Key:**
1. Go to `console.cloud.google.com`
2. Enable **Custom Search API**
3. Credentials → Create API Key

**Search Engine ID (cx):**
1. Go to `programmablesearchengine.google.com`
2. Create engine → set site to `linkedin.com`
3. Turn ON **"Search the entire web"**
4. Copy the `cx` ID

**Groq Key:**
1. Go to `console.groq.com`
2. API Keys → Create
3. Free tier: ~14,400 req/day

**Important:** Your CSE must have
`linkedin.com` as a primary site
to rank LinkedIn profiles higher.
        """)

    with st.expander("⚠️ LinkedIn Limitations"):
        st.markdown("""
LinkedIn blocks direct scraping.
This tool uses **Google's index** of
LinkedIn public profiles, extracting
info from search snippets + cached pages.

Results depend on what Google has indexed.
Active/open-to-work profiles appear more.
        """)

# ─────────────────────────────────────────────
# SEARCH CONFIGURATION — TWO MODES
# ─────────────────────────────────────────────
st.markdown("### 🎯 What are you hiring for?")

search_mode = st.radio(
    "Search mode",
    ["🧩 Role + Skills Builder", "✏️ Custom Query"],
    horizontal=True,
    help="Use the builder for guided search, or write your own raw query."
)

# ── MODE 1: Role + Skills Builder ──
if search_mode == "🧩 Role + Skills Builder":
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-label">Job Role / Title</div>', unsafe_allow_html=True)

        role_category = st.selectbox(
            "Role category",
            [
                "Technology & Engineering",
                "Data & Analytics",
                "Product & Design",
                "Marketing & Growth",
                "Finance & Accounting",
                "Sales & Business Development",
                "Operations & Supply Chain",
                "HR & Talent",
                "Legal & Compliance",
                "Healthcare & Life Sciences",
                "Custom / Other",
            ]
        )

        ROLE_PRESETS = {
            "Technology & Engineering": [
                "Software Engineer", "Backend Engineer", "Frontend Engineer",
                "Full Stack Developer", "DevOps Engineer", "Cloud Architect",
                "Site Reliability Engineer", "Mobile Developer", "QA Engineer",
                "Embedded Systems Engineer", "Cybersecurity Analyst",
            ],
            "Data & Analytics": [
                "Data Scientist", "Data Analyst", "ML Engineer", "AI Engineer",
                "Data Engineer", "Analytics Engineer", "BI Developer",
                "Research Scientist", "NLP Engineer", "Computer Vision Engineer",
            ],
            "Product & Design": [
                "Product Manager", "Senior Product Manager", "UX Designer",
                "UI Designer", "Product Designer", "UX Researcher",
                "Growth Product Manager", "Technical Product Manager",
            ],
            "Marketing & Growth": [
                "Digital Marketing Manager", "SEO Specialist", "Content Strategist",
                "Performance Marketer", "Brand Manager", "Social Media Manager",
                "Growth Hacker", "CRM Manager",
            ],
            "Finance & Accounting": [
                "Financial Analyst", "FP&A Manager", "Investment Analyst",
                "Chartered Accountant", "Controller", "CFO",
                "Equity Research Analyst", "Risk Manager",
            ],
            "Sales & Business Development": [
                "Sales Manager", "Business Development Manager", "Account Executive",
                "Inside Sales Representative", "Enterprise Sales", "SDR",
            ],
            "Operations & Supply Chain": [
                "Operations Manager", "Supply Chain Analyst", "Logistics Manager",
                "Procurement Manager", "Project Manager", "Program Manager",
            ],
            "HR & Talent": [
                "HR Manager", "Talent Acquisition Specialist", "HRBP",
                "Recruiter", "L&D Manager", "Compensation & Benefits Analyst",
            ],
            "Legal & Compliance": [
                "Corporate Lawyer", "Compliance Officer", "Legal Counsel",
                "Contract Manager", "IP Attorney",
            ],
            "Healthcare & Life Sciences": [
                "Clinical Research Associate", "Biostatistician", "Regulatory Affairs",
                "Medical Affairs Manager", "Pharmacovigilance Specialist",
            ],
            "Custom / Other": [],
        }

        presets = ROLE_PRESETS.get(role_category, [])
        if presets:
            selected_role = st.selectbox("Select role", [""] + presets)
        else:
            selected_role = ""

        custom_role = st.text_input(
            "Or type custom role title",
            placeholder="e.g. Quant Researcher, AI Product Lead"
        )
        final_role = custom_role.strip() if custom_role.strip() else selected_role

        st.markdown('<div class="section-label" style="margin-top:1rem">Experience Level</div>', unsafe_allow_html=True)
        exp_level = st.multiselect(
            "Experience required",
            ["Fresher / 0-1 yr", "Junior / 1-3 yrs", "Mid-level / 3-6 yrs",
             "Senior / 6-10 yrs", "Lead / Principal", "Manager / Director", "VP / C-Suite"],
            default=["Mid-level / 3-6 yrs", "Senior / 6-10 yrs"]
        )

    with col2:
        st.markdown('<div class="section-label">Must-Have Skills</div>', unsafe_allow_html=True)
        must_skills = st.text_input(
            "Required skills (comma-separated)",
            placeholder='e.g. Python, SQL, Machine Learning'
        )
        nice_skills = st.text_input(
            "Nice-to-have skills",
            placeholder='e.g. Spark, Airflow, AWS'
        )

        st.markdown('<div class="section-label" style="margin-top:1rem">Location & Work Mode</div>', unsafe_allow_html=True)

        location_type = st.selectbox(
            "Target location",
            ["India (any city)", "Bangalore", "Mumbai", "Delhi / NCR", "Hyderabad",
             "Pune", "Chennai", "Remote / WFH", "Global / Any", "Custom city"]
        )
        if location_type == "Custom city":
            location_type = st.text_input("Enter city/region", placeholder="e.g. Ahmedabad")

        open_to_work = st.checkbox("Prioritise 'Open to Work' profiles", value=True)
        recent_activity = st.checkbox("Filter recently active profiles", value=False)

        st.markdown('<div class="section-label" style="margin-top:1rem">Education / Certifications</div>', unsafe_allow_html=True)
        education_filter = st.text_input(
            "Degree / certification keywords (optional)",
            placeholder='e.g. IIT, MBA, PhD, AWS Certified'
        )

# ── MODE 2: Custom Raw Query ──
else:
    st.markdown("""
<div class="card" style="margin-bottom:1rem">
<div class="section-label">Custom Google Site Search Query</div>
<div class="meta-text" style="margin-top:0.4rem">
Write a raw query — the tool will prepend <code>site:linkedin.com/in</code> automatically.<br>
Example: <code>"data scientist" "Python" "Bangalore" "open to work"</code>
</div>
</div>
""", unsafe_allow_html=True)
    custom_query_raw = st.text_area(
        "Your search query",
        placeholder='"senior data scientist" "pytorch" OR "tensorflow" "Bangalore" OR "remote"',
        height=100,
    )
    num_custom_queries = st.number_input("How many query variations to run", 1, 5, 1)
    final_role = "Custom Search"

# ─────────────────────────────────────────────
# REGEX
# ─────────────────────────────────────────────
EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'

# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

def build_candidate_queries(role, must_skills, nice_skills, exp_level,
                             location, open_to_work, education_filter):
    """
    Build multiple Google search query strings targeting LinkedIn /in/ profiles.
    Strategy: generate query variations to widen recall.
    """
    queries = []

    # Parse skill lists
    must_list = [s.strip() for s in must_skills.split(",") if s.strip()] if must_skills else []
    nice_list = [s.strip() for s in nice_skills.split(",") if s.strip()] if nice_skills else []

    # Experience keyword mapping
    EXP_MAP = {
        "Fresher / 0-1 yr":       ["fresher", "graduate", "0-1 year"],
        "Junior / 1-3 yrs":       ["1-3 years experience", "junior"],
        "Mid-level / 3-6 yrs":    ["3-5 years experience", "mid-level"],
        "Senior / 6-10 yrs":      ["senior", "6+ years"],
        "Lead / Principal":        ["lead", "principal", "staff"],
        "Manager / Director":      ["manager", "director"],
        "VP / C-Suite":            ["VP", "Vice President", "CXO"],
    }

    # Location handling
    loc_map = {
        "India (any city)": "India",
        "Bangalore": "Bangalore",
        "Mumbai": "Mumbai",
        "Delhi / NCR": "Delhi",
        "Hyderabad": "Hyderabad",
        "Pune": "Pune",
        "Chennai": "Chennai",
        "Remote / WFH": "remote",
        "Global / Any": "",
    }
    loc_str = loc_map.get(location, location)

    # Build skill string
    skill_parts = []
    if must_list:
        # Top 3 must-have skills joined with AND logic
        skill_parts.append(" ".join(f'"{s}"' for s in must_list[:3]))
    if nice_list:
        nice_or = " OR ".join(f'"{s}"' for s in nice_list[:2])
        skill_parts.append(f"({nice_or})")

    skill_str = " ".join(skill_parts)

    # Open to work signal
    otw = '"open to work" OR "#opentowork"' if open_to_work else ""

    # Education
    edu_str = f'"{education_filter}"' if education_filter.strip() else ""

    # Base profile query (targets /in/ pages — actual profiles)
    base = f'site:linkedin.com/in "{role}"'

    # Query 1: Role + skills + location
    q1_parts = [base, skill_str]
    if loc_str:
        q1_parts.append(f'"{loc_str}"')
    if otw:
        q1_parts.append(otw)
    queries.append({"label": f"{role} + skills", "query": " ".join(p for p in q1_parts if p)})

    # Query 2: Experience-specific queries
    for exp in exp_level[:2]:  # limit to 2 exp levels
        exp_kws = EXP_MAP.get(exp, [])
        if exp_kws:
            exp_or = " OR ".join(f'"{e}"' for e in exp_kws[:2])
            q2 = f'{base} ({exp_or})'
            if loc_str:
                q2 += f' "{loc_str}"'
            if skill_str:
                q2 += f' {skill_str}'
            queries.append({"label": f"{role} + {exp}", "query": q2})

    # Query 3: Education filter variant
    if edu_str:
        q3 = f'{base} {edu_str}'
        if loc_str:
            q3 += f' "{loc_str}"'
        if skill_str:
            q3 += f' {skill_str}'
        queries.append({"label": f"{role} + {education_filter}", "query": q3})

    # Query 4: Headline-style search (people whose headline contains role + skill)
    if must_list:
        top_skill = must_list[0]
        q4 = f'site:linkedin.com/in "{role}" "{top_skill}"'
        if loc_str:
            q4 += f' "{loc_str}"'
        queries.append({"label": f"{role} headline search", "query": q4})

    return queries


def google_search(query: str, api_key: str, cx: str, num: int = 10):
    """Call Google Custom Search API."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num, 10),
    }
    try:
        resp = requests.get(url, params=params, timeout=12)
        data = resp.json()
        if "error" in data:
            msg = data["error"].get("message", "Unknown error")
            code = data["error"].get("code", 0)
            return [], f"API Error {code}: {msg}"
        return data.get("items", []), None
    except Exception as e:
        return [], str(e)


def fetch_page_text(url: str) -> str:
    """
    Try to fetch readable text from a LinkedIn profile URL.
    Strategy: use Bing cache or Google cache as LinkedIn blocks direct scraping.
    Returns stripped text or empty string.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Strategy 1: Google cache
    for cache_fmt in [
        f"https://webcache.googleusercontent.com/search?q=cache:{url}&hl=en",
    ]:
        try:
            r = requests.get(cache_fmt, headers=headers, timeout=8)
            if r.status_code == 200 and "linkedin" in r.text.lower():
                text = re.sub(r'<[^>]+>', ' ', r.text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 200:
                    return text[:4000]
        except Exception:
            pass

    return ""


def extract_candidate_with_ai(groq_key: str, snippet: str, url: str, role: str) -> dict | None:
    """
    Use Groq LLM to extract structured candidate profile data.
    The prompt is specifically tuned for candidate hunting (not job postings).
    """
    client = Groq(api_key=groq_key)

    prompt = f"""You are an expert recruiter AI. Extract structured candidate profile information
from the following LinkedIn profile text/snippet. This is for hiring purposes.

PROFILE TEXT / SNIPPET:
{snippet}

PROFILE URL: {url}
ROLE BEING SEARCHED: {role}

Extract the following fields. If a field cannot be determined, write "N/A".
Return ONLY valid JSON, no markdown, no explanation:

{{
  "full_name": "candidate's full name",
  "current_title": "current job title / designation",
  "current_company": "current employer",
  "location": "city, country",
  "years_experience": "estimated total years of experience (e.g. '5 years' or '3-5 years')",
  "education": "highest degree and institution (e.g. 'B.Tech IIT Delhi', 'MBA IIM Calcutta')",
  "key_skills": "comma-separated list of top skills visible in profile",
  "open_to_work": "Yes / No / Unknown",
  "profile_summary": "1-2 sentence summary of the candidate's background and strengths",
  "fit_score": "1-10 score for relevance to the role '{role}' based on available info",
  "fit_reason": "one line explaining fit score"
}}

Rules:
- full_name: derive from the URL slug or text (e.g. john-doe → John Doe)
- key_skills: list the most relevant technical or domain skills mentioned
- fit_score must be an integer between 1 and 10
- Do NOT hallucinate details not present in the text; use "N/A" when unsure
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'```$', '', raw).strip()
        data = json.loads(raw)
        data["profile_url"] = url
        data["searched_role"] = role
        data["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Sanitise fit_score to int
        try:
            data["fit_score"] = int(str(data.get("fit_score", 5)).strip())
        except Exception:
            data["fit_score"] = 5

        return data
    except Exception:
        return None


def results_to_excel(results: list) -> BytesIO:
    df = pd.DataFrame(results)
    cols = [
        "full_name", "current_title", "current_company", "location",
        "years_experience", "education", "key_skills", "open_to_work",
        "fit_score", "fit_reason", "profile_summary",
        "searched_role", "profile_url", "extracted_at"
    ]
    df = df[[c for c in cols if c in df.columns]]
    df.columns = [c.replace("_", " ").title() for c in df.columns]

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Candidates")
        ws = writer.sheets["Candidates"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 55)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "candidates" not in st.session_state:
    st.session_state.candidates = []

# ─────────────────────────────────────────────
# RUN / CLEAR BUTTONS
# ─────────────────────────────────────────────
st.markdown("---")
col_run, col_clear, _ = st.columns([1, 1, 4])
with col_run:
    run_btn = st.button("🔭 Hunt Candidates", use_container_width=True)
with col_clear:
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.candidates = []
        st.rerun()

# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────
if run_btn:
    # ── Validate ──
    if not google_api_key or not search_engine_id:
        st.error("⚠️ Please enter your Google API Key and Search Engine ID in the sidebar.")
        st.stop()
    if not groq_api_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar.")
        st.stop()

    # ── Build queries ──
    if search_mode == "✏️ Custom Query":
        if not custom_query_raw.strip():
            st.error("⚠️ Please enter a custom query.")
            st.stop()
        all_queries = [
            {"label": f"Custom query {i+1}", "query": f"site:linkedin.com/in {custom_query_raw.strip()}"}
            for i in range(int(num_custom_queries))
        ]
        search_role = "Custom Search"
    else:
        if not final_role:
            st.error("⚠️ Please select or type a role to search for.")
            st.stop()
        all_queries = build_candidate_queries(
            role=final_role,
            must_skills=must_skills if 'must_skills' in dir() else "",
            nice_skills=nice_skills if 'nice_skills' in dir() else "",
            exp_level=exp_level if 'exp_level' in dir() else [],
            location=location_type if 'location_type' in dir() else "India (any city)",
            open_to_work=open_to_work if 'open_to_work' in dir() else False,
            education_filter=education_filter if 'education_filter' in dir() else "",
        )
        search_role = final_role

    st.session_state.candidates = []

    progress_bar = st.progress(0)
    log_box = st.empty()
    logs = []

    def refresh_logs():
        log_box.markdown(
            "\n".join([
                f'<div class="{"warn-line" if "⚠️" in l or "❌" in l else "log-line"}">{l}</div>'
                for l in logs[-10:]
            ]),
            unsafe_allow_html=True,
        )

    all_profile_urls = set()
    all_items = []

    # ── Step 1: Google Search ──
    for i, q in enumerate(all_queries):
        logs.append(f"🔍 Query [{i+1}/{len(all_queries)}]: {q['label']}")
        refresh_logs()

        items, err = google_search(q["query"], google_api_key, search_engine_id, max_results)

        if err:
            logs.append(f"⚠️ Error: {err}")
        else:
            # Filter to only linkedin.com/in/ profile pages
            profile_items = [
                item for item in items
                if "/in/" in item.get("link", "") and item.get("link", "") not in all_profile_urls
            ]
            for item in profile_items:
                all_profile_urls.add(item["link"])
                all_items.append({"label": q["label"], "item": item})
            logs.append(f"   ✅ {len(profile_items)} new profiles found (total: {len(all_items)})")

        refresh_logs()
        progress_bar.progress((i + 1) / len(all_queries) * 0.35)
        time.sleep(delay_between)

    logs.append(f"📦 Total unique profiles to analyze: {len(all_items)}")
    refresh_logs()

    if not all_items:
        st.warning("No LinkedIn profiles found. Try broadening your query or check your API keys / CSE setup.")
        st.stop()

    # ── Step 2: AI Extraction per profile ──
    for j, entry in enumerate(all_items):
        item = entry["item"]
        url = item.get("link", "")
        # snippet from Google search result = most reliable public data
        snippet = item.get("title", "") + "\n" + item.get("snippet", "")

        logs.append(f"🤖 Extracting profile [{j+1}/{len(all_items)}]: {url.split('linkedin.com/in/')[-1][:40]}...")
        refresh_logs()

        # Try to get more text from cache
        full_text = fetch_page_text(url)
        combined_text = (full_text if len(full_text) > len(snippet) else snippet)[:4000]

        candidate = extract_candidate_with_ai(groq_api_key, combined_text, url, search_role)

        if candidate:
            # Derive name from URL slug as fallback
            if candidate.get("full_name", "N/A") == "N/A":
                slug = url.rstrip("/").split("/in/")[-1].split("?")[0]
                candidate["full_name"] = slug.replace("-", " ").title()

            st.session_state.candidates.append(candidate)
            score = candidate.get("fit_score", "?")
            logs.append(f"   ✅ {candidate.get('full_name','?')} | Score: {score}/10 | {candidate.get('current_title','?')}")
        else:
            logs.append(f"   ⚠️ Could not extract: {url[:50]}")

        refresh_logs()
        progress_bar.progress(0.35 + (j + 1) / len(all_items) * 0.65)
        time.sleep(delay_between * 0.5)

    progress_bar.progress(1.0)
    logs.append(f"🎉 Done! {len(st.session_state.candidates)} candidates extracted.")
    refresh_logs()


# ─────────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────────
if st.session_state.candidates:
    results = st.session_state.candidates

    st.markdown("---")
    st.markdown("### 📊 Results Overview")

    c1, c2, c3, c4 = st.columns(4)
    otw_count = sum(1 for r in results if str(r.get("open_to_work", "")).lower() == "yes")
    avg_score = round(sum(r.get("fit_score", 0) for r in results) / len(results), 1)
    companies = list(set(r.get("current_company", "") for r in results if r.get("current_company", "N/A") != "N/A"))

    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(results)}</div><div class="stat-label">Profiles Found</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{otw_count}</div><div class="stat-label">Open to Work</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{avg_score}</div><div class="stat-label">Avg Fit Score</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(companies)}</div><div class="stat-label">Companies</div></div>', unsafe_allow_html=True)

    # ── Filters ──
    st.markdown("### 🎯 Candidate Profiles")
    f1, f2, f3 = st.columns(3)

    with f1:
        min_score = st.slider("Minimum fit score", 1, 10, 5)
    with f2:
        filter_otw = st.checkbox("Show only 'Open to Work'", value=False)
    with f3:
        sort_by = st.selectbox("Sort by", ["Fit Score (High → Low)", "Fit Score (Low → High)", "Name A-Z"])

    filtered = [r for r in results if r.get("fit_score", 0) >= min_score]
    if filter_otw:
        filtered = [r for r in filtered if str(r.get("open_to_work", "")).lower() == "yes"]

    if sort_by == "Fit Score (High → Low)":
        filtered = sorted(filtered, key=lambda x: x.get("fit_score", 0), reverse=True)
    elif sort_by == "Fit Score (Low → High)":
        filtered = sorted(filtered, key=lambda x: x.get("fit_score", 0))
    else:
        filtered = sorted(filtered, key=lambda x: x.get("full_name", ""))

    st.markdown(f"**Showing {len(filtered)} candidates**")

    for r in filtered:
        score = r.get("fit_score", 5)
        score_color = "#22c55e" if score >= 8 else "#f97316" if score >= 6 else "#64748b"
        otw_badge = '&nbsp;<span style="background:#16a34a;color:#fff;font-size:0.68rem;padding:2px 8px;border-radius:4px;font-family:IBM Plex Mono,monospace;">OPEN TO WORK</span>' if str(r.get("open_to_work", "")).lower() == "yes" else ""
        skills_html = "".join(
            f'<span class="skill-badge">{s.strip()}</span>'
            for s in r.get("key_skills", "").split(",")[:8]
            if s.strip() and s.strip() != "N/A"
        )

        st.markdown(f"""
<div class="card">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <span class="candidate-name">{r.get('full_name', 'Unknown')}</span>
      {otw_badge}
      <br/>
      <span class="role-text">{r.get('current_title', 'N/A')} &nbsp;·&nbsp; {r.get('current_company', 'N/A')}</span>
    </div>
    <div style="text-align:right; flex-shrink:0; margin-left:1rem;">
      <div style="font-family:'IBM Plex Mono',monospace; font-size:1.6rem; font-weight:700; color:{score_color};">{score}<span style="font-size:0.9rem; color:#475569;">/10</span></div>
      <div style="font-size:0.68rem; color:#475569; font-family:'IBM Plex Mono',monospace;">FIT SCORE</div>
    </div>
  </div>

  <div style="margin: 0.6rem 0; display:flex; gap:1.5rem; flex-wrap:wrap;">
    <span class="meta-text">📍 {r.get('location', 'N/A')}</span>
    <span class="meta-text">💼 {r.get('years_experience', 'N/A')}</span>
    <span class="meta-text">🎓 {r.get('education', 'N/A')}</span>
  </div>

  <div style="margin: 0.4rem 0;">{skills_html}</div>

  <div style="margin: 0.6rem 0; color:#94a3b8; font-size:0.83rem;">{r.get('profile_summary', '')}</div>

  <div style="margin: 0.4rem 0; color:#64748b; font-size:0.78rem; font-style:italic;">
    💡 {r.get('fit_reason', '')}
  </div>

  <div style="margin-top: 0.7rem; font-size:0.72rem;">
    <a href="{r.get('profile_url', '#')}" target="_blank"
       style="color:#f97316; font-family:'IBM Plex Mono',monospace; text-decoration:none;">
       🔗 View LinkedIn Profile ↗
    </a>
    &nbsp;·&nbsp;
    <span class="meta-text">Extracted: {r.get('extracted_at', '')}</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Export ──
    st.markdown("---")
    st.markdown("### 📥 Export Candidates")
    ex1, ex2 = st.columns(2)

    with ex1:
        excel_buf = results_to_excel(filtered)
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_buf,
            file_name=f"candidates_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with ex2:
        csv_data = pd.DataFrame(filtered).to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"candidates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    st.markdown("""
<div class="card" style="text-align:center; padding:2.5rem;">
  <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔭</div>
  <div style="font-family:'IBM Plex Mono',monospace; color:#f97316; font-size:1rem;">Ready to Hunt</div>
  <div style="color:#64748b; font-size:0.85rem; margin-top:0.4rem;">
    Configure your search above, add API keys in the sidebar, and click <b>Hunt Candidates</b>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#334155; font-size:0.73rem; font-family:'IBM Plex Mono',monospace;">
  LinkedIn Candidate Hunter · Built with Streamlit + Groq + Google CSE
  · Results depend on Google's public index of LinkedIn profiles
</div>
""", unsafe_allow_html=True)
