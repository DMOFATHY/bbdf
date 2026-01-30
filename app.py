import streamlit as st
import subprocess
import os
import shutil
import sqlite3
import hashlib
import time
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة والتصميم (UI/UX)
# ==========================================
st.set_page_config(page_title="المحول المتقدم للمستندات", page_icon="📄", layout="centered")

# دمج ملفات CSS لتطبيق ألوان الأزرق والأخضر (Deep Blue & Soft Green)
st.markdown("""
<style>
    /* الخلفية والخطوط */
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* العناوين */
    h1, h2, h3 {
        color: #1a3c5e; /* Deep Blue */
    }
    
    /* الأزرار */
    div.stButton > button {
        background-color: #1a3c5e;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: 0.3s;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #4CAF50; /* Soft Green Accent */
        color: white;
    }
    
    /* الكروت (Cards) */
    .css-1y4p8pa {
        padding: 2rem;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* الرسائل */
    .success-msg {
        color: #4CAF50;
        font-weight: bold;
    }
    
    /* القائمة الجانبية */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات والأمان (Backend)
# ==========================================
def init_db():
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, join_date TEXT)''')
    # جدول السجل
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, filename TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", 
                  (username, hash_password(password), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate(username, password):
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def log_history(username, filename):
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (username, filename, date) VALUES (?, ?, ?)", 
              (username, filename, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_user_history(username):
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    c.execute("SELECT filename, date FROM history WHERE username=? ORDER BY id DESC", (username,))
    data = c.fetchall()
    conn.close()
    return data

def get_global_stats():
    conn = sqlite3.connect('app_data.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM history")
    count = c.fetchone()[0]
    conn.close()
    return count

init_db()

# ==========================================
# 3. إدارة الجلسة (Session State)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = 'Guest'
    st.session_state.guest_conversions = 0
    st.session_state.first_visit = True

# ==========================================
# 4. رسالة الصدقة الجارية (تظهر مرة واحدة)
# ==========================================
if st.session_state.first_visit:
    st.info("🕊️ **صدقة جارية:** نسألكم الدعاء بالرحمة والمغفرة لجدتي ولموتى المسلمين.")
    st.session_state.first_visit = False

# ==========================================
# 5. القائمة الجانبية (Sidebar)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=80)
    st.title("لوحة التحكم")
    
    if st.session_state.logged_in:
        st.success(f"مرحباً, {st.session_state.username}")
        st.markdown("---")
        
        # الملف الشخصي والسجل
        st.subheader("📂 سجل تحويلاتك")
        history = get_user_history(st.session_state.username)
        if history:
            for item in history[:5]: # عرض آخر 5 فقط
                st.caption(f"📄 {item[0]} | 🕒 {item[1]}")
            if len(history) > 5:
                st.caption("... والمزيد")
        else:
            st.info("لا يوجد تحويلات سابقة.")
            
        st.markdown("---")
        if st.button("تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.username = 'Guest'
            st.rerun()
            
    else:
        # نظام الدخول للزوار
        st.warning("أنت تستخدم وضع الزائر (محاولتان فقط)")
        st.markdown(f"**المتبقي:** {2 - st.session_state.guest_conversions}")
        
        st.markdown("---")
        auth_mode = st.radio("خيارات الحساب", ["تسجيل الدخول", "حساب جديد"])
        
        user_input = st.text_input("اسم المستخدم")
        pass_input = st.text_input("كلمة المرور", type="password")
        
        if auth_mode == "تسجيل الدخول":
            if st.button("دخول"):
                if authenticate(user_input, pass_input):
                    st.session_state.logged_in = True
                    st.session_state.username = user_input
                    st.success("تم الدخول!")
                    st.rerun()
                else:
                    st.error("بيانات خاطئة")
        else:
            if st.button("إنشاء حساب"):
                if user_input and pass_input:
                    if register_user(user_input, pass_input):
                        st.success("تم إنشاء الحساب! سجل دخولك الآن.")
                    else:
                        st.error("اسم المستخدم مأخوذ.")
                else:
                    st.error("الرجاء ملء البيانات")

    st.markdown("---")
    st.caption(f"📊 إجمالي الملفات المحولة عالمياً: {get_global_stats()}")
    st.caption("v2.0 | Developed for Charity")

# ==========================================
# 6. الواجهة الرئيسية (Conversion Card)
# ==========================================
st.title("تحويل المستندات إلى PDF")
st.markdown("حول ملفات **Word, Excel, PowerPoint** بسرعة وأمان.")

# الكارد الرئيسي
with st.container():
    uploaded_file = st.file_uploader(
        "اسحب الملف هنا أو اضغط للاختيار", 
        type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls']
    )

    if uploaded_file:
        st.write(f"**الملف المختار:** {uploaded_file.name}")
        
        # التحقق من الصلاحيات (Guest Limit Check)
        can_convert = True
        if not st.session_state.logged_in:
            if st.session_state.guest_conversions >= 2:
                can_convert = False
                st.error("🔒 لقد استنفدت المحاولات المجانية للزائر.")
                st.info("قم بإنشاء حساب مجاني (من القائمة الجانبية) للتمتع بتحويلات غير محدودة وحفظ السجل.")

        if can_convert:
            if st.button("ابدأ التحويل 🚀"):
                with st.spinner('جاري المعالجة والتحويل...'):
                    try:
                        # 1. إعداد المجلدات
                        work_dir = "temp_work"
                        if not os.path.exists(work_dir):
                            os.makedirs(work_dir)
                        
                        # 2. حفظ الملف
                        safe_filename = uploaded_file.name.replace(" ", "_")
                        input_path = os.path.join(work_dir, safe_filename)
                        with open(input_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # 3. التحويل بـ LibreOffice
                        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                        # 4. النتيجة
                        pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                        output_path = os.path.join(work_dir, pdf_filename)

                        if os.path.exists(output_path):
                            st.success("✅ تم التحويل بنجاح!")
                            
                            # تحديث العدادات والسجل
                            if not st.session_state.logged_in:
                                st.session_state.guest_conversions += 1
                            else:
                                log_history(st.session_state.username, uploaded_file.name)
                            
                            # زر التحميل
                            with open(output_path, "rb") as f:
                                st.download_button(
                                    label="📥 تحميل ملف PDF",
                                    data=f,
                                    file_name=pdf_filename,
                                    mime="application/pdf"
                                )
                        else:
                            st.error("حدث خطأ أثناء التحويل.")
                        
                        # تنظيف
                        shutil.rmtree(work_dir)

                    except Exception as e:
                        st.error(f"خطأ غير متوقع: {e}")
