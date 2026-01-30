import streamlit as st
import subprocess
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ===================== إعدادات =====================
APP_TITLE = "📄 محول الملفات إلى PDF"
DEVELOPER = "تطوير: محمد فتحي أبو الجيلاني"
WORK_DIR = Path("temp_convert")
USERS_FILE = Path("users.json")
HISTORY_FILE = Path("history.json")
ALLOWED_TYPES = ['docx','doc','pptx','ppt','xlsx','xls']

# ===================== أدوات =====================
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def load_json(file):
    if file.exists():
        return json.load(open(file, "r", encoding="utf-8"))
    return {}

def save_json(file, data):
    json.dump(data, open(file, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

users = load_json(USERS_FILE)
history = load_json(HISTORY_FILE)

# ===================== إعداد الصفحة =====================
st.set_page_config(page_title=APP_TITLE, page_icon="📄")

st.markdown("""
<style>
.stApp { background:#020617; color:white }
h1,h2 { color:#22c55e }
.stButton>button {
    background:#22c55e; color:black;
    border-radius:10px; font-weight:bold
}
.card {
    background:#020617;
    border:1px solid #22c55e;
    padding:15px; border-radius:12px;
    margin-bottom:10px
}
</style>
""", unsafe_allow_html=True)

# ===================== Session =====================
if "login" not in st.session_state:
    st.session_state.login = False

# ===================== تسجيل / إنشاء =====================
if not st.session_state.login:
    t1, t2 = st.tabs(["🔐 تسجيل الدخول", "🆕 إنشاء حساب"])

    with t1:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if u in users and users[u]["pw"] == hash_pw(p):
                st.session_state.login = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("بيانات غير صحيحة")

    with t2:
        nu = st.text_input("اسم مستخدم جديد")
        np = st.text_input("كلمة سر", type="password")
        if st.button("إنشاء الحساب"):
            if nu in users:
                st.warning("الاسم موجود")
            elif len(np) < 4:
                st.warning("كلمة السر قصيرة")
            else:
                users[nu] = {
                    "pw": hash_pw(np),
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "count": 0
                }
                save_json(USERS_FILE, users)
                st.success("تم إنشاء الحساب")

    st.stop()

# ===================== Sidebar =====================
with st.sidebar:
    st.write(f"👤 {st.session_state.user}")
    if st.button("🗑️ حذف الحساب"):
        del users[st.session_state.user]
        save_json(USERS_FILE, users)
        st.session_state.login = False
        st.rerun()

    if st.button("🚪 تسجيل الخروج"):
        st.session_state.login = False
        st.rerun()

# ===================== رسالة الصدقة =====================
if "visited" not in st.session_state:
    st.session_state.visited = True
    st.markdown("""
    <div class='card'>
    🕊️ <b>صدقة جارية على روح جدتي</b><br><br>
    اللهم اغفر لها وارحمها ونوّر قبرها واجعل هذا العمل في ميزان حسناتها 🤍
    </div>
    """, unsafe_allow_html=True)

# ===================== العنوان =====================
st.title(APP_TITLE)
st.caption(DEVELOPER)
st.divider()

# ===================== التحويل =====================
uploaded = st.file_uploader("📤 اختر ملف", type=ALLOWED_TYPES)

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

if uploaded and st.button("🚀 تحويل"):
    with st.spinner("جاري التحويل..."):
        pdf = convert(uploaded)
        if pdf:
            st.success("تم التحويل")
            st.download_button("تحميل PDF", open(pdf,"rb"), pdf.name)

            users[st.session_state.user]["count"] += 1
            save_json(USERS_FILE, users)

            history.setdefault(st.session_state.user, []).append({
                "file": uploaded.name,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_json(HISTORY_FILE, history)
        else:
            st.error("فشل التحويل")

# ===================== بروفايل =====================
st.divider()
st.markdown("## 👤 البروفايل")
u = users[st.session_state.user]
st.markdown(
    f"<div class='card'>📅 تاريخ الحساب: {u['created']}<br>📄 عدد التحويلات: {u['count']}</div>",
    unsafe_allow_html=True
)

# ===================== السجل =====================
if st.session_state.user in history:
    st.markdown("## 🗂️ سجل التحويلات")
    for h in history[st.session_state.user][::-1]:
        st.markdown(
            f"<div class='card'>📄 {h['file']}<br>🕒 {h['time']}</div>",
            unsafe_allow_html=True
        )

# ===================== شير =====================
st.divider()
st.markdown("## 🔗 مشاركة")
st.code("شارِك التطبيق – ولك الأجر 🤍")

st.caption("© 2026 | صدقة جارية")
