import streamlit as st
import subprocess
import os
import shutil

# إعداد الصفحة
st.set_page_config(page_title="المحول المجاني", page_icon="📄")

# العنوان
st.title("📄 محول الملفات (تطوير محمد فتحي ابو الجيلاني ")
st.write("حول ملفات Word و Excel و PowerPoint إلى PDF بدون حدود وبدون إنترنت")

# رفع الملف
uploaded_file = st.file_uploader("اختر الملف", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])

if uploaded_file is not None:
    if st.button("تحويل الآن 🚀"):
        with st.spinner('جاري التحويل باستخدام LibreOffice...'):
            try:
                # إنشاء مجلد مؤقت
                work_dir = "temp_convert"
                if not os.path.exists(work_dir):
                    os.makedirs(work_dir)
                
                # حفظ الملف المرفوع (مع استبدال المسافات لتجنب الأخطاء)
                safe_filename = uploaded_file.name.replace(" ", "_")
                input_path = os.path.join(work_dir, safe_filename)
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # أمر التحويل باستخدام LibreOffice
                cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # النتيجة
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
                    st.text(process.stderr.decode())

                # تنظيف
                shutil.rmtree(work_dir)

            except Exception as e:
                st.error(f"حدث خطأ: {e}")
