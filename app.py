import streamlit as st
import subprocess
import os
import shutil
import uuid
import json
from datetime import datetime

# =======================
# إعداد الصفحة
# =======================
st.set_page_config(page_title="عون - محول الملفات", page_icon="🛠️", layout="wide")

# =======================
# Session State
# =======================
if "user" not in st.session_state:
    st.session_state.user = None

# =======================
# ملفات التخزين
# =======================
USERS_FILE = "users.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =======================
# إنشاء admin تلقائي
# =======================
users = load_json(USERS_FILE)
if "admin" not in users:
    users["admin"] = {
        "password": "admin123",
        "daily_used": 0,
        "last_day": datetime.now().strftime("%Y-%m-%d"),
        "role": "admin",
        "blocked": False
    }
    save_json(USERS_FILE, users)

# =======================
# CSS
# =======================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif;
    direction: rtl;
}
#MainMenu, footer, header {visibility: hidden;}
.navbar {
    background:#333;
    padding:15px 20px;
    display:flex;
    justify-content:space-between;
    color:white;
    margin-top:-60px;
    margin-left:-5rem;
    margin-right:-5rem;
}
.logo span {
    background:#ff3b3b;
    padding:5px 10px;
    border-radius:50%;
}
</style>
""", unsafe_allow_html=True)

# =======================
# Header
# =======================
st.markdown(f"""
<div class="navbar">
  <div class="logo"><span>🔁</span> عون</div>
  <div>{f"👤 {st.session_state.user}" if st.session_state.user else "تسجيل الدخول | إنشاء حساب"}</div>
</div>
""", unsafe_allow_html=True)

# =======================
# Auth
# =======================
if st.session_state.user is None:
    with st.expander("🔐 تسجيل الدخول / إنشاء حساب"):
        tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب"])
        users = load_json(USERS_FILE)

        with tab1:
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if u in users and users[u]["password"] == p:
                    st.session_state.user = u
                    st.success("تم تسجيل الدخول")
                    st.rerun()
                else:
                    st.error("بيانات غير صحيحة")

        with tab2:
            nu = st.text_input("اسم مستخدم جديد")
            np = st.text_input("كلمة مرور", type="password")
            if st.button("إنشاء حساب"):
                if nu in users:
                    st.warning("اسم المستخدم موجود")
                else:
                    users[nu] = {
                        "password": np,
                        "daily_used": 0,
                        "last_day": datetime.now().strftime("%Y-%m-%d"),
                        "role": "user",
                        "blocked": False
                    }
                    save_json(USERS_FILE, users)
                    st.success("تم إنشاء الحساب")

# =======================
# العنوان
# =======================
st.markdown("<h1 style='text-align:center'>محوّل <span style='color:#ff3b3b'>الملفات</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center'>5 تحويلات مجانية يوميًا</p>", unsafe_allow_html=True)

# =======================
# دالة فحص التحويل
# =======================
def can_convert_today(user):
    today = datetime.now().strftime("%Y-%m-%d")

    if user["blocked"]:
        return False, "🚫 الحساب محظور"

    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today

    if user["daily_used"] >= 5:
        return False, "⚠️ استهلكت 5 تحويلات اليوم"

    return True, ""

# =======================
# رفع وتحويل
# =======================
file = st.file_uploader("اختر ملف", type=["docx","doc","pptx","ppt","xlsx","xls"])

if file and st.button("تحويل الآن 🚀", use_container_width=True):
    if st.session_state.user:
        users = load_json(USERS_FILE)
        user = users[st.session_state.user]

        allowed, msg = can_convert_today(user)
        if not allowed:
            st.error(msg)
            save_json(USERS_FILE, users)
            st.stop()

    with st.spinner("جاري التحويل..."):
        uid = str(uuid.uuid4())
        work = f"temp/{uid}"
        os.makedirs(work, exist_ok=True)

        input_path = os.path.join(work, file.name)
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        subprocess.run(
            ["libreoffice","--headless","--convert-to","pdf",input_path,"--outdir",work],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        pdf = file.name.rsplit(".",1)[0] + ".pdf"
        pdf_path = os.path.join(work, pdf)

        if os.path.exists(pdf_path):
            st.success("تم التحويل بنجاح")
            with open(pdf_path,"rb") as f:
                st.download_button("📥 تحميل PDF", f, file_name=pdf)

            if st.session_state.user:
                users[st.session_state.user]["daily_used"] += 1
                save_json(USERS_FILE, users)
        else:
            st.error("فشل التحويل")

        shutil.rmtree(work, ignore_errors=True)

# =======================
# Dashboard المستخدم
# =======================
if st.session_state.user:
    users = load_json(USERS_FILE)
    u = users[st.session_state.user]

    st.markdown("## 📊 حسابك")
    st.write(f"تحويلات اليوم: {u['daily_used']} / 5")

# =======================
# Admin Panel
# =======================
if st.session_state.user and users[st.session_state.user]["role"] == "admin":
    st.markdown("## 🛠️ Admin Panel")

    for username, data in users.items():
        if username == "admin":
            continue

        with st.expander(f"👤 {username}"):
            st.write(f"تحويلات اليوم: {data['daily_used']}")
            st.write(f"محظور: {'نعم' if data['blocked'] else 'لا'}")

            c1, c2 = st.columns(2)

            with c1:
                if st.button("🔁 تصفير", key=f"r_{username}"):
                    users[username]["daily_used"] = 0
                    save_json(USERS_FILE, users)
                    st.success("تم التصفير")

            with c2:
                if st.button("⛔ حظر / فك", key=f"b_{username}"):
                    users[username]["blocked"] = not data["blocked"]
                    save_json(USERS_FILE, users)
                    st.warning("تم التعديل")
