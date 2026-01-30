import streamlit as st
import subprocess
import os
import shutil
import uuid
import base64

# --- إعداد الصفحة وتكوينها ---
st.set_page_config(page_title="عون - محول الملفات", page_icon="🛠️", layout="wide")

# --- دالة لحقن CSS (التصميم) ---
def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Cairo', sans-serif;
            direction: rtl;
        }
        
        /* إخفاء القوائم الافتراضية لستريم ليت */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* تنسيق الهيدر (الشريط العلوي) */
        .navbar {
            background-color: #333333;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            justify_content: space-between;
            color: white;
            margin-top: -60px; /* لرفع الشريط لأقصى الأعلى */
            margin-left: -5rem;
            margin-right: -5rem;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo-icon {
            background-color: #ff3b3b; /* أحمر */
            color: white;
            padding: 5px 10px;
            border-radius: 50%;
            font-size: 20px;
        }

        /* النصوص الرئيسية */
        .main-title {
            text-align: center;
            font-size: 40px;
            font-weight: 700;
            color: #333;
            margin-bottom: 10px;
        }
        
        .main-title span {
            color: #ff3b3b; /* اللون الأحمر */
        }
        
        .sub-title {
            text-align: center;
            font-size: 20px;
            color: #666;
            margin-bottom: 40px;
        }

        /* تنسيق منطقة الرفع لتشبه الشريط الرمادي في الصورة */
        .upload-container {
            background-color: #444444;
            padding: 60px;
            border-radius: 0;
            text-align: center;
            margin-left: -5rem;
            margin-right: -5rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        /* تعديل شكل أداة رفع الملفات الخاصة بستريم ليت */
        div[data-testid="stFileUploader"] {
            width: 60%;
            margin: 0 auto;
        }
        
        div[data-testid="stFileUploader"] section {
            background-color: #444; /* خلفية رمادية غامقة */
            border: none;
        }
        
        /* جعل زر الرفع أحمر وكبير */
        button[kind="secondary"] {
            background-color: #ff3b3b !important;
            color: white !important;
            border: none !important;
            font-size: 20px !important;
            padding: 15px 40px !important;
            width: 100% !important;
            border-radius: 5px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: 0.3s;
        }
        
        button[kind="secondary"]:hover {
            background-color: #d63030 !important;
        }

        /* أيقونة التحميل */
        .convert-btn {
            background-color: #333;
            color: white;
            font-size: 18px;
            padding: 10px 30px;
            border-radius: 5px;
            border: 1px solid #333;
            cursor: pointer;
        }

        /* منطقة الإحصائيات أسفل الصفحة */
        .stats-area {
            text-align: center;
            margin-top: 50px;
            color: #777;
        }
        
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- الهيدر (الشريط العلوي) ---
st.markdown("""
<div class="navbar">
    <div class="logo">
        <span class="logo-icon">🔁</span>
        عون
    </div>
    <div style="font-size: 14px;">تسجيل الدخول | اشتراك</div>
</div>
""", unsafe_allow_html=True)

# --- النصوص الرئيسية ---
st.markdown('<div class="main-title">محوّل <span>الملفات</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">حوّل ملفاتك إلى أي صيغة (PDF)</div>', unsafe_allow_html=True)

# --- منطقة العمل (الرفع والتحويل) ---
# نضعها داخل كونتينر لتنسيق الخلفية الرمادية
with st.container():
    st.write("---") # خط فاصل وهمي لبدء المنطقة الداكنة (CSS يعالج الباقي)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # رفع الملف
        uploaded_file = st.file_uploader("اختر الملفات", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'], label_visibility="collapsed")

# --- منطق التحويل (Backend Logic) ---
if uploaded_file is not None:
    st.markdown(f"<h3 style='text-align: center; color: #333;'>تم اختيار الملف: {uploaded_file.name}</h3>", unsafe_allow_html=True)
    
    # زر التحويل بتصميم مخصص
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c2:
        start_convert = st.button("تحويل الآن 🚀", type="primary", use_container_width=True)

    if start_convert:
        with st.spinner('جاري التحويل...'):
            unique_id = str(uuid.uuid4())
            work_dir = os.path.join("temp_convert", unique_id)
            
            try:
                if not os.path.exists(work_dir):
                    os.makedirs(work_dir)
                
                safe_filename = uploaded_file.name.replace(" ", "_")
                input_path = os.path.join(work_dir, safe_filename)
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # LibreOffice Command
                cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                output_path = os.path.join(work_dir, pdf_filename)

                if os.path.exists(output_path):
                    st.success("✅ جاهز للتحميل!")
                    
                    with open(output_path, "rb") as f:
                        pdf_data = f.read()

                    st.download_button(
                        label="📥 تنزيل الملف (PDF)",
                        data=pdf_data,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("عفواً، حدث خطأ أثناء التحويل.")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
            finally:
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir)

# --- الفوتر (أسفل الصفحة) ---
st.markdown("""
<div class="stats-area">
    <div style="font-size: 30px;">🔄</div>
    <h3>يدعم الموقع تحويل ملفات Office</h3>
    <p>Word, Excel, PowerPoint إلى PDF بسرعة عالية ومجاناً</p>
</div>
""", unsafe_allow_html=True)
