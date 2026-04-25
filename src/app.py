"""
Streamlit chat UI for VibeFinder — an agentic music recommender.

Run with:
    streamlit run src/app.py
"""

import streamlit as st

try:
    from src.agent import MusicAgent
except ModuleNotFoundError:
    from agent import MusicAgent

st.set_page_config(page_title="VibeFinder", page_icon="🎵", layout="centered")

st.title("🎵 VibeFinder")
st.caption("Describe what you want to listen to and I'll find your next favorite song.")

# ── Session state ────────────────────────────────────────────────────────────
if "agent" not in st.session_state:
    st.session_state.agent = MusicAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("How it works")
    st.markdown(
        """
        1. Type what vibe you're after in plain English
        2. VibeFinder's AI agent scores every song in the catalog
        3. It looks up genre knowledge to explain its picks
        4. Give feedback ("too intense", "more chill") to refine

        **Genres in catalog:**
        pop · lofi · rock · metal · ambient · hip-hop ·
        r&b · folk · country · jazz · synthwave · edm · classical · indie pop
        """
    )
    if st.button("🔄 New conversation"):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()

# ── Replay chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("steps"):
            with st.expander("🔍 Agent reasoning steps", expanded=False):
                for step in msg["steps"]:
                    st.markdown(f"**Tool:** `{step['tool']}`")
                    st.markdown(f"**Input:** `{step['input']}`")
                    if isinstance(step["output"], list):
                        for item in step["output"][:3]:
                            st.markdown(
                                f"- **{item['title']}** — score {item['score']} — {item['explanation']}"
                            )
                    else:
                        st.text(str(step["output"])[:400])
                    st.divider()

# ── Input ────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("e.g. 'something chill to study to' or 'hype me up'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding your vibe..."):
            try:
                reply = st.session_state.agent.chat(prompt)
                steps = list(st.session_state.agent.steps)
            except EnvironmentError as e:
                reply = f"⚠️ **Setup error:** {e}"
                steps = []
            except Exception as e:
                reply = f"⚠️ **Error:** {e}"
                steps = []

        st.markdown(reply)

        if steps:
            with st.expander("🔍 Agent reasoning steps", expanded=False):
                for step in steps:
                    st.markdown(f"**Tool:** `{step['tool']}`")
                    st.markdown(f"**Input:** `{step['input']}`")
                    if isinstance(step["output"], list):
                        for item in step["output"][:3]:
                            st.markdown(
                                f"- **{item['title']}** — score {item['score']} — {item['explanation']}"
                            )
                    else:
                        st.text(str(step["output"])[:400])
                    st.divider()

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "steps": steps}
    )
