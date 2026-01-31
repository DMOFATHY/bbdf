import streamlit as st
import subprocess
import os
import shutil
import uuid
import json
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pandas as pd
import time

# =======================
# 📧 إعدادات البريد الإلكتروني (تم التجهيز)
# =======================
SENDER_EMAIL = "Dmofathy@gmail.com"
SENDER_PASSWORD = "fxns iuta umlu fprn"

def send_email_otp(receiver_email, otp_code):
    """دالة لإرسال الكود عبر الإيميل"""
    msg = MIMEText(f"""
    مرحباً بك في موقع عون 🤲
    
    كود التفعيل الخاص بك هو: {otp_code}
    
    هذا الكود صالح لمرة واحدة للتسجيل في الموقع.
    """, 'plain', 'utf-8')
    
    msg['Subject'] = "كود تفعيل حساب عون - Awn App"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email

    try:
        # الاتصال بسيرفر جيميل
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# =======================
# 1. إعداد الصفحة والستايل
# =======================
st.set_page_config(page_title="عون - صدقة جارية", page_icon="🤲", layout="centered")

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    
    /* تنسيق صندوق الصدقة الجارية */
    .dedication-box {
        background-color: #f0fdf4; 
        border: 2px solid #bbf7d0;
        color: #14532d;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .dua-text {
        font-family: 'Amiri', serif;
        font-size: 1.1rem;
        line-height: 1.8;
        margin-top: 10px;
    }
    .names-text {
        font-weight: bold;
        color: #15803d;
        font-size: 1.1rem;
    }

    .success-box {
        background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724;
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;
    }
    .locked-box {
        background-color: #fff3cd; border: 1px solid #ffeeba;
        color: #856404; padding: 15px; border-radius: 10px; text-align: center; margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. لافتة الصدقة الجارية
# =======================
st.markdown("""
<div class="dedication-box">
    <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">🤲 صدقة جارية</div>
    <p>هذا العمل صدقة جارية وموهوب ثوابه إلى أرواح المغفور لهم بإذن الله:</p>
    <p class="names-text">
        جدتي، والأستاذ/ أحمد أمجد، والأستاذ/ محمود جمال
    </p>
    <hr style="border-top: 1px solid #bbf7d0; margin: 10px 0;">
    <p class="dua-text">
        "اللهم اغفر لهم وارحمهم، وعافهم واعف عنهم، وأكرم نزلهم، ووسع مدخلهم، واجعل قبورهم روضة من رياض الجنة، ولا تجعلها حفرة من حفر النار. اللهم اجعل هذا العمل خالصاً لوجهك الكريم وانفع به الناس."
    </p>
</div>
""", unsafe_allow_html=True)

# =======================
# 3. إدارة البيانات والملفات
# =======================
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
TEMP_DIR = "temp_conversion"
ARCHIVE_DIR = "archive_files"

for d in [TEMP_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {} if filename == USERS_FILE else []
    return {} if filename == USERS_FILE else []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_log(email, name, filename, status, archived_path=None):
    logs = load_json(LOGS_FILE)
    if not isinstance(logs, list): logs = []
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "email": email, "name": name, "filename": filename,
        "status": status, "archived_path": archived_path
    }
    logs.insert(0, entry)
    save_json(LOGS_FILE, logs)

# إعداد الأدمن
users = load_json(USERS_FILE)
if "admin" not in users:
    users["admin"] = {
        "name": "Admin", "password": hash_pass("admin123"),
        "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"),
        "role": "admin", "blocked": False, "is_vip": True
    }
    save_json(USERS_FILE, users)

# =======================
# 4. دوال النظام
# =======================
def check_libreoffice():
    return shutil.which("libreoffice") or shutil.which("soffice")

def can_convert(email):
    users = load_json(USERS_FILE)
    user = users.get(email)
    if not user: return False, "غير موجود"
    if user.get("blocked", False): return False, "محظور"
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today
        save_json(USERS_FILE, users)
    
    if user["daily_used"] >= 5: return False, "انتهى الرصيد اليومي"
    return True, ""

def update_usage(email):
    users = load_json(USERS_FILE)
    if email in users:
        users[email]["daily_used"] += 1
        save_json(USERS_FILE, users)

# =======================
# 5. متغيرات الجلسة (Session)
# =======================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "pending_file" not in st.session_state: st.session_state.pending_file = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "reg_data" not in st.session_state: st.session_state.reg_data = {}

# =======================
# 6. نظام الدخول والتسجيل
# =======================
if not st.session_state.user_email:
    
    # رسالة التشويق (إذا كان هناك ملف تم تحويله)
    if st.session_state.pending_file:
        st.markdown(f"""
        <div class="locked-box">
            🔒 <b>تم تحويل الملف ({st.session_state.pending_file['name']}) بنجاح!</b><br>
            سجل دخولك أو أنشئ حساباً الآن لتحميله فوراً.
        </div>
        """, unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["تسجيل دخول", "حساب جديد (تفعيل بالإيميل)"])
    
    # --- تسجيل الدخول ---
    with tab_login:
        l_em = st.text_input("البريد الإلكتروني", key="l_em")
        l_pa = st.text_input("كلمة المرور", type="password", key="l_pa")
        if st.button("دخول", use_container_width=True):
            users = load_json(USERS_FILE)
            if l_em in users and users[l_em]["password"] == hash_pass(l_pa):
                st.session_state.user_email = l_em
                st.session_state.user_name = users[l_em].get("name", "")
                st.rerun()
            else: st.error("بيانات غير صحيحة")

    # --- إنشاء حساب جديد ---
    with tab_signup:
        if not st.session_state.otp_sent:
            # نموذج التسجيل
            with st.form("signup_form"):
                r_nm = st.text_input("الاسم الثلاثي")
                r_em = st.text_input("البريد الإلكتروني (Gmail)")
                r_pa = st.text_input("كلمة مرور قوية", type="password")
                submitted = st.form_submit_button("إرسال كود التفعيل 📨", use_container_width=True)
                
                if submitted:
                    users = load_json(USERS_FILE)
                    if r_em in users:
                        st.warning("هذا البريد مسجل بالفعل.")
                    elif "@gmail.com" not in r_em:
                        st.warning("يرجى استخدام بريد Gmail.")
                    elif not r_nm or not r_pa:
                        st.warning("يرجى ملء جميع البيانات.")
                    else:
                        code = str(random.randint(1000, 9999))
                        # محاولة الإرسال
                        with st.spinner("جاري إرسال الكود إلى بريدك..."):
                            if send_email_otp(r_em, code):
                                st.session_state.otp_code = code
                                st.session_state.otp_sent = True
                                st.session_state.reg_data = {"name": r_nm, "email": r_em, "pass": r_pa}
                                st.success(f"✅ تم إرسال الكود إلى {r_em}")
                                st.rerun()
                            else:
                                st.error("فشل إرسال الإيميل. تأكد من صحة الإيميل.")
        else:
            # نموذج تفعيل الكود
            st.info(f"📩 أدخل الكود المكون من 4 أرقام المرسل إلى: {st.session_state.reg_data['email']}")
            otp_in = st.text_input("كود التفعيل", max_chars=4, key="otp_val")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("تأكيد وإنشاء الحساب 🚀", use_container_width=True):
                    if otp_in == st.session_state.otp_code:
                        users = load_json(USERS_FILE)
                        d = st.session_state.reg_data
                        users[d["email"]] = {
                            "name": d["name"], "password": hash_pass(d["pass"]),
                            "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"),
                            "role": "user", "blocked": False, "is_vip": False
                        }
                        save_json(USERS_FILE, users)
                        
                        st.session_state.user_email = d["email"]
                        st.session_state.user_name = d["name"]
                        st.session_state.otp_sent = False
                        st.balloons()
                        st.success("تم إنشاء الحساب بنجاح!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("الكود غير صحيح ❌")
            with c2:
                if st.button("تغيير الإيميل / إلغاء", use_container_width=True):
                    st.session_state.otp_sent = False
                    st.session_state.otp_code = None
                    st.rerun()

# =======================
# 7. واجهة المستخدم (بعد الدخول)
# =======================
else:
    c1, c2 = st.columns([4, 1])
    with c1: st.success(f"أهلاً بك، **{st.session_state.user_name}**")
    with c2:
        if st.button("تسجيل خروج"):
            st.session_state.user_email = None; st.session_state.user_name = None; st.session_state.pending_file = None; st.rerun()

    # لوحة الأدمن
    users = load_json(USERS_FILE)
    if users.get(st.session_state.user_email, {}).get("role") == "admin":
        with st.expander("🛠️ لوحة الأدمن (بيانات المستخدمين)"):
            st.dataframe(pd.DataFrame(users).T.drop("password", axis=1))

# =======================
# 8. أداة التحويل
# =======================
st.markdown("### 📄 تحويل الملفات إلى PDF")

if not check_libreoffice():
    st.error("⚠️ خطأ: LibreOffice غير مثبت على السيرفر.")
    st.stop()

# حالة الملف المعلق (تم تحويله وينتظر التحميل)
if st.session_state.pending_file and st.session_state.user_email:
    p = st.session_state.pending_file
    if os.path.exists(p["path"]):
        st.markdown(f"<div class='success-box'>🎉 ملفك جاهز للتحميل: {p['name']}</div>", unsafe_allow_html=True)
        with open(p["path"], "rb") as f:
            st.download_button("⬇️ تحميل الملف PDF", f, file_name=p["pdf_name"], mime="application/pdf", type="primary", use_container_width=True)
        
        if st.button("تحويل ملف جديد"):
            update_usage(st.session_state.user_email)
            st.session_state.pending_file = None
            st.rerun()
    else:
        st.error("الملف غير موجود (ربما تم حذفه).")
        st.session_state.pending_file = None

# حالة الرفع العادية
else:
    if st.session_state.user_email:
        u = users[st.session_state.user_email].get('daily_used', 0)
        st.caption(f"استهلاكك اليومي: {u} / 5")
        
    up = st.file_uploader("ارفع الملف (Word, Excel, PPT)", type=["docx","doc","xlsx","xls","pptx","ppt"])
    
    if up and st.button("بدء التحويل 🚀", type="primary", use_container_width=True):
        # التحقق من الرصيد للمسجلين
        if st.session_state.user_email:
            ok, msg = can_convert(st.session_state.user_email)
            if not ok: st.error(msg); st.stop()
            
        with st.spinner("جاري التحويل..."):
            uid = str(uuid.uuid4())
            wd = os.path.join(TEMP_DIR, uid)
            os.makedirs(wd, exist_ok=True)
            ip = os.path.join(wd, up.name)
            with open(ip, "wb") as f: f.write(up.getbuffer())
            
            # الأرشفة
            ue = st.session_state.user_email if st.session_state.user_email else "Guest"
            un = st.session_state.user_name if st.session_state.user_name else "Unknown"
            arc = os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ue}_{up.name}")
            shutil.copy(ip, arc)
            
            try:
                subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                pn = up.name.rsplit(".", 1)[0] + ".pdf"
                pp = os.path.join(wd, pn)
                if os.path.exists(pp):
                    # حفظ الملف في الجلسة
                    st.session_state.pending_file = {"path": pp, "name": up.name, "pdf_name": pn}
                    add_log(ue, un, up.name, "نجاح", arc)
                    st.rerun()
                else: st.error("فشل التحويل.")
            except Exception as e: st.error(f"خطأ: {e}")

