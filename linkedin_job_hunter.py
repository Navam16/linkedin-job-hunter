import streamlit as st
import requests
import re
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from groq import Groq

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Job Hunter",
    page_icon="🎯",
    layout="wide",
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.main { background: #0a0a0f; }

h1, h2, h3 {
    font-family: 'Space Mono', monospace !important;
}

.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00f5a0, #00d9f5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}

.hero-sub {
    color: #8888aa;
    font-size: 1rem;
    font-family: 'DM Sans', sans-serif;
    margin-bottom: 2rem;
}

.card {
    background: #13131f;
    border: 1px solid #1e1e30;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

.email-badge {
    display: inline-block;
    background: linear-gradient(135deg, #00f5a0, #00d9f5);
    color: #0a0a0f;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px;
}

.role-badge {
    display: inline-block;
    background: #1e1e35;
    color: #00d9f5;
    border: 1px solid #00d9f5;
    font-size: 0.75rem;
    padding: 2px 9px;
    border-radius: 20px;
    margin: 2px;
}

.company-name {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    color: #ffffff;
    font-weight: 700;
}

.meta-text {
    color: #8888aa;
    font-size: 0.82rem;
}

.stat-box {
    background: #13131f;
    border: 1px solid #1e1e30;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}

.stat-num {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00f5a0, #00d9f5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-label {
    color: #8888aa;
    font-size: 0.8rem;
}

.stButton > button {
    background: linear-gradient(135deg, #00f5a0, #00d9f5) !important;
    color: #0a0a0f !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important;
    font-size: 0.9rem !important;
}

.stButton > button:hover {
    opacity: 0.85 !important;
    transform: translateY(-1px) !important;
}

.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #13131f !important;
    border: 1px solid #1e1e30 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

div[data-testid="stExpander"] {
    background: #13131f;
    border: 1px solid #1e1e30;
    border-radius: 10px;
}

.log-line {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #00f5a0;
    padding: 2px 0;
}

.warn-line {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #f5a000;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">🎯 LinkedIn Job Hunter</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Find hiring posts with email IDs · MBA Data Science & AI · Last 48 hrs</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — API KEYS & CONFIG
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    google_api_key = st.text_input("Google Custom Search API Key", type="password", placeholder="AIza...")
    search_engine_id = st.text_input("Search Engine ID (cx)", placeholder="a1b2c3d4e...")
    groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown("---")
    st.markdown("### ⚙️ Search Settings")
    hours_back = st.slider("Search posts from last N hours", 12, 72, 48)
    max_results = st.slider("Max results per keyword", 5, 20, 10)

    st.markdown("---")
    st.markdown("### 📖 Setup Guide")
    with st.expander("How to get keys"):
        st.markdown("""
**Google API Key:**
1. console.cloud.google.com
2. Enable "Custom Search API"
3. Credentials → Create API Key

**Search Engine ID:**
1. programmablesearchengine.google.com
2. Create engine → site: linkedin.com
3. Enable "Search entire web"

**Groq Key:**
1. console.groq.com
2. API Keys → Create
3. Free tier: 14,400 req/day
        """)

# ─────────────────────────────────────────────
# ROLE KEYWORDS INPUT
# ─────────────────────────────────────────────
st.markdown("### 🔍 Target Roles")
col1, col2 = st.columns([2, 1])

with col1:
    preset_roles = st.multiselect(
        "Quick select roles",
        ["Data Analyst", "Business Analyst", "Product Manager", "Data Scientist",
         "AI/ML Engineer", "Analytics Manager", "Strategy Analyst", "Growth Analyst"],
        default=["Data Analyst", "Business Analyst", "Product Manager"]
    )
    custom_roles = st.text_input("Add custom keywords (comma separated)", placeholder="e.g. Quant Analyst, AI Product Manager")

with col2:
    st.markdown("**Search Mode**")
    include_fresher = st.checkbox("Include fresher/entry level", value=True)
    include_remote = st.checkbox("Include remote roles", value=True)
    india_only = st.checkbox("India only", value=True)

# Build final keyword list
all_roles = list(preset_roles)
if custom_roles.strip():
    all_roles += [r.strip() for r in custom_roles.split(",") if r.strip()]

# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

EMAIL_REGEX = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'

def build_queries(roles, hours_back, include_fresher, include_remote, india_only):
    """Build Google search queries for each role."""
    queries = []
    date_cutoff = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%d")

    modifiers = []
    if include_fresher:
        modifiers.append('"fresher" OR "entry level" OR "0-2 years"')
    if include_remote:
        modifiers.append('"remote" OR "WFH"')
    if india_only:
        modifiers.append('"India"')

    for role in roles:
        base = f'site:linkedin.com/posts "{role}" "hiring" ("email" OR "send resume" OR "apply") after:{date_cutoff}'
        if modifiers:
            base += " " + modifiers[0]  # add first modifier to keep query focused
        queries.append({"role": role, "query": base})
    return queries


def google_search(query, api_key, cx, num=10):
    """Call Google Custom Search API."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num, 10),
        "dateRestrict": "d2",  # last 2 days
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "items" not in data:
            return [], data.get("error", {}).get("message", "No results")
        return data["items"], None
    except Exception as e:
        return [], str(e)


def fetch_page_text(url):
    """Fetch readable text from a URL via Google cache or direct."""
    # Try Google cache first (avoids LinkedIn login wall)
    cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(cache_url, headers=headers, timeout=8)
        if r.status_code == 200:
            # Strip HTML tags roughly
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:3000]  # limit to 3k chars
    except:
        pass
    # Fallback: use snippet from search result
    return ""


def extract_with_ai(groq_key, snippet, url, role):
    """Use Groq LLM to extract structured info from post text."""
    client = Groq(api_key=groq_key)

    prompt = f"""You are extracting job posting information from LinkedIn post text.

POST TEXT:
{snippet}

SOURCE URL: {url}
TARGET ROLE: {role}

Extract the following. If a field is not found, write "N/A".
Return ONLY valid JSON, no explanation:

{{
  "name": "poster's full name",
  "designation": "poster's job title",
  "company": "company name hiring for",
  "role_hiring": "exact role they are hiring for",
  "email": "email address mentioned (comma separated if multiple)",
  "location": "job location if mentioned",
  "experience": "experience required if mentioned",
  "post_summary": "one line summary of what they need"
}}

Rules:
- email must be a real email pattern like abc@company.com
- If no email found, set email to "N/A"
- company should be the hiring company, not the poster's employer if different
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        # Clean JSON
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'```$', '', raw).strip()
        data = json.loads(raw)
        data["source_url"] = url
        data["searched_role"] = role
        data["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return data
    except Exception as e:
        return None


def results_to_excel(results):
    """Convert results list to Excel bytes."""
    df = pd.DataFrame(results)
    # Reorder columns
    cols = ["name", "designation", "company", "role_hiring", "email",
            "location", "experience", "post_summary", "searched_role",
            "source_url", "extracted_at"]
    df = df[[c for c in cols if c in df.columns]]
    df.columns = [c.replace("_", " ").title() for c in df.columns]

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Job Leads")
        ws = writer.sheets["Job Leads"]
        # Auto-fit columns
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 50)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "running" not in st.session_state:
    st.session_state.running = False

# ─────────────────────────────────────────────
# RUN BUTTON
# ─────────────────────────────────────────────
st.markdown("---")
col_run, col_clear = st.columns([1, 5])
with col_run:
    run_btn = st.button("🚀 Start Hunt", use_container_width=True)
with col_clear:
    if st.button("🗑️ Clear Results"):
        st.session_state.results = []
        st.rerun()

# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────
if run_btn:
    # Validate
    if not google_api_key or not search_engine_id:
        st.error("⚠️ Please enter your Google API Key and Search Engine ID in the sidebar.")
        st.stop()
    if not groq_api_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar.")
        st.stop()
    if not all_roles:
        st.error("⚠️ Please select at least one role to search for.")
        st.stop()

    st.session_state.results = []
    queries = build_queries(all_roles, hours_back, include_fresher, include_remote, india_only)

    progress_bar = st.progress(0)
    log_box = st.empty()
    logs = []

    all_items = []

    for i, q in enumerate(queries):
        logs.append(f"🔍 Searching: {q['role']}...")
        log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)

        items, err = google_search(q["query"], google_api_key, search_engine_id, max_results)
        if err:
            logs.append(f"⚠️ {q['role']}: {err}")
            log_box.markdown("\n".join([f'<div class="warn-line">{l}</div>' if "⚠️" in l else f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)
        else:
            logs.append(f"   ✅ {len(items)} posts found for {q['role']}")
            for item in items:
                all_items.append({"role": q["role"], "item": item})

        progress_bar.progress((i + 1) / len(queries) * 0.4)
        time.sleep(0.3)  # rate limit respect

    logs.append(f"📦 Total posts to analyze: {len(all_items)}")
    log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)

    # Filter: only posts that have email-like patterns in snippet
    email_items = []
    for entry in all_items:
        item = entry["item"]
        snippet = item.get("snippet", "") + " " + item.get("title", "")
        if re.search(EMAIL_REGEX, snippet):
            email_items.append(entry)

    logs.append(f"📧 Posts with visible emails in snippet: {len(email_items)}")
    log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)

    # Also keep posts with strong hiring signals even without visible email (AI may find email in full text)
    hiring_keywords = ["send resume", "send your cv", "mail me", "email me", "reach out", "dm me"]
    maybe_items = [
        e for e in all_items
        if e not in email_items and any(kw in (e["item"].get("snippet","") + e["item"].get("title","")).lower() for kw in hiring_keywords)
    ]
    logs.append(f"🔎 Additional posts with hiring signals: {len(maybe_items)}")

    process_items = email_items + maybe_items[:10]  # cap to save API quota

    # AI Extraction
    for j, entry in enumerate(process_items):
        item = entry["item"]
        url = item.get("link", "")
        snippet = item.get("snippet", "") + "\n" + item.get("title", "")
        role = entry["role"]

        logs.append(f"🤖 Extracting [{j+1}/{len(process_items)}]: {url[:60]}...")
        log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)

        # Try to get full page text
        full_text = fetch_page_text(url)
        combined = (full_text or snippet)[:3000]

        result = extract_with_ai(groq_api_key, combined, url, role)
        if result and result.get("email", "N/A") != "N/A":
            st.session_state.results.append(result)
            logs.append(f"   ✅ Email found: {result['email']} | {result.get('company','?')}")
        elif result:
            # Keep even without email — might be useful
            st.session_state.results.append(result)
            logs.append(f"   📋 Saved (no email): {result.get('company','?')} — {result.get('role_hiring','?')}")

        log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)
        progress_bar.progress(0.4 + (j + 1) / len(process_items) * 0.6)
        time.sleep(0.2)

    progress_bar.progress(1.0)
    logs.append(f"🎉 Done! {len(st.session_state.results)} leads extracted.")
    log_box.markdown("\n".join([f'<div class="log-line">{l}</div>' for l in logs[-8:]]), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results

    # Stats
    st.markdown("---")
    st.markdown("### 📊 Results Overview")
    c1, c2, c3, c4 = st.columns(4)

    with_email = [r for r in results if r.get("email", "N/A") != "N/A"]
    roles_found = list(set(r.get("searched_role", "") for r in results))
    companies = list(set(r.get("company", "") for r in results if r.get("company", "N/A") != "N/A"))

    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(results)}</div><div class="stat-label">Total Leads</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(with_email)}</div><div class="stat-label">With Email</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(companies)}</div><div class="stat-label">Companies</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(roles_found)}</div><div class="stat-label">Roles Covered</div></div>', unsafe_allow_html=True)

    # Filter
    st.markdown("### 🎯 Leads")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_email = st.checkbox("Show only leads WITH email", value=True)
    with filter_col2:
        filter_role = st.selectbox("Filter by role", ["All"] + roles_found)

    filtered = results
    if filter_email:
        filtered = [r for r in filtered if r.get("email", "N/A") != "N/A"]
    if filter_role != "All":
        filtered = [r for r in filtered if r.get("searched_role") == filter_role]

    st.markdown(f"**Showing {len(filtered)} leads**")

    for r in filtered:
        with st.container():
            st.markdown(f"""
<div class="card">
  <span class="company-name">{r.get('company', 'Unknown Company')}</span>
  &nbsp;&nbsp;
  <span class="role-badge">{r.get('role_hiring', r.get('searched_role', ''))}</span>
  <br/>
  <span class="meta-text">👤 {r.get('name','?')} — {r.get('designation','?')}</span>
  &nbsp;|&nbsp;
  <span class="meta-text">📍 {r.get('location','?')}</span>
  &nbsp;|&nbsp;
  <span class="meta-text">💼 Exp: {r.get('experience','?')}</span>
  <br/><br/>
  <span class="meta-text">{r.get('post_summary','')}</span>
  <br/><br/>
  {"".join([f'<span class="email-badge">✉️ {e.strip()}</span>' for e in r.get("email","N/A").split(",")]) if r.get("email","N/A") != "N/A" else '<span class="meta-text">No email found</span>'}
  <br/>
  <span class="meta-text" style="font-size:0.7rem; margin-top:6px; display:block">
    <a href="{r.get('source_url','#')}" target="_blank" style="color:#00d9f5;">🔗 View Post</a>
    &nbsp;·&nbsp; Extracted: {r.get('extracted_at','')}
  </span>
</div>
""", unsafe_allow_html=True)

    # Download
    st.markdown("---")
    st.markdown("### 📥 Export")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        excel_buf = results_to_excel(filtered)
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_buf,
            file_name=f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_dl2:
        csv_data = pd.DataFrame(filtered).to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"job_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.markdown("""
<div class="card" style="text-align:center; padding: 2.5rem;">
  <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
  <div style="font-family: 'Space Mono', monospace; color: #00f5a0; font-size: 1rem;">Ready to Hunt</div>
  <div style="color: #8888aa; font-size: 0.85rem; margin-top: 0.4rem;">
    Add your API keys in the sidebar, select target roles, and hit Start Hunt
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color: #555577; font-size: 0.75rem; font-family: 'Space Mono', monospace;">
  LinkedIn Job Hunter · MBA Data Science & AI · Built with Streamlit + Groq + Google Search API
</div>
""", unsafe_allow_html=True)
