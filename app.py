import streamlit as st
import subprocess
import os
import shutil
import uuid
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd

# --- 1. إعداد قاعدة البيانات (SQLite) ---
def init_db():
    conn = sqlite3.connect('awn_database.db')
    c = conn.cursor()
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # جدول سجل التحويلات
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  filename TEXT, 
                  convert_date TEXT)''')
    conn.commit()
    conn.close()

# دالة لتشفير كلمة المرور (أمان بسيط)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# دالة إضافة مستخدم
def add_user(username, password):
    conn = sqlite3.connect('awn_database.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# دالة تسجيل الدخول
def login_user(username, password):
    conn = sqlite3.connect('awn_database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    if data:
        if check_hashes(password, data[0][1]):
            return True
    return False

# دالة تسجيل عملية تحويل
def log_conversion(username, filename):
    conn = sqlite3.connect('awn_database.db')
    c = conn.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO history(username, filename, convert_date) VALUES (?,?,?)', 
              (username, filename, date_now))
    conn.commit()
    conn.close()

# دالة جلب سجل المستخدم
def get_user_history(username):
    conn = sqlite3.connect('awn_database.db')
    # تحميل البيانات مباشرة في DataFrame لعرضها كجدول
    df = pd.read_sql_query(f"SELECT filename, convert_date FROM history WHERE username = '{username}' ORDER BY id DESC", conn)
    conn.close()
    return df

# --- 2. إعداد الصفحة والتصميم ---
st.set_page_config(page_title="عون - محول الملفات", page_icon="🛠️", layout="wide")
init_db() # تشغيل قاعدة البيانات عند البدء

# CSS مخصص (نفس تصميم Convertio)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; }
    
    /* الهيدر */
    .navbar {
        background-color: #333; padding: 15px; display: flex; 
        justify-content: space-between; color: white; border-radius: 8px; margin-bottom: 20px;
    }
    .logo { font-size: 24px; font-weight: bold; }
    .logo span { background-color: #ff3b3b; padding: 2px 10px; border-radius: 50%; }

    /* الأزرار */
    div.stButton > button:first-child {
        background-color: #ff3b3b; color: white; border-radius: 5px; border: none;
        font-size: 18px; font-weight: bold; width: 100%;
    }
    div.stButton > button:first-child:hover { background-color: #d63030; color: white; }
    
    /* الجداول */
    .dataframe { width: 100% !important; text-align: right !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. إدارة الجلسة (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""

# --- 4. واجهة التطبيق ---

# === إذا لم يكن مسجلاً للدخول ===
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>مرحباً بك في عون 🛠️</h1>", unsafe_allow_html=True)
        choice = st.selectbox("اختر الإجراء", ["تسجيل الدخول", "إنشاء حساب جديد"])
        
        if choice == "تسجيل الدخول":
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type='password')
            if st.button("دخول"):
                if login_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
                    
        elif choice == "إنشاء حساب جديد":
            new_user = st.text_input("اختر اسم مستخدم")
            new_pass = st.text_input("اختر كلمة مرور", type='password')
            if st.button("تسجيل حساب"):
                if add_user(new_user, new_pass):
                    st.success("تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.")
                else:
                    st.warning("اسم المستخدم هذا موجود بالفعل.")

# === إذا تم تسجيل الدخول (الصفحة الرئيسية للمحول) ===
else:
    # الهيدر العلوي
    st.markdown(f"""
    <div class="navbar">
        <div class="logo"><span>🔁</span> عون</div>
        <div>مرحباً، {st.session_state['username']} | <a href="#" target="_self" style="color:#aaa; text-decoration:none;">تسجيل خروج (قم بتحديث الصفحة)</a></div>
    </div>
    """, unsafe_allow_html=True)
    
    # القائمة الجانبية (الإحصائيات)
    with st.sidebar:
        st.header(f"الملف الشخصي: {st.session_state['username']}")
        history_df = get_user_history(st.session_state['username'])
        conversion_count = len(history_df)
        
        st.metric(label="عدد الملفات المحولة", value=str(conversion_count))
        st.write("---")
        if st.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()

    # المحتوى الرئيسي (المحول)
    st.markdown('<h2 style="text-align: center;">محول الملفات <span style="color:#ff3b3b">السريع</span></h2>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("ارفع ملف Word, Excel, PowerPoint", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])

    if uploaded_file is not None:
        if st.button("تحويل الآن 🚀"):
            with st.spinner('جاري المعالجة...'):
                # إنشاء مسار مؤقت
                unique_id = str(uuid.uuid4())
                work_dir = os.path.join("temp_convert", unique_id)
                os.makedirs(work_dir, exist_ok=True)
                
                try:
                    # حفظ الملف
                    safe_filename = uploaded_file.name.replace(" ", "_")
                    input_path = os.path.join(work_dir, safe_filename)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # أمر التحويل (LibreOffice)
                    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                    output_path = os.path.join(work_dir, pdf_filename)

                    if os.path.exists(output_path):
                        # تسجيل العملية في قاعدة البيانات
                        log_conversion(st.session_state['username'], safe_filename)
                        
                        st.success("✅ تم التحويل بنجاح!")
                        with open(output_path, "rb") as f:
                            st.download_button("📥 تحميل PDF", f, file_name=pdf_filename, mime="application/pdf")
                        
                        # تحديث الصفحة لرؤية العداد يزيد (اختياري)
                        # st.rerun() 
                    else:
                        st.error("فشل التحويل.")
                
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
                finally:
                    if os.path.exists(work_dir):
                        shutil.rmtree(work_dir)

    # عرض سجل التحويلات أسفل الصفحة
    st.write("---")
    st.subheader("📋 سجل تحويلاتك السابقة")
    
    user_history = get_user_history(st.session_state['username'])
    
    if not user_history.empty:
        # تحسين عرض الجدول
        user_history.columns = ["اسم الملف", "تاريخ التحويل"]
        st.dataframe(user_history, use_container_width=True)
    else:
        st.info("لم تقم بأي عمليات تحويل حتى الآن.")

