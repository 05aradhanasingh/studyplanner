import streamlit as st
import os
from importlib.util import spec_from_file_location, module_from_spec

# Set layout
st.set_page_config(page_title="LIWM – Lock In With Me", layout="wide")

def local_css(file_name):
    full_path = os.path.abspath(file_name)
    with open(full_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = os.path.join(os.path.dirname(__file__), "..", "styles.css")
local_css(css_path)

# --- Load Google Font Jersey 20 ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Jersey+20&display=swap" rel="stylesheet">
<style>
    .title {
        font-family: 'Jersey 20', cursive;
        font-size: 72px;
        margin-bottom: 0;
        color: #111;
    }
    .sub {
        font-size: 28px;
        margin-top: 0;
        color: #444;
    }
</style>
""", unsafe_allow_html=True)

# --- App Heading ---
st.markdown("<h1 class='title'>Lock In With Me</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Are you ready to lock in with me?</div>", unsafe_allow_html=True)

st.markdown("### Choose your Study Buddy")

# --- Load Avatars ---
AVATAR_DIR = "avatars"
avatar_files = sorted([f for f in os.listdir(AVATAR_DIR) if f.startswith("av") and f.endswith(".png")])
cols = st.columns(len(avatar_files))

# --- Avatar Picker ---
for i, file in enumerate(avatar_files):
    with cols[i]:
        st.image(f"{AVATAR_DIR}/{file}", width=100)
        if st.button("Select", key=file):
            st.session_state["selected_avatar"] = file

# --- Info if no avatar yet ---
if "selected_avatar" not in st.session_state:
    st.markdown("👇 Pick one to begin locking in.")
else:
    st.success(f"Locked in with: {st.session_state['selected_avatar']}")

    # --- Dynamically run workpage.py ---
    workpage_path = os.path.join("pages", "workpage.py")
    spec = spec_from_file_location("workpage", workpage_path)
    workpage = module_from_spec(spec)
    spec.loader.exec_module(workpage)
