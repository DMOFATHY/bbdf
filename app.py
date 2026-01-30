import streamlit as st
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime
import hashlib

# ===================== إعدادات =====================
APP_TITLE = "📄 محول الملفات إلى PDF"
DEVELOPER = "تطوير: محمد فتحي أبو الجيلاني"
WORK_DIR = Path("temp_convert")
USERS_FILE = Path("users.json")
ALLOWED_TYPES = ['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls']

# ===================== إعداد الصفحة =====================
st.set_page_config(page_title=APP_TITLE, page_icon="📄")

# ===================== CSS =====================
st.markdown("""
<style>
.stApp { background-color: #020617; color: white; }
h1 { color: #22c55e; }
.stButton>button { background:#22c55e; color:black; border-radius:10px; }
.card {
    background:#020617; padding:15px;
    border-radius:12px; border:1px solid #22c55e;
}
</style>
""", unsafe_allow_html=True)

# ===================== دوال المستخدمين =====================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if USERS_FILE.exists():
        return json.load(open(USERS_FILE, "r", encoding="utf-8"))
    return {}

def save_users(users):
    json.dump(users, open(USERS_FILE, "w", encoding="utf-8"), indent=2)

# ===================== Session =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

users = load_users()

# ===================== تسجيل / دخول =====================
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "🆕 إنشاء حساب"])

    with tab1:
        username = st.text_input("👤 اسم المستخدم")
        password = st.text_input("🔑 كلمة السر", type="password")

        if st.button("➡️ دخول"):
            if username in users and users[username] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success("تم تسجيل الدخول بنجاح")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")

    with tab2:
        new_user = st.text_input("👤 اسم مستخدم جديد")
        new_pass = st.text_input("🔑 كلمة سر", type="password")

        if st.button("🆕 إنشاء الحساب"):
            if new_user in users:
                st.warning("اسم المستخدم موجود بالفعل")
            elif len(new_pass) < 4:
                st.warning("كلمة السر قصيرة")
            else:
                users[new_user] = hash_password(new_pass)
                save_users(users)
                st.success("تم إنشاء الحساب – يمكنك تسجيل الدخول الآن")

    st.stop()

# ===================== Sidebar =====================
with st.sidebar:
    st.write(f"👋 مرحبًا {st.session_state.user}")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

# ===================== رسالة الصدقة =====================
if "visited" not in st.session_state:
    st.session_state.visited = True
    st.markdown("""
    <div class='card'>
    🕊️ <b>صدقة جارية على روح جدتي</b><br><br>
    اللهم اغفر لها وارحمها واجعل هذا العمل في ميزان حسناتها 🤍
    </div>
    """, unsafe_allow_html=True)

# ===================== العنوان =====================
st.title(APP_TITLE)
st.caption(DEVELOPER)
st.divider()

# ===================== التحويل =====================
uploaded_file = st.file_uploader("📤 اختر ملف", type=ALLOWED_TYPES)

def convert_to_pdf(file):
    WORK_DIR.mkdir(exist_ok=True)
    path = WORK_DIR / file.name.replace(" ", "_")
    open(path, "wb").write(file.getbuffer())

    subprocess.run([
        "libreoffice", "--headless",
        "--convert-to", "pdf",
        str(path), "--outdir", str(WORK_DIR)
    ])

    pdf = WORK_DIR / (path.stem + ".pdf")
    shutil.rmtree(WORK_DIR)
    return pdf if pdf.exists() else None

if uploaded_file and st.button("🚀 تحويل"):
    with st.spinner("جاري التحويل..."):
        pdf = convert_to_pdf(uploaded_file)
        if pdf:
            st.success("تم التحويل بنجاح")
            st.download_button("📥 تحميل PDF", open(pdf, "rb"), pdf.name)
        else:
            st.error("فشل التحويل")

# ===================== فوتر =====================
st.divider()
st.caption("© 2026 | صدقة جارية")
