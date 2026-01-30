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
# Session
# =======================
if "user" not in st.session_state:
    st.session_state.user = None

# =======================
# ملفات
# =======================
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =======================
# إنشاء admin
# =======================
users = load_users()
if "admin" not in users:
    users["admin"] = {
        "password": "admin123",
        "daily_used": 0,
        "last_day": datetime.now().strftime("%Y-%m-%d"),
        "role": "admin",
        "blocked": False
    }
    save_users(users)

# =======================
# CSS
# =======================
st.markdown("""
<style>
html, body {direction: rtl; font-family: Cairo;}
#MainMenu, footer, header {visibility:hidden;}
.admin-box {
    border:1px solid #ddd;
    padding:15px;
    border-radius:10px;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# =======================
# Header
# =======================
st.markdown(f"""
<div style="background:#333;padding:15px;color:white;display:flex;justify-content:space-between">
<div>🔁 عون</div>
<div>{f"👤 {st.session_state.user}" if st.session_state.user else "تسجيل الدخول | إنشاء حساب"}</div>
</div>
""", unsafe_allow_html=True)

# =======================
# Auth
# =======================
if st.session_state.user is None:
    with st.expander("🔐 تسجيل الدخول / إنشاء حساب"):
        t1, t2 = st.tabs(["دخول", "تسجيل"])
        users = load_users()

        with t1:
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if u in users and users[u]["password"] == p:
                    st.session_state.user = u
                    st.success("تم الدخول")
                    st.rerun()
                else:
                    st.error("بيانات غلط")

        with t2:
            nu = st.text_input("اسم جديد")
            np = st.text_input("كلمة مرور", type="password")
            if st.button("إنشاء"):
                if nu in users:
                    st.warning("موجود")
                else:
                    users[nu] = {
                        "password": np,
                        "daily_used": 0,
                        "last_day": datetime.now().strftime("%Y-%m-%d"),
                        "role": "user",
                        "blocked": False
                    }
                    save_users(users)
                    st.success("تم التسجيل")

# =======================
# دالة التحقق
# =======================
def can_convert(user):
    today = datetime.now().strftime("%Y-%m-%d")

    if user["blocked"]:
        return False, "🚫 الحساب محظور"

    if user["daily_used"] == -1:
        return True, ""

    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today

    if user["daily_used"] >= 5:
        return False, "⚠️ خلصت 5 تحويلات اليوم"

    return True, ""

# =======================
# الواجهة
# =======================
st.markdown("## محول الملفات (5 يوميًا مجانًا)")

file = st.file_uploader("اختر ملف", type=["docx","doc","pptx","ppt","xlsx","xls"])

if file and st.button("تحويل 🚀"):
    if st.session_state.user:
        users = load_users()
        user = users[st.session_state.user]

        ok, msg = can_convert(user)
        if not ok:
            st.error(msg)
            save_users(users)
            st.stop()

    uid = str(uuid.uuid4())
    work = f"temp/{uid}"
    os.makedirs(work, exist_ok=True)

    path = os.path.join(work, file.name)
    with open(path, "wb") as f:
        f.write(file.getbuffer())

    subprocess.run(["libreoffice","--headless","--convert-to","pdf",path,"--outdir",work])

    pdf = file.name.rsplit(".",1)[0] + ".pdf"
    pdf_path = os.path.join(work, pdf)

    if os.path.exists(pdf_path):
        st.success("تم التحويل")
        with open(pdf_path,"rb") as f:
            st.download_button("تحميل PDF", f, file_name=pdf)

        if st.session_state.user:
            if users[st.session_state.user]["daily_used"] != -1:
                users[st.session_state.user]["daily_used"] += 1
            save_users(users)
    else:
        st.error("فشل")

    shutil.rmtree(work, ignore_errors=True)

# =======================
# Admin Panel المتطورة
# =======================
if st.session_state.user and load_users()[st.session_state.user]["role"] == "admin":
    st.markdown("## 🛠️ Admin Panel")

    users = load_users()

    for name, data in users.items():
        if name == "admin":
            continue

        with st.container():
            st.markdown(f"<div class='admin-box'>👤 <b>{name}</b></div>", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"تحويلات: {'∞' if data['daily_used']==-1 else data['daily_used']}")
            c2.write(f"آخر يوم: {data['last_day']}")
            c3.write(f"الحالة: {'محظور' if data['blocked'] else 'نشط'}")

            with c4:
                if st.button("🔁 تصفير", key=f"reset_{name}"):
                    users[name]["daily_used"] = 0
                    save_users(users)
                    st.rerun()

            colA, colB = st.columns(2)
            with colA:
                if st.button("⛔ حظر / فك", key=f"block_{name}"):
                    users[name]["blocked"] = not data["blocked"]
                    save_users(users)
                    st.rerun()

            with colB:
                if st.button("⭐ Unlimited", key=f"vip_{name}"):
                    users[name]["daily_used"] = -1
                    save_users(users)
                    st.rerun()
