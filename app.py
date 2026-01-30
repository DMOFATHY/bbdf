import streamlit as st
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# ===================== إعدادات =====================
APP_TITLE = "📄 محول الملفات إلى PDF"
DEVELOPER = "تطوير: محمد فتحي أبو الجيلاني"
WORK_DIR = Path("temp_convert")
ALLOWED_TYPES = ['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls']

USERS = {
    "admin": "1234",
    "mohamed": "pdf2026"
}

# ===================== إعداد الصفحة =====================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📄",
    layout="centered"
)

# ===================== CSS =====================
st.markdown("""
<style>
.stApp {
    background-color: #020617;
    color: white;
}
h1, h2, h3 {
    color: #22c55e;
}
.stButton > button {
    background-color: #22c55e;
    color: black;
    border-radius: 10px;
    font-weight: bold;
}
.card {
    background-color: #020617;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #22c55e;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ===================== Session =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "history" not in st.session_state:
    st.session_state.history = []

if "count" not in st.session_state:
    st.session_state.count = 0

# ===================== LOGIN =====================
if not st.session_state.logged_in:
    st.markdown("## 🔐 تسجيل الدخول")

    username = st.text_input("👤 اسم المستخدم")
    password = st.text_input("🔑 كلمة السر", type="password")

    if st.button("➡️ دخول", use_container_width=True):
        if username in USERS and USERS[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("✅ تم تسجيل الدخول")
            st.rerun()
        else:
            st.error("❌ بيانات الدخول غير صحيحة")

    st.stop()

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown(f"👋 مرحبًا **{st.session_state.user}**")
    if st.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

# ===================== رسالة الصدقة =====================
if "visited" not in st.session_state:
    st.session_state.visited = True
    st.markdown("""
    <div class="card">
    🕊️ <b>صدقة جارية على روح جدتي</b><br><br>
    اللهم اغفر لها، وارحمها، ونوّر قبرها، واجعل هذا العمل في ميزان حسناتها 🤍
    </div>
    """, unsafe_allow_html=True)

# ===================== العنوان =====================
st.title(APP_TITLE)
st.caption(DEVELOPER)
st.write("تحويل ملفات Office إلى PDF بدون إنترنت")
st.divider()

# ===================== دوال =====================
def create_work_dir():
    WORK_DIR.mkdir(exist_ok=True)

def clean_work_dir():
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)

def convert_to_pdf(input_path: Path) -> Path | None:
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        str(input_path),
        "--outdir",
        str(WORK_DIR)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_path = WORK_DIR / (input_path.stem + ".pdf")
    return pdf_path if pdf_path.exists() else None

# ===================== التحويل =====================
uploaded_file = st.file_uploader("📤 اختر ملف", type=ALLOWED_TYPES)

if uploaded_file:
    st.markdown(f"<div class='card'>📄 {uploaded_file.name}</div>", unsafe_allow_html=True)

    if st.button("🚀 تحويل إلى PDF", use_container_width=True):
        with st.spinner("⏳ جاري التحويل..."):
            try:
                create_work_dir()
                safe_name = uploaded_file.name.replace(" ", "_")
                input_path = WORK_DIR / safe_name

                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                pdf_path = convert_to_pdf(input_path)

                if pdf_path:
                    st.success("✅ تم التحويل بنجاح")

                    st.session_state.count += 1
                    st.session_state.history.append({
                        "user": st.session_state.user,
                        "file": uploaded_file.name,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "📥 تحميل PDF",
                            f,
                            pdf_path.name,
                            "application/pdf",
                            use_container_width=True
                        )
                else:
                    st.error("❌ فشل التحويل")

            finally:
                clean_work_dir()

# ===================== الإحصائيات =====================
st.divider()
st.markdown(f"### 📊 عدد الملفات المحوّلة: **{st.session_state.count}**")

# ===================== السجل =====================
if st.session_state.history:
    st.markdown("### 🗂️ سجل التحويلات")
    for h in st.session_state.history[::-1]:
        st.markdown(
            f"<div class='card'>👤 {h['user']}<br>📄 {h['file']}<br>🕒 {h['time']}</div>",
            unsafe_allow_html=True
        )

# ===================== الشير =====================
st.divider()
st.markdown("### 🔗 مشاركة التطبيق")
st.code("انسخ رابط التطبيق وشاركه – ولك الأجر 🤍")

# ===================== فوتر =====================
st.divider()
st.caption("© 2026 | محول PDF – صدقة جارية")
