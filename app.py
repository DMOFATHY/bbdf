import streamlit as st
import subprocess
import os
import shutil
import sqlite3
import hashlib
from datetime import datetime

# ---------------------------------------------------------
# 1. إعداد قاعدة البيانات (Database Setup)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # جدول السجل
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (username TEXT, filename TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    data = c.fetchone()
    conn.close()
    return data

def add_to_history(username, filename):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO history VALUES (?, ?, ?)", (username, filename, date_now))
    conn.commit()
    conn.close()

def get_history(username):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT filename, date FROM history WHERE username=? ORDER BY date DESC", (username,))
    data = c.fetchall()
    conn.close()
    return data

# تشغيل قاعدة البيانات عند البدء
init_db()

# ---------------------------------------------------------
# 2. واجهة التطبيق (UI)
# ---------------------------------------------------------
st.set_page_config(page_title="المحول الشامل", page_icon="🎓", layout="wide")

# حالة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = 'Guest'

# --- القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.title("👤 الحساب")
    
    if st.session_state['logged_in']:
        st.success(f"مرحباً, {st.session_state['username']}! 👋")
        
        st.divider()
        st.subheader("📜 سجلك السابق")
        history = get_history(st.session_state['username'])
        if history:
            for item in history:
                st.text(f"📅 {item[1]}\n📄 {item[0]}")
                st.markdown("---")
        else:
            st.caption("لم تقم بتحويل ملفات بعد.")
            
        if st.button("تسجيل خروج"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = 'Guest'
            st.rerun()
            
    else:
        st.info("💡 يمكنك التحويل كزائر، أو تسجيل الدخول لحفظ سجلك.")
        choice = st.selectbox("اختر:", ["زائر (Guest)", "تسجيل دخول", "إنشاء حساب جديد"])
        
        if choice == "تسجيل دخول":
            user = st.text_input("اسم المستخدم")
            pw = st.text_input("كلمة المرور", type="password")
            if st.button("دخول"):
                if check_login(user, pw):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = user
                    st.success("تم الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("بيانات خاطئة")
                    
        elif choice == "إنشاء حساب جديد":
            new_user = st.text_input("اختر اسم مستخدم")
            new_pw = st.text_input("اختر كلمة مرور", type="password")
            if st.button("تسجيل حساب"):
                if add_user(new_user, new_pw):
                    st.success("تم إنشاء الحساب! يمكنك تسجيل الدخول الآن.")
                else:
                    st.error("اسم المستخدم مأخوذ سابقاً.")

# --- الصفحة الرئيسية (Main Page) ---
st.title("🎓 محول الملفات (صدقة جارية)")
st.write("تحويل المستندات إلى PDF مجاناً وبلا حدود.")

if st.session_state['logged_in']:
    st.caption(f"أنت تستخدم الموقع الآن بصفتك: **{st.session_state['username']}**")
else:
    st.caption("أنت تستخدم الموقع بصفتك: **زائر**")

st.divider()

uploaded_file = st.file_uploader("ارفع ملفك (Word, PowerPoint, Excel)", type=['docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls'])

if uploaded_file is not None:
    if st.button("تحويل الملف 🚀"):
        with st.spinner('جاري التحويل...'):
            try:
                # إنشاء مجلد مؤقت
                work_dir = "temp_gen"
                if not os.path.exists(work_dir):
                    os.makedirs(work_dir)
                
                safe_filename = uploaded_file.name.replace(" ", "_")
                input_path = os.path.join(work_dir, safe_filename)
                
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # التحويل
                cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir]
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                pdf_filename = os.path.splitext(safe_filename)[0] + ".pdf"
                output_path = os.path.join(work_dir, pdf_filename)

                if os.path.exists(output_path):
                    st.balloons() # احتفال بسيط بالنجاح
                    st.success("✅ تم التحويل بنجاح!")
                    
                    # لو عضو مسجل، نحفظ في السجل
                    if st.session_state['logged_in']:
                        add_to_history(st.session_state['username'], uploaded_file.name)
                    
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 تحميل الـ PDF",
                            data=f,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                else:
                    st.error("فشل التحويل.")
                
                shutil.rmtree(work_dir)

            except Exception as e:
                st.error(f"حدث خطأ: {e}")
