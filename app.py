import streamlit as st
import subprocess
import os
import shutil
from datetime import datetime

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="منصة عـون - Awn", page_icon="⚡", layout="wide")

# --- 2. إعداد سجل التحويلات ---
if 'history' not in st.session_state:
    st.session_state.history = []

def add_to_history(filename, status):
    now = datetime.now().strftime("%I:%M %p") # وقت بصيغة 12 ساعة
    st.session_state.history.append({
        "time": now,
        "file": filename,
        "status": status
    })

# --- 3. القائمة الجانبية (السجل) ---
with st.sidebar:
    st.title("🕒 سجل التحويلات")
    if len(st.session_state.history) == 0:
        st.write("لم تقم بتحويل أي ملفات بعد.")
    else:
        for item in reversed(st.session_state.history):
            st.markdown(f"""
            <div style="padding: 8px; border-bottom: 1px solid #eee; margin-bottom: 5px;">
                <div style="font-weight: bold; color: #222;">📄 {item['file']}</div>
                <div style="font-size: 12px; color: #666;">
                   {item['time']} | {item['status']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    st.caption("السجل يمسح عند تحديث الصفحة")

# --- 4. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #ffffff;
        direction: rtl; 
    }

    /* --- الشريط العلوي (نظيف جداً) --- */
    .navbar {
        background-color: #ffffff;
        padding: 10px 20px;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        align-items: center; /* توسيط عمودي */
        margin-bottom: 40px;
    }

    /* --- العناوين --- */
    .hero-title {
        text-align: center;
        color: #da2f2f;
        font-size: 45px;
        font-weight: 900;
        margin-top: 20px;
    }
    .hero-subtitle {
        text-align: center;
        color: #333;
        font-size: 20px;
        margin-bottom: 40px;
    }

    /* --- منطقة الرفع والزر --- */
    div[data-testid="stFileUploader"] {
        background-color: #333;
        padding: 30px;
        border-radius: 8px;
        text-align: center;
        max-width: 700px;
        margin: 0 auto;
    }
    div[data-testid="stFileUploader"] label { color: white; }
    div[data-testid="stFileUploader"] .stMarkdown { color: #eee; }

    .stButton button {
        background-color: #da2f2f !important;
        color: white !important;
        font-size: 18px !important;
        padding: 10px 30px !important;
        border-radius: 5px !important;
        border: none !important;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #b71c1c !important;
    }

    /* --- كروت الصدقة --- */
    .sadaqa-header {
        text-align: center;
        margin-top: 60px;
        margin-bottom: 20px;
        color: #2c3e50;
        border-top: 2px solid #f5f5f5;
        padding-top: 30px;
    }
    .full-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        overflow: hidden;
        border: 1px solid #eee;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .full-card:hover { transform: translateY(-3px); }
    .card-img-container img {
        width: 100%;
        height: 220px !important;
        object-fit: cover;
    }
    .card-content { padding: 15px; text-align: center; }
    .person-name-title { font-size: 18px; font-weight: bold; color: #000; margin-bottom: 5px; }
    .dua-text-body { font-size: 14px; color: #444; line-height: 1.6; background-color: #f9fff9; padding: 8px; border-radius: 6px; }
    .final-footer { background-color: #333; color: white; padding: 15px; text-align: center; border-radius: 6px; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

# --- 5. الهيكل العلوي (لوجو عون فقط) ---
st.markdown("""
<div class="navbar" style="direction: ltr;">
    <div class="nav-logo" style="font-family: 'Cairo', sans-serif; display: flex; align-items: center; gap: 10px;">
        <div style="
            background: linear-gradient(135deg, #da2f2f, #b71c1c);
            color: white;
            width: 40px; height: 40px;
            border-radius: 8px;
            display: flex; justify-content: center; align-items: center;
            font-weight: 900; font-size: 22px;
            box-shadow: 0 2px 4px rgba(218, 47, 47, 0.2);
        ">
            عـ
        </div>
        <span style="color: #000; font-size: 24px; font-weight: 900;">عون</span>
    </div>
</div>

<div class="hero-title">محوّل الملفات</div>
<div class="hero-subtitle">حوّل ملفاتك إلى أي صيغة (PDF)</div>
""", unsafe_allow_html=True)

# --- 6. منطق التحويل ---
col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])

with col_main:
    uploaded_file = st.file_uploader(" ", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])

    if uploaded_file is not None:
        st.write(f"📂 الملف المختار: **{uploaded_file.name}**")
        
        if st.button("تحويل الآن 🚀"):
            with st.spinner('جاري التحويل...'):
                try:
                    work_dir = "temp_convert"
                    if not os.path.exists(work_dir):
                        os.makedirs(work_dir)
                    
                    safe_filename = uploaded_file.name.replace(" ", "_")
                    input_path = os.path.join(work_dir, safe_filename)
                    
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                    output_path = os.path.join(work_dir, pdf_filename)

                    if os.path.exists(output_path):
                        st.success("✅ تم التحويل!")
                        add_to_history(uploaded_file.name, "✅ تم")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 تنزيل الملف (PDF)",
                                data=f,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                    else:
                        st.error("فشل التحويل.")
                        add_to_history(uploaded_file.name, "❌ فشل")
                    
                    shutil.rmtree(work_dir)

                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

# --- 7. قسم الصدقة الجارية ---
st.markdown('<h2 class="sadaqa-header">🤲 صدقة جارية ونسألكم الدعاء</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

# الجدة
with col1:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container"><img src="1000479933.jpg" alt="جدتي"></div>
        <div class="card-content">
            <div class="person-name-title">جدتي (رحمها الله)</div>
            <div class="dua-text-body">اللهم ارحمها واغفر لها، واجعل قبرها روضة من رياض الجنة، وأسكنها الفردوس الأعلى.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# محمود
with col2:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container"><img src="1000479919.jpg" alt="محمود"></div>
        <div class="card-content">
            <div class="person-name-title">محمود (رحمه الله)</div>
            <div class="dua-text-body">اللهم اغفر له وارحمه، وعافه واعف عنه، وأكرم نزله، ووسع مدخله، ونقه من الخطايا.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# أحمد
with col3:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container"><img src="1000479894.jpg" alt="أحمد"></div>
        <div class="card-content">
            <div class="person-name-title">أحمد (عريس الجنة)</div>
            <div class="dua-text-body">اللهم إنه في ذمتك، فقه فتنة القبر وعذاب النار. اللهم عوض شبابه في الجنة، واجعله من الضاحكين.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="final-footer">هذا الموقع خالص لوجه الله وصدقة جارية</div>', unsafe_allow_html=True)

