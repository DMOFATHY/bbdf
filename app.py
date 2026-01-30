import streamlit as st
import subprocess
import os
import shutil

# --- إعداد الصفحة وتنسيق الاتجاه (RTL) ---
st.set_page_config(page_title="المحول المجاني + صدقة جارية", page_icon="🤲", layout="wide") # استخدام layout="wide" لمساحة أكبر للكروت

# إضافة CSS لجعل النصوص عربية ومنسقة وشكل الكروت الأفقية
st.markdown("""
<style>
    /* تحويل الاتجاه لليمين */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    
    /* تنسيق الكارت الكامل (الصورة + النص) */
    .full-card {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        overflow: hidden; /* لضمان انحناء الصورة مع الكارت */
        margin-bottom: 20px;
        border: 1px solid #eee;
        height: 100%; /* محاولة لجعل الكروت بنفس الطول */
        display: flex;
        flex-direction: column;
    }

    /* تنسيق الصورة داخل الكارت */
    .card-img-container img {
        width: 100%;
        height: 250px !important; /* ارتفاع ثابت للصور لتكون مربعة/متناسقة */
        object-fit: cover; /* لملء الإطار دون مط الصورة */
        border-bottom: 3px solid #28a745;
    }

    /* تنسيق المحتوى النصي داخل الكارت */
    .card-content {
        padding: 15px;
        text-align: center;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .person-name-title {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
    }

    .dua-text-body {
        font-size: 16px;
        color: #555;
        line-height: 1.6;
        background-color: #f9fff9;
        padding: 10px;
        border-radius: 8px;
    }

    /* تنسيق الجملة الختامية */
    .final-footer {
        text-align: center;
        margin-top: 40px;
        padding: 20px;
        background-color: #28a745;
        color: white;
        font-size: 22px;
        font-weight: bold;
        border-radius: 10px;
    }
    
    /* تنسيق العناوين */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- الجزء الأول: محول الملفات ---
st.title("📄 محول الملفات (مجاني 100%)")
st.write("حول ملفات Word و Excel و PowerPoint إلى PDF بسهولة.")

uploaded_file = st.file_uploader("اختر الملف", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])

if uploaded_file is not None:
    if st.button("تحويل الآن 🚀"):
        with st.spinner('جاري التحويل... (قد يستغرق لحظات)'):
            try:
                work_dir = "temp_convert"
                if not os.path.exists(work_dir):
                    os.makedirs(work_dir)
                
                safe_filename = uploaded_file.name.replace(" ", "_")
                input_path = os.path.join(work_dir, safe_filename)
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # أمر التحويل (يتطلب وجود LibreOffice)
                cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                output_path = os.path.join(work_dir, pdf_filename)

                if os.path.exists(output_path):
                    st.success("✅ تم التحويل بنجاح!")
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 تحميل ملف PDF",
                            data=f,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                else:
                    st.error("فشل التحويل. تأكد أن الملف غير تالف.")
                
                shutil.rmtree(work_dir)

            except Exception as e:
                st.error(f"حدث خطأ: {e}")

st.markdown("---") # فاصل خطي

# --- الجزء الثاني: صدقة جارية (الكروت المتجاورة) ---

st.header("🤲 صدقة جارية ونسألكم الدعاء")

# إنشاء 3 أعمدة متجاورة
col1, col2, col3 = st.columns(3, gap="medium")

# --- الكارت الأول (الجدة) ---
with col1:
    # نستخدم HTML مباشر لدمج الصورة والنص في كارت واحد متماسك
    st.markdown("""
    <div class="full-card">
        <div class="card-img-container">
            <img src="1000479933.jpg" alt="جدتي">
        </div>
        <div class="card-content">
            <div class="person-name-title">جدتي (رحمها الله)</div>
            <div class="dua-text-body">
                اللهم ارحمها واغفر لها، واجعل قبرها روضة من رياض الجنة، وأسكنها الفردوس الأعلى بلا حساب ولا سابق عذاب.
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
                اللهم إنه في ذمتك وحبل جوارك، فقه فتنة القبر وعذاب النار. اللهم عوض شبابه في الجنة، واجعله من الضاحكين المستبشرين.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- الجملة الختامية ---
st.markdown("""
<div class="final-footer">
    هذا الموقع خالص لوجه الله وصدقة جارية
</div>
""", unsafe_allow_html=True)
