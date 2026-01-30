import streamlit as st
import subprocess
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ===================== إعدادات =====================
APP_TITLE = "📄 Offline Office-to-PDF Converter"
DEVELOPER = "Developed by Mohamed Fathy Abu El-Gelany"
WORK_DIR = Path("temp_convert")
USERS_FILE = Path("users.json")
HISTORY_FILE = Path("history.json")
ALLOWED_TYPES = ['docx','doc','pptx','ppt','xlsx','xls']

FREE_LIMIT = 2  # Number of free conversions for guests

# ===================== أدوات =====================
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def load_json(file): return json.load(open(file,"r",encoding="utf-8")) if file.exists() else {}
def save_json(file, data): json.dump(data, open(file,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

users = load_json(USERS_FILE)
history = load_json(HISTORY_FILE)

# ===================== إعداد الصفحة =====================
st.set_page_config(page_title=APP_TITLE, page_icon="📄")

st.markdown("""
<style>
.stApp { background:#F8FAFC; color:#0F172A; font-family:Arial; }
h1,h2,h3 { color:#0F172A; }
.stButton>button {
    background:#22C55E; color:black;
    border-radius:10px; font-weight:bold
}
.card {
    background:#FFFFFF;
    border:1px solid #22C55E;
    padding:15px; border-radius:12px;
    margin-bottom:10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ===================== Session =====================
if "login" not in st.session_state: st.session_state.login = False
if "guest_count" not in st.session_state: st.session_state.guest_count = 0
if "visited" not in st.session_state: st.session_state.visited = False

# ===================== تسجيل / إنشاء =====================
if not st.session_state.login:
    t1,t2 = st.tabs(["🔐 Login", "🆕 Register"])

    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u in users and users[u]["pw"] == hash_pw(p):
                st.session_state.login = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            if nu in users:
                st.warning("Username already exists")
            elif len(np)<4:
                st.warning("Password too short")
            else:
                users[nu] = {
                    "pw": hash_pw(np),
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "count": 0
                }
                save_json(USERS_FILE, users)
                st.success("Account created! Please login.")

    st.stop()

# ===================== Sidebar =====================
with st.sidebar:
    st.write(f"👤 {st.session_state.user if st.session_state.login else 'Guest'}")
    if st.session_state.login:
        if st.button("🗑️ Delete Account"):
            del users[st.session_state.user]
            save_json(USERS_FILE, users)
            st.session_state.login = False
            st.rerun()
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.rerun()

# ===================== Charity message =====================
if not st.session_state.visited:
    st.session_state.visited = True
    st.markdown("""
    <div class='card'>
    🕊️ <b>Sadaqa Jariya for my grandmother</b><br><br>
    May Allah forgive her, have mercy, and make this action in her reward balance 🤍
    </div>
    """, unsafe_allow_html=True)

# ===================== Header =====================
st.title(APP_TITLE)
st.caption(DEVELOPER)
st.divider()

# ===================== File Conversion =====================
uploaded = st.file_uploader("📤 Select your file", type=ALLOWED_TYPES)

def convert(file):
    WORK_DIR.mkdir(exist_ok=True)
    path = WORK_DIR / file.name.replace(" ", "_")
    open(path,"wb").write(file.getbuffer())
    subprocess.run([
        "libreoffice","--headless",
        "--convert-to","pdf",
        str(path),"--outdir",str(WORK_DIR)
    ])
    pdf = WORK_DIR / (path.stem + ".pdf")
    shutil.rmtree(WORK_DIR)
    return pdf if pdf.exists() else None

conversion_allowed = True
if not st.session_state.login:
    if st.session_state.guest_count >= FREE_LIMIT:
        st.warning(f"⚠️ You have reached {FREE_LIMIT} free conversions. Please create an account for unlimited usage.")
        conversion_allowed = False

if uploaded and conversion_allowed and st.button("🚀 Convert to PDF"):
    with st.spinner("Converting..."):
        pdf = convert(uploaded)
        if pdf:
            st.success("Conversion successful!")
            st.download_button("📥 Download PDF", open(pdf,"rb"), pdf.name)
            if st.session_state.login:
                users[st.session_state.user]["count"] +=1
                save_json(USERS_FILE, users)
            else:
                st.session_state.guest_count +=1

            # Save history
            user = st.session_state.user if st.session_state.login else f"Guest_{st.session_state.guest_count}"
            history.setdefault(user, []).append({
                "file": uploaded.name,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_json(HISTORY_FILE, history)
        else:
            st.error("Conversion failed!")

# ===================== Profile & History =====================
if st.session_state.login:
    st.divider()
    st.markdown("## 👤 Profile")
    u = users[st.session_state.user]
    st.markdown(
        f"<div class='card'>📅 Account created: {u['created']}<br>📄 Total conversions: {u['count']}</div>",
        unsafe_allow_html=True
    )
    if st.session_state.user in history:
        st.markdown("## 🗂️ Conversion History")
        for h in history[st.session_state.user][::-1]:
            st.markdown(
                f"<div class='card'>📄 {h['file']}<br>🕒 {h['time']}</div>",
                unsafe_allow_html=True
            )

# ===================== Share =====================
st.divider()
st.markdown("## 🔗 Share this app")
st.code("Share the link and earn rewards 🤍")

st.caption("© 2026 | Sadaqa Jariya")
