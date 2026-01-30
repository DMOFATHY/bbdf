import streamlit as st
import subprocess
import os
import shutil
from pathlib import Path

# ===================== إعدادات عامة =====================
APP_TITLE = "📄 محول الملفات إلى PDF"
APP_DESCRIPTION = "تحويل ملفات Word وExcel وPowerPoint إلى PDF مجانًا وبدون إنترنت"
DEVELOPER = "تطوير: محمد فتحي أبو الجيلاني"
WORK_DIR = Path("temp_convert")
ALLOWED_TYPES = ['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls']


# ===================== إعداد الصفحة =====================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📄",
    layout="centered"
)

st.title(APP_TITLE)
st.caption(DEVELOPER)
st.write(APP_DESCRIPTION)
st.divider()


# ===================== دوال مساعدة =====================
def create_work_dir():
    WORK_DIR.mkdir(exist_ok=True)


def clean_work_dir():
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)


def convert_to_pdf(input_path: Path) -> Path | None:
    """تحويل ملف إلى PDF باستخدام LibreOffice"""
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        str(input_path),
        "--outdir",
        str(WORK_DIR)
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    pdf_path = WORK_DIR / (input_path.stem + ".pdf")
    return pdf_path if pdf_path.exists() else None


# ===================== واجهة المستخدم =====================
uploaded_file = st.file_uploader(
    "📤 اختر ملف للتحويل",
    type=ALLOWED_TYPES,
    help="الصيغ المدعومة: Word / Excel / PowerPoint"
)

if uploaded_file:
    st.info(f"📄 الملف المختار: **{uploaded_file.name}**")

    if st.button("🚀 تحويل إلى PDF", use_container_width=True):
        with st.spinner("⏳ جاري التحويل باستخدام LibreOffice..."):
            try:
                create_work_dir()

                safe_name = uploaded_file.name.replace(" ", "_")
                input_path = WORK_DIR / safe_name

                # حفظ الملف
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # التحويل
                pdf_path = convert_to_pdf(input_path)

                if pdf_path:
                    st.success("✅ تم التحويل بنجاح!")

                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="📥 تحميل ملف PDF",
                            data=pdf_file,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.error("❌ فشل التحويل. تأكد من سلامة الملف.")

            except Exception as e:
                st.error("⚠️ حدث خطأ غير متوقع")
                st.code(str(e))

            finally:
                clean_work_dir()


# ===================== الفوتر =====================
st.divider()
st.caption("© 2026 - محول ملفات PDF | يعمل محليًا بدون إنترنت")
