import streamlit as st
import subprocess
import os
import shutil
from datetime import datetime

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="منصة عـون - Awn", page_icon="⚡", layout="wide")

# --- 2. إعداد سجل التحويلات (Session State) ---
if 'history' not in st.session_state:
    st.session_state.history = []

# دالة لإضافة عملية للسجل
def add_to_history(filename, status):
    now = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.append({
        "time": now,
        "file": filename,
        "status": status
    })

# --- 3. القائمة الجانبية (السجل) ---
with st.sidebar:
    st.title("🕒 سجل التحويلات")
    st.write("هنا تظهر الملفات التي حولتها في هذه الجلسة:")
    
    if len(st.session_state.history) == 0:
        st.info("لم تقم بتحويل أي ملفات بعد.")
    else:
        for item in reversed(st.session_state.history):
            st.markdown(f"""
            <div style="padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 5px;">
                <div style="font-weight: bold; color: #333;">📄 {item['file']}</div>
                <div style="font-size: 12px; color: #666;">
                    الساعة: {item['time']} | الحالة: {item['status']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    st.write("💡 هذا السجل يمسح عند تحديث الصفحة.")

# --- 4. التصميم (CSS) ---
st.markdown("""
<style>
    /* استيراد خط Cairo */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    /* إخفاء القائمة العلوية الافتراضية */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* خلفية التطبيق */
    .stApp {
        background-color: #ffffff;
        direction: rtl; 
    }

    /* --- الشريط العلوي (Navbar) --- */
    .navbar {
        background-color: #f8f9fa; /* خلفية فاتحة */
        padding: 15px 30px;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        color: #333333; /* جعل النص أسود */
    }

    /* --- العناوين --- */
    .hero-title {
        text-align: center;
        color: #da2f2f; /* أحمر */
        font-size: 50px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        text-align: center;
        color: #333333; /* أسود */
        font-size: 22px;
        margin-bottom: 40px;
    }

    /* --- منطقة الرفع --- */
    div[data-testid="stFileUploader"] {
        background-color: #333; /* منطقة الرفع تظل غامقة لتبرز */
        padding: 40px;
        border-radius: 8px;
        text-align: center;
        max-width: 800px;
        margin: 0 auto;
    }
    /* جعل نص داخل منطقة الرفع أبيض لأنه على خلفية غامقة */
    div[data-testid="stFileUploader"] label {
        color: white; 
    }
    div[data-testid="stFileUploader"] .stMarkdown {
        color: #eee;
    }

    /* --- الزر --- */
    .stButton button {
        background-color: #da2f2f !important;
        color: white !important;
        font-size: 20px !important;
        padding: 10px 40px !important;
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
        margin-top: 80px;
        margin-bottom: 30px;
        color: #2c3e50; /* كحلي غامق */
        border-top: 2px solid #eee;
        padding-top: 40px;
    }
    .full-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid #eee;
        margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .full-card:hover {
        transform: translateY(-5px);
    }
    .card-img-container img {
        width: 100%;
        height: 250px !important; /* ارتفاع موحد */
        object-fit: cover;
    }
    .card-content {
        padding: 15px;
        text-align: center;
    }
    .person-name-title {
        font-size: 20px;
        font-weight: bold;
        color: #000; /* أسود */
        margin-bottom: 8px;
    }
    .dua-text-body {
        font-size: 15px;
        color: #444; /* رمادي غامق */
        line-height: 1.6;
        background-color: #f9fff9;
        padding: 10px;
        border-radius: 8px;
    }
    .final-footer {
        background-color: #333;
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        margin-top: 40px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. الهيكل العلوي (اللوجو) ---
# ملاحظة: تم تغيير الألوان للأسود لتظهر بوضوح
st.markdown("""
<div class="navbar" style="direction: ltr;">
    <div class="nav-logo" style="font-family: 'Cairo', sans-serif; display: flex; align-items: center; gap: 12px;">
        <div style="
            background: linear-gradient(135deg, #da2f2f, #b71c1c);
            color: white;
            width: 45px; height: 45px;
            border-radius: 10px;
            display: flex; justify-content: center; align-items: center;
            font-weight: 900; font-size: 26px;
            box-shadow: 0 4px 6px rgba(218, 47, 47, 0.3);
        ">
            عـ
        </div>
        <div style="display: flex; flex-direction: column; justify-content: center;">
             <span style="color: #000; font-size: 26px; font-weight: 900; line-height: 1;">عون</span>
             <span style="color: #555; font-size: 14px; font-weight: normal;">Awn Converter</span>
        </div>
    </div>
    
    <div style="color: #333; font-size: 16px; font-weight: bold;">
       ⬅️ افتح القائمة للسجل 
    </div>
</div>

<div class="hero-title">محوّل الملفات</div>
<div class="hero-subtitle">حوّل ملفاتك إلى أي صيغة (PDF) مجاناً</div>
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

                    # أمر التحويل
                    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                    output_path = os.path.join(work_dir, pdf_filename)

                    if os.path.exists(output_path):
                        st.success("✅ تم التحويل بنجاح!")
                        # إضافة للسجل
                        add_to_history(uploaded_file.name, "✅ تم التحويل")
                        
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

st.markdown("""
<div style="text-align: center; margin-top: 30px; color: #333;">
    <p style="font-weight: bold;">يدعم الموقع ملفات Word و Excel و PowerPoint</p>
    <p>سهل الاستخدام • مجاني 100% • آمن</p>
</div>
""", unsafe_allow_html=True)


# --- 7. قسم الصدقة الجارية ---

st.markdown('<h2 class="sadaqa-header">🤲 صدقة جارية ونسألكم الدعاء</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

# الكارت الأول (الجدة)
with col1:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container">
            <img src="1000479933.jpg" alt="جدتي">
        </div>
        <div class="card-content">
            <div class="person-name-title">جدتي (رحمها الله)</div>
            <div class="dua-text-body">
                اللهم ارحمها واغفر لها، واجعل قبرها روضة من رياض الجنة، وأسكنها الفردوس الأعلى بلا حساب.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# الكارت الثاني (محمود)
with col2:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container">
            <img src="1000479919.jpg" alt="محمود">
        </div>
        <div class="card-content">
            <div class="person-name-title">محمود (رحمه الله)</div>
            <div class="dua-text-body">
                اللهم اغفر له وارحمه، وعافه واعف عنه، وأكرم نزله، ووسع مدخله، ونقه من الخطايا كما ينقى الثوب الأبيض من الدنس.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# الكارت الثالث (أحمد)
with col3:
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container">
            <img src="1000479894.jpg" alt="أحمد">
        </div>
        <div class="card-content">
            <div class="person-name-title">أحمد (عريس الجنة)</div>
            <div class="dua-text-body">
                اللهم إنه في ذمتك، فقه فتنة القبر وعذاب النار. اللهم عوض شبابه في الجنة، واجعله من الضاحكين المستبشرين.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# التذييل
st.markdown("""
<div class="final-footer">
    هذا الموقع خالص لوجه الله وصدقة جارية
</div>
""", unsafe_allow_html=True)

