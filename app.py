import streamlit as st

st.set_page_config(page_title="Election Assistant", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Election Process Assistant")

section = st.sidebar.radio("Navigate", ["Overview", "Process", "Timeline", "Simulator", "Ask"])

data = {
    "Announcement": "Election schedule is released officially.",
    "Nomination": "Candidates submit required documents.",
    "Scrutiny": "Authorities verify eligibility.",
    "Campaign": "Candidates reach out to voters.",
    "Polling": "Citizens vote.",
    "Counting": "Votes are tallied.",
    "Result": "Winner is declared."
}

if section == "Overview":
    st.header("Overview")
    st.write("This assistant explains elections interactively.")
    st.progress(len(st.session_state.history) / 10 if st.session_state.history else 0)

elif section == "Process":
    st.header("Steps")

    cols = st.columns(3)
    keys = list(data.keys())

    for i, step in enumerate(keys):
        with cols[i % 3]:
            if st.button(step):
                st.session_state.history.append(step)
                st.success(data[step])

elif section == "Timeline":
    st.header("Timeline")

    phases = ["Announcement", "Nomination", "Campaign", "Polling", "Result"]
    selected = st.select_slider("Flow", options=phases)

    for p in phases:
        if phases.index(p) <= phases.index(selected):
            st.write("✓ " + p)
        else:
            st.write("• " + p)

elif section == "Simulator":
    st.header("Voting Simulation")

    voters = st.number_input("Number of voters", min_value=1, max_value=1000, value=10)
    candidates = st.text_input("Candidates (comma separated)", "A,B,C")

    if st.button("Run Simulation"):
        import random
        c = [x.strip() for x in candidates.split(",") if x.strip()]
        result = {i: 0 for i in c}

        for _ in range(voters):
            result[random.choice(c)] += 1

        winner = max(result, key=result.get)

        st.write(result)
        st.success("Winner: " + winner)

elif section == "Ask":
    st.header("Ask")

    q = st.text_input("Your question")

    def respond(x):
        x = x.lower()
        if "vote" in x:
            return "Voting is the act of choosing a representative."
        if "candidate" in x:
            return "Candidates are contesting individuals."
        if "timeline" in x:
            return "It moves from announcement to results."
        if "process" in x:
            return "Nomination, campaign, polling, counting, result."
        return "Ask about voting, process, or timeline."

    if q:
        ans = respond(q)
        st.session_state.history.append(q)
        st.write(ans)
