import streamlit as st
import subprocess
import os
import shutil

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="محول الملفات - Convertio Style", page_icon="📂", layout="wide")

# --- 2. التصميم (CSS) لمحاكاة الصورة ---
st.markdown("""
<style>
    /* استيراد خط جميل (Cairo) */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    /* إخفاء القائمة الجانبية الافتراضية وشريط الهيدر الخاص بـ Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    
    /* تنسيق الخلفية */
    .stApp {
        background-color: #ffffff;
        direction: rtl; 
    }

    /* --- الشريط العلوي (Navbar) --- */
    .navbar {
        background-color: #333333;
        padding: 15px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        color: white;
        font-size: 20px;
        font-weight: bold;
    }
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .convertio-logo {
        color: #fff;
        font-size: 24px;
        font-weight: 900;
    }
    .red-icon {
        color: #e53935;
        font-size: 28px;
    }

    /* --- النصوص الرئيسية (Hero Section) --- */
    .hero-title {
        text-align: center;
        color: #da2f2f; /* اللون الأحمر المميز */
        font-size: 50px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        text-align: center;
        color: #555;
        font-size: 22px;
        margin-bottom: 40px;
    }

    /* --- تنسيق زر الرفع والزر الأساسي --- */
    /* محاولة صبغ زر الرفع باللون الأحمر */
    .stFileUploader label {
        display: none; /* إخفاء النص الصغير الافتراضي */
    }
    div[data-testid="stFileUploader"] {
        background-color: #333; /* خلفية داكنة لمنطقة الرفع */
        padding: 40px;
        border-radius: 8px;
        text-align: center;
        max-width: 800px;
        margin: 0 auto;
    }
    /* تنسيق زر "تحويل الآن" */
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

    /* --- تنسيق كروت الصدقة الجارية (كما طلب سابقاً) --- */
    .sadaqa-header {
        text-align: center;
        margin-top: 80px;
        margin-bottom: 30px;
        color: #2c3e50;
        border-top: 2px solid #eee;
        padding-top: 40px;
    }
    .full-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid #f0f0f0;
        margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .full-card:hover {
        transform: translateY(-5px);
    }
    .card-img-container img {
        width: 100%;
        height: 300px !important;
        object-fit: cover;
    }
    .card-content {
        padding: 20px;
        text-align: center;
    }
    .person-name-title {
        font-size: 22px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .dua-text-body {
        font-size: 16px;
        color: #666;
        line-height: 1.7;
        background-color: #fafafa;
        padding: 15px;
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

# --- 3. الهيكل العلوي (HTML) ---
st.markdown("""
<div class="navbar">
    <div class="nav-logo">
        <span class="red-icon">⚡</span>
        <span class="convertio-logo">Convertio Clone</span>
    </div>
    <div>☰</div>
</div>

<div class="hero-title">محوّل الملفات</div>
<div class="hero-subtitle">حوّل ملفاتك إلى أي صيغة (PDF)</div>
""", unsafe_allow_html=True)

# --- 4. منطق التطبيق (Python) ---

# وضعنا رفع الملفات داخل حاوية لتنسيقها
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
                        st.success("✅ تم التحويل!")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 تنزيل الملف (PDF)",
                                data=f,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                    else:
                        st.error("فشل التحويل. تأكد من سلامة الملف.")
                    
                    shutil.rmtree(work_dir)

                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

# نص إضافي تحت الزر مثل الصورة
st.markdown("""
<div style="text-align: center; margin-top: 30px; color: #888;">
    <p>يدعم الموقع ملفات Word و Excel و PowerPoint</p>
    <p>سهل الاستخدام • مجاني 100% • آمن</p>
</div>
""", unsafe_allow_html=True)


# --- 5. قسم الصدقة الجارية ---

st.markdown('<h2 class="sadaqa-header">🤲 صدقة جارية ونسألكم الدعاء</h2>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

# --- الكارت الأول (الجدة) ---
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

# --- الكارت الثاني (محمود) ---
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

# --- الكارت الثالث (أحمد) ---
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

