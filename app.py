import streamlit as st

st.set_page_config(page_title="Election Assistant", layout="wide")

st.title("Election Process Assistant")

section = st.sidebar.radio("Go to", ["Home", "Process", "Timeline", "Interactive Guide"])

if section == "Home":
    st.header("Understand Elections Simply")
    st.write("This assistant helps you explore how elections work, step by step, along with timelines and key concepts.")
    st.write("Use the sidebar to navigate different sections.")

elif section == "Process":
    st.header("Election Process")

    steps = {
        "Announcement": "Election dates and details are officially declared.",
        "Nomination": "Candidates file their applications.",
        "Scrutiny": "Verification of candidate eligibility.",
        "Campaigning": "Candidates promote their agendas.",
        "Polling": "Citizens cast their votes.",
        "Counting": "Votes are counted.",
        "Result": "Winners are announced."
    }

    choice = st.selectbox("Select a step", list(steps.keys()))
    st.subheader(choice)
    st.write(steps[choice])

elif section == "Timeline":
    st.header("Election Timeline")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Phase 1", "Announcement")
        st.metric("Phase 2", "Nomination")

    with col2:
        st.metric("Phase 3", "Campaigning")
        st.metric("Phase 4", "Voting & Results")

    st.progress(75)

elif section == "Interactive Guide":
    st.header("Ask Anything About Elections")

    user_input = st.text_input("Enter your question")

    def get_response(q):
        q = q.lower()

        if "vote" in q or "voting" in q:
            return "Voting is when eligible citizens select their preferred candidate."
        elif "candidate" in q:
            return "Candidates are individuals contesting to represent the public."
        elif "timeline" in q:
            return "An election typically moves from announcement to results over several weeks."
        elif "process" in q or "steps" in q:
            return "The process includes nomination, campaigning, polling, counting, and results."
        elif "commission" in q:
            return "The Election Commission oversees and ensures fair elections."
        else:
            return "Try asking about voting, candidates, process, or timeline."

    if user_input:
        st.write(get_response(user_input))
