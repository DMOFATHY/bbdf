import streamlit as st
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import requests

# ===================== إعدادات =====================
APP_TITLE = "📄 محول الملفات إلى PDF مع AI Chat"
WORK_DIR = Path("temp_convert")
ALLOWED_TYPES = ['docx','doc','pptx','ppt','xlsx','xls']

# Gemini API Key
GEMINI_API_KEY = "AIzaSyDeRmbMyDST6WzJQAuPY4DIqxCb19G-g_4"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"

# ===================== Session =====================
if "login" not in st.session_state: st.session_state.login = False
if "visited" not in st.session_state: st.session_state.visited = False

# ===================== الصفحة =====================
st.set_page_config(page_title=APP_TITLE, page_icon="📄")
st.markdown("""
<style>
.stApp { background:#1F2937; color:white; font-family:Arial; }
h1,h2,h3 { color:#22C55E; }
.stButton>button { background:#22C55E; color:black; border-radius:10px; font-weight:bold }
.card { background:#374151; border:1px solid #22C55E; padding:15px; border-radius:12px; margin-bottom:10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2); }
input, textarea { background:#4B5563; color:white; }
</style>
""", unsafe_allow_html=True)

# ===================== Header =====================
st.title(APP_TITLE)
st.divider()

# ===================== التسجيل اختياري =====================
with st.expander("🔐 تسجيل الدخول / إنشاء حساب (اختياري)"):
    username = st.text_input("اسم المستخدم / Username")
    password = st.text_input("كلمة السر / Password", type="password")
    login_btn = st.button("دخول / Login")
    st.write("يمكنك استخدام التطبيق بدون تسجيل أيضًا / You can use the app without login")

# ===================== رفع الملفات =====================
uploaded_file = st.file_uploader("اختر ملف Word / Excel / PowerPoint / Select your file", type=ALLOWED_TYPES)

def convert(file):
    WORK_DIR.mkdir(exist_ok=True)
    path = WORK_DIR / file.name.replace(" ", "_")
    open(path,"wb").write(file.getbuffer())
    subprocess.run(["libreoffice","--headless","--convert-to","pdf", str(path),"--outdir",str(WORK_DIR)])
    pdf = WORK_DIR / (path.stem + ".pdf")
    shutil.rmtree(WORK_DIR)
    return pdf if pdf.exists() else None

if uploaded_file and st.button("🚀 تحويل / Convert to PDF"):
    with st.spinner("جاري التحويل / Converting..."):
        pdf = convert(uploaded_file)
        if pdf:
            st.success("✅ تم التحويل بنجاح / Conversion successful!")
            st.download_button("📥 تحميل PDF / Download PDF", open(pdf,"rb"), pdf.name)
        else:
            st.error("❌ فشل التحويل / Conversion failed!")

# ===================== زر Chat AI =====================
st.divider()
st.markdown("## 💬 Chat AI (Powered by Gemini)")
user_prompt = st.text_area("اكتب سؤالك هنا / Type your question here")

if st.button("💡 إرسال / Send"):
    if user_prompt.strip() == "":
        st.warning("اكتب شيء / Please type something")
    else:
        headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
        data = {
            "prompt": user_prompt,
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        if response.status_code == 200:
            res = response.json()
            answer = res.get("candidates", [{}])[0].get("output", "لا يوجد رد / No response")
            st.markdown(f"**AI Answer / الرد:** {answer}")
        else:
            st.error(f"خطأ في الاتصال / API Error: {response.status_code}")
