import streamlit as st
import subprocess
import os
import shutil

# --- إعداد الصفحة وتنسيق الاتجاه (RTL) ---
st.set_page_config(page_title="المحول المجاني + صدقة جارية", page_icon="🤲", layout="centered")

# إضافة CSS لجعل النصوص عربية ومنسقة وشكل الكروت
st.markdown("""
<style>
    /* تحويل الاتجاه لليمين */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    /* تنسيق كارت الدعاء */
    .dua-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border-right: 5px solid #28a745;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        text-align: center;
    }
    .dua-text {
        font-size: 18px;
        color: #333;
        line-height: 1.8;
        margin-top: 10px;
    }
    .person-name {
        font-size: 22px;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 10px;
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

# --- الجزء الثاني: صدقة جارية (الصور والدعاء) ---

st.header("🤲 صدقة جارية ونسألكم الدعاء")

# دالة مساعدة لعرض الكارت
def show_dua_card(image_file, name, dua_text):
    try:
        # عرض الصورة
        st.image(image_file, use_container_width=True)
        # عرض النص والدعاء داخل تصميم كارت
        st.markdown(f"""
        <div class="dua-card">
            <div class="person-name">{name}</div>
            <div class="dua-text">{dua_text}</div>
        </div>
        """, unsafe_allow_html=True)
    except:
        st.warning(f"الصورة {image_file} غير موجودة، يرجى التأكد من رفعها.")

# 1. الجدة
show_dua_card(
    "1000479933.jpg",
    "المغفور لها بإذن الله (جدتي)",
    "اللهم ارحمها واغفر لها، واجعل قبرها روضة من رياض الجنة، ولا تجعله حفرة من حفر النار. اللهم أسكنها الفردوس الأعلى بلا حساب."
)

# 2. محمود
show_dua_card(
    "1000479919.jpg",
    "المغفور له بإذن الله (محمود)",
    "اللهم اغفر له وارحمه، وعافه واعف عنه، وأكرم نزله، ووسع مدخله، ونقه من الخطايا كما ينقى الثوب الأبيض من الدنس."
)

# 3. أحمد
show_dua_card(
    "1000479894.jpg",
    "عريس الجنة (أحمد)",
    "اللهم إنه في ذمتك وحبل جوارك، فقه فتنة القبر وعذاب النار. اللهم عوض شبابه في الجنة، واجعله من الضاحكين المستبشرين."
)

# تذييل الصفحة
st.markdown("<div style='text-align: center; margin-top: 50px; color: #888;'>اللهم تقبل منا ومنكم صالح الأعمال</div>", unsafe_allow_html=True)
