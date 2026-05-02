import streamlit as st
import random
import time
import unittest
import io
import sys
import requests
import urllib.parse

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Election Process Assistant",
    layout="wide",
    page_icon="🗳️",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://en.wikipedia.org/wiki/Elections",
        "About": "A civic education tool for understanding elections."
    }
)

# ─── Accessibility: Skip-to-content + ARIA-friendly CSS ───────────────────────
st.markdown("""
<style>
/* Skip-to-content for keyboard users */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #1a56db;
    color: white;
    padding: 8px 16px;
    z-index: 9999;
    font-size: 14px;
    border-radius: 0 0 4px 0;
    text-decoration: none;
    font-family: 'Georgia', serif;
}
.skip-link:focus {
    top: 0;
}

/* High-contrast accessible text */
body, .stMarkdown, .stText {
    color: #1a1a2e;
    font-family: 'Georgia', serif;
}

/* Focus indicator */
button:focus, input:focus, select:focus {
    outline: 3px solid #1a56db !important;
    outline-offset: 2px !important;
}

/* Badge styles */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 8px;
}
.badge-green  { background: #dcfce7; color: #166534; }
.badge-blue   { background: #dbeafe; color: #1e40af; }
.badge-yellow { background: #fef9c3; color: #92400e; }

/* Step cards */
.step-card {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    background: #f8fafc;
    transition: box-shadow 0.2s;
}
.step-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }

/* Timeline node */
.tl-node { display:flex; align-items:flex-start; margin-bottom:20px; }
.tl-dot  { width:18px; height:18px; border-radius:50%; background:#1a56db;
            margin-right:14px; margin-top:3px; flex-shrink:0; }
.tl-dot.done { background:#22c55e; }
.tl-dot.pending { background:#cbd5e1; }
.tl-text h4 { margin:0 0 4px; font-size:15px; color:#1e293b; }
.tl-text p  { margin:0; font-size:13px; color:#64748b; }

/* Metric cards */
.metric-box {
    border-radius: 8px;
    padding: 14px 18px;
    text-align: center;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
}
.metric-box .val { font-size: 28px; font-weight: 700; color: #1d4ed8; }
.metric-box .lbl { font-size: 12px; color: #64748b; margin-top: 4px; }
</style>
<a class="skip-link" href="#main">Skip to main content</a>
<div id="main"></div>
""", unsafe_allow_html=True)

# ─── Session State Init ────────────────────────────────────────────────────────
defaults = {
    "history": [],
    "sim_results": None,
    "sim_winner": None,
    "explored_steps": set(),
    "last_search": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Data ─────────────────────────────────────────────────────────────────────
STEPS = {
    "Announcement":  {"desc": "Election schedule is officially declared by the Election Commission.", "icon": "📢", "phase": 1},
    "Nomination":    {"desc": "Candidates file nomination papers and required documents.",             "icon": "📝", "phase": 2},
    "Scrutiny":      {"desc": "Authorities verify the eligibility of all candidates.",                "icon": "🔍", "phase": 3},
    "Campaigning":   {"desc": "Candidates campaign and interact with the public.",                    "icon": "📣", "phase": 4},
    "Polling":       {"desc": "Citizens cast their votes at designated booths.",                      "icon": "🗳️", "phase": 5},
    "Counting":      {"desc": "Votes are tallied under strict supervision.",                          "icon": "🔢", "phase": 6},
    "Result":        {"desc": "The winner is announced and certified.",                               "icon": "🏆", "phase": 7},
}

PHASES = list(STEPS.keys())

QA_MAP = {
    ("vote", "voting"):          "Voting is the act of eligible citizens selecting their preferred candidate by casting a ballot.",
    ("candidate",):              "Candidates are individuals who formally contest an election to represent the public.",
    ("timeline", "schedule"):    "An election typically moves from Announcement → Nomination → Scrutiny → Campaigning → Polling → Counting → Result.",
    ("process", "steps", "how"): "The election process: Nomination, Scrutiny, Campaigning, Polling, Counting, then the Result.",
    ("commission", "eci"):       "The Election Commission of India (ECI) is an autonomous constitutional authority that oversees elections.",
    ("nomination",):             "Nomination is when candidates submit their legal papers to contest an election.",
    ("scrutiny",):               "Scrutiny is the formal verification of candidate eligibility by election authorities.",
    ("campaign",):               "Campaigning is the period when candidates promote their agendas to attract voters.",
    ("result", "winner"):        "Results are announced after votes are counted. The candidate with most valid votes wins.",
    ("esi", "evm", "machine"):   "EVMs (Electronic Voting Machines) are used in India to ensure accuracy and efficiency in vote counting.",
}

def get_response(q: str) -> str:
    q = q.lower()
    for keywords, answer in QA_MAP.items():
        if any(k in q for k in keywords):
            return answer
    return "Try asking about: voting, candidates, nomination, scrutiny, campaigning, timeline, commission, or EVMs."

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_India.svg/320px-Flag_of_India.svg.png", width=120)
    st.markdown("### 🗳️ Election Assistant")
    section = st.radio(
        "Navigate",
        ["🏠 Overview", "📋 Process", "📅 Timeline", "🎲 Simulator", "🔍 Ask", "🌐 Google Services", "🧪 Tests"],
        label_visibility="collapsed"
    )
    st.divider()
    progress_val = len(st.session_state.explored_steps) / len(STEPS)
    st.markdown(f"**Exploration Progress:** {int(progress_val * 100)}%")
    st.progress(progress_val)
    st.caption(f"Steps explored: {len(st.session_state.explored_steps)} / {len(STEPS)}")

# ─── Main Content ─────────────────────────────────────────────────────────────

# 1. OVERVIEW
if section == "🏠 Overview":
    st.title("Election Process Assistant")
    st.markdown("> *Understand elections clearly, step by step.*")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-box"><div class="val">7</div><div class="lbl">Election Phases</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box"><div class="val">~60</div><div class="lbl">Days (Avg. Cycle)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box"><div class="val">960M+</div><div class="lbl">Registered Voters (India)</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("What you can do here")
    st.markdown("""
- 📋 **Process** — Explore each election step in detail  
- 📅 **Timeline** — Navigate the election flow visually  
- 🎲 **Simulator** — Run a mock election with live results  
- 🔍 **Ask** — Get plain-language answers to your questions  
- 🌐 **Google Services** — Search Google and fetch live Wikipedia data  
- 🧪 **Tests** — Run built-in unit tests to verify the app logic  
    """)
    st.info("💡 Tip: Track your exploration progress in the sidebar!")

# 2. PROCESS
elif section == "📋 Process":
    st.title("Election Process")
    st.caption("Click any step to learn more.")
    st.divider()

    cols = st.columns(3)
    step_list = list(STEPS.items())
    for i, (step, info) in enumerate(step_list):
        with cols[i % 3]:
            explored = step in st.session_state.explored_steps
            badge = '<span class="badge badge-green">✓ Done</span>' if explored else ""
            st.markdown(f"""
            <div class="step-card" role="region" aria-label="Step: {step}">
                <h4>{info['icon']} Phase {info['phase']}: {step} {badge}</h4>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Learn: {step}", key=f"btn_{step}", help=f"Click to see details about {step}"):
                st.session_state.explored_steps.add(step)
                st.success(f"**{info['icon']} {step}**: {info['desc']}")

    st.divider()
    if st.session_state.explored_steps:
        st.markdown(f"**Steps explored this session:** {', '.join(st.session_state.explored_steps)}")

# 3. TIMELINE
elif section == "📅 Timeline":
    st.title("Election Timeline")
    st.divider()

    selected = st.select_slider(
        "Move through the election phases:",
        options=PHASES,
        value=PHASES[0],
        help="Drag the slider to see which phases are complete"
    )
    selected_idx = PHASES.index(selected)
    st.divider()

    for i, phase in enumerate(PHASES):
        info = STEPS[phase]
        if i < selected_idx:
            dot_class, status = "tl-dot done", "✅ Complete"
        elif i == selected_idx:
            dot_class, status = "tl-dot", "▶ Current"
        else:
            dot_class, status = "tl-dot pending", "⏳ Upcoming"

        st.markdown(f"""
        <div class="tl-node" role="listitem" aria-label="Phase {i+1}: {phase}, {status}">
            <div class="{dot_class}"></div>
            <div class="tl-text">
                <h4>{info['icon']} Phase {i+1}: {phase} &nbsp; <small style="font-weight:400;color:#64748b;">{status}</small></h4>
                <p>{info['desc']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    pct = int((selected_idx + 1) / len(PHASES) * 100)
    st.markdown(f"**Overall progress: {pct}%**")
    st.progress(pct / 100)

# 4. SIMULATOR
elif section == "🎲 Simulator":
    st.title("Voting Simulator")
    st.caption("Simulate a mock election with configurable voters and candidates.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        voters = st.number_input("Number of Voters", min_value=1, max_value=100_000, value=100, step=10, help="Total voters casting ballots")
    with col2:
        candidates_input = st.text_input("Candidates (comma-separated)", value="Alice, Bob, Carol", help="Enter candidate names separated by commas")

    add_noise = st.checkbox("Add voter bias (simulate realistic turnout)", value=True)

    if st.button("🗳️ Run Election", type="primary"):
        candidates = [c.strip() for c in candidates_input.split(",") if c.strip()]
        if len(candidates) < 2:
            st.error("Please enter at least 2 candidates.")
        else:
            with st.spinner("Simulating election..."):
                time.sleep(0.4)   # Simulate processing (efficient — no heavy loops shown to user)

                if add_noise:
                    weights = [random.uniform(0.5, 2.0) for _ in candidates]
                    total_w = sum(weights)
                    weights = [w / total_w for w in weights]
                    result = {c: 0 for c in candidates}
                    for _ in range(voters):
                        result[random.choices(candidates, weights=weights)[0]] += 1
                else:
                    result = {c: 0 for c in candidates}
                    for _ in range(voters):
                        result[random.choice(candidates)] += 1

                winner = max(result, key=result.get)
                st.session_state.sim_results = result
                st.session_state.sim_winner = winner

    if st.session_state.sim_results:
        st.divider()
        st.success(f"🏆 Winner: **{st.session_state.sim_winner}**")
        st.subheader("Results Breakdown")

        total_votes = sum(st.session_state.sim_results.values())
        for candidate, votes in sorted(st.session_state.sim_results.items(), key=lambda x: -x[1]):
            pct = votes / total_votes * 100
            label = f"{candidate}: {votes:,} votes ({pct:.1f}%)"
            st.markdown(f"**{label}**" + (" 🏆" if candidate == st.session_state.sim_winner else ""))
            st.progress(pct / 100)

        st.caption(f"Total votes cast: {total_votes:,}")

# 5. ASK
elif section == "🔍 Ask":
    st.title("Ask About Elections")
    st.caption("Type your question below and get an instant answer.")
    st.divider()

    q = st.text_input("Your question:", placeholder="e.g. What is the election commission?", label_visibility="visible")
    if q:
        start = time.time()
        ans = get_response(q)
        elapsed = time.time() - start
        st.session_state.history.append({"q": q, "a": ans})
        st.markdown(f"**Answer:** {ans}")
        st.caption(f"Response time: {elapsed*1000:.1f} ms")

    if st.session_state.history:
        st.divider()
        with st.expander("📜 Q&A History"):
            for item in reversed(st.session_state.history):
                st.markdown(f"**Q:** {item['q']}")
                st.markdown(f"**A:** {item['a']}")
                st.divider()

# 6. GOOGLE SERVICES
elif section == "🌐 Google Services":
    st.title("Google Services Integration")
    st.caption("Search Google or fetch live data from Wikipedia's API.")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["🔎 Google Search", "📖 Wikipedia API", "🗺️ Google Maps"])

    with tab1:
        st.subheader("Google Search")
        search_query = st.text_input("Enter search query:", placeholder="India election commission 2024", key="gsearch")
        if st.button("Open in Google", key="google_btn"):
            if search_query:
                encoded = urllib.parse.quote_plus(search_query)
                url = f"https://www.google.com/search?q={encoded}"
                st.markdown(f"🔗 [Click to open Google Search for **'{search_query}'**]({url})", unsafe_allow_html=False)
                st.info("Google Search results open externally. Use the link above.")
            else:
                st.warning("Please enter a search query.")

    with tab2:
        st.subheader("Wikipedia Live Data (via Wikipedia API)")
        wiki_query = st.text_input("Wikipedia article topic:", value="Elections in India", key="wiki_q")
        if st.button("Fetch from Wikipedia", key="wiki_btn"):
            if wiki_query:
                with st.spinner("Fetching from Wikipedia API..."):
                    try:
                        params = {
                            "action": "query",
                            "titles": wiki_query,
                            "prop": "extracts",
                            "exintro": True,
                            "explaintext": True,
                            "format": "json",
                            "redirects": 1,
                        }
                        resp = requests.get(
                            "https://en.wikipedia.org/w/api.php",
                            params=params,
                            timeout=5
                        )
                        if resp.status_code == 200:
                            pages = resp.json().get("query", {}).get("pages", {})
                            page = next(iter(pages.values()))
                            title = page.get("title", "Unknown")
                            extract = page.get("extract", "No content found.")
                            st.success(f"**{title}**")
                            st.write(extract[:1500] + ("..." if len(extract) > 1500 else ""))
                            st.caption(f"Source: Wikipedia | Characters fetched: {len(extract)}")
                        else:
                            st.error(f"Wikipedia API error: {resp.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Network error: {e}")
            else:
                st.warning("Please enter a topic.")

    with tab3:
        st.subheader("Google Maps — Find Polling Booth")
        location = st.text_input("Enter your city or area:", placeholder="Mumbai, Maharashtra")
        if st.button("Find on Google Maps", key="maps_btn"):
            if location:
                encoded_loc = urllib.parse.quote_plus(f"polling booth near {location}")
                maps_url = f"https://www.google.com/maps/search/{encoded_loc}"
                st.markdown(f"🗺️ [Open Google Maps for polling booths near **{location}**]({maps_url})")
                st.caption("Opens Google Maps in a new tab.")
            else:
                st.warning("Please enter a location.")

# 7. TESTS
elif section == "🧪 Tests":
    st.title("Unit Tests")
    st.caption("Built-in tests to verify the app logic is working correctly.")
    st.divider()

    class TestElectionLogic(unittest.TestCase):

        def test_get_response_vote(self):
            resp = get_response("how do I vote?")
            self.assertIn("ballot", resp.lower())

        def test_get_response_candidate(self):
            resp = get_response("who is a candidate?")
            self.assertIn("candidate", resp.lower())

        def test_get_response_timeline(self):
            resp = get_response("what is the timeline?")
            self.assertIn("Announcement", resp)

        def test_get_response_unknown(self):
            resp = get_response("xyzzy unknown question")
            self.assertIn("Try asking", resp)

        def test_simulation_vote_count(self):
            candidates = ["A", "B", "C"]
            voters = 100
            result = {c: 0 for c in candidates}
            for _ in range(voters):
                result[random.choice(candidates)] += 1
            self.assertEqual(sum(result.values()), voters)

        def test_simulation_winner_is_candidate(self):
            candidates = ["X", "Y"]
            result = {"X": 60, "Y": 40}
            winner = max(result, key=result.get)
            self.assertIn(winner, candidates)
            self.assertEqual(winner, "X")

        def test_steps_completeness(self):
            self.assertEqual(len(STEPS), 7)

        def test_steps_have_required_keys(self):
            for name, info in STEPS.items():
                self.assertIn("desc",  info, f"{name} missing 'desc'")
                self.assertIn("icon",  info, f"{name} missing 'icon'")
                self.assertIn("phase", info, f"{name} missing 'phase'")

        def test_phases_order(self):
            phases_ordered = [info["phase"] for info in STEPS.values()]
            self.assertEqual(phases_ordered, sorted(phases_ordered))

        def test_qa_map_non_empty(self):
            self.assertGreater(len(QA_MAP), 0)

    if st.button("▶ Run All Tests", type="primary"):
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestElectionLogic)

        buf = io.StringIO()
        runner = unittest.TextTestRunner(stream=buf, verbosity=2)

        with st.spinner("Running tests..."):
            result_obj = runner.run(suite)

        output = buf.getvalue()
        st.divider()

        passed = result_obj.testsRun - len(result_obj.failures) - len(result_obj.errors)
        total  = result_obj.testsRun

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tests", total)
        col2.metric("Passed ✅", passed)
        col3.metric("Failed ❌", len(result_obj.failures) + len(result_obj.errors))

        if result_obj.wasSuccessful():
            st.success(f"All {total} tests passed! ✅")
        else:
            st.error(f"{len(result_obj.failures) + len(result_obj.errors)} test(s) failed.")

        with st.expander("📄 Full Test Output"):
            st.code(output, language="text")

        if result_obj.failures:
            st.subheader("Failures")
            for test, traceback in result_obj.failures:
                st.error(f"**{test}**\n```\n{traceback}\n```")

        if result_obj.errors:
            st.subheader("Errors")
            for test, traceback in result_obj.errors:
                st.error(f"**{test}**\n```\n{traceback}\n```")
