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
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

# =======================
# 📧 إعدادات البريد
# =======================
SENDER_EMAIL = "Dmofathy@gmail.com"
SENDER_PASSWORD = "fxns iuta umlu fprn"

def send_email_otp(receiver_email, otp_code):
    msg = MIMEText(f"كود التفعيل الخاص بك في موقع عون: {otp_code}", 'plain', 'utf-8')
    msg['Subject'] = "كود تفعيل حساب عون"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(e)
        return False

# =======================
# 1. إعداد الصفحة
# =======================
st.set_page_config(page_title="عون - صدقة جارية", page_icon="🤲", layout="centered")

# التعامل مع "تذكرني"
if "token" not in st.session_state:
    st.session_state.token = st.query_params.get("token", None)

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    .features-banner {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        color: white; padding: 15px; border-radius: 10px;
        text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dedication-box {
        background-color: #f0fdf4; border: 2px solid #bbf7d0;
        color: #14532d; padding: 20px; border-radius: 12px;
        text-align: center; margin-bottom: 25px;
    }
    .auth-popup {
        background-color: #fff3cd; border: 2px solid #ffeeba;
        padding: 20px; border-radius: 15px; text-align: center;
        margin-top: 20px; color: #856404;
    }
    .success-box {
        background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724;
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. اللافتات
# =======================
st.markdown("""
<div class="features-banner">
    🚀 <b>أهلاً بك في عون!</b><br>
    👤 <b>الزائر:</b> تحويل ملف واحد مجاناً (مرتبط بالجهاز).<br>
    🌟 <b>المسجل:</b> 7 ملفات يومياً + حفظ السجلات.<br>
    ✅ <b>التسجيل اختياري ومجاني تماماً.</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="dedication-box">
    <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">🤲 صدقة جارية</div>
    <p>موهوب ثوابه إلى أرواح المغفور لهم بإذن الله:</p>
    <p style="font-weight:bold; color:#15803d;">جدتي، والأستاذ/ أحمد أمجد، والأستاذ/ محمود جمال</p>
    <p style="font-family:'Amiri'; font-size:1.1rem;">"اللهم اغفر لهم وارحمهم، وأكرم نزلهم، واجعل قبورهم روضة من رياض الجنة."</p>
</div>
""", unsafe_allow_html=True)

# =======================
# 3. إدارة الملفات والبيانات
# =======================
USERS_FILE = "users.json"
GUESTS_FILE = "guests.json" # ملف جديد لتخزين الـ IP
LOGS_FILE = "logs.json"
TOKENS_FILE = "tokens.json"
TEMP_DIR = "temp_conversion"
ARCHIVE_DIR = "archive_files"

for d in [TEMP_DIR, ARCHIVE_DIR]: os.makedirs(d, exist_ok=True)

def hash_pass(password): return hashlib.sha256(password.encode()).hexdigest()

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def add_log(email, name, filename, status, archived_path=None):
    logs = load_json(LOGS_FILE)
    if not isinstance(logs, list): logs = []
    entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "email": email, "name": name, "filename": filename, "status": status, "archived_path": archived_path}
    logs.insert(0, entry)
    save_json(LOGS_FILE, logs)

users = load_json(USERS_FILE)
if "admin" not in users:
    users["admin"] = {"name": "Admin", "password": hash_pass("admin123"), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "admin", "blocked": False, "is_vip": True}
    save_json(USERS_FILE, users)

def check_libreoffice(): return shutil.which("libreoffice") or shutil.which("soffice")

# --- دوال التعامل مع IP الزوار ---
def get_remote_ip():
    """محاولة الحصول على IP المستخدم"""
    try:
        ctx = get_script_run_ctx()
        if ctx is None: return "unknown"
        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info: return session_info.request.remote_ip
    except: return "unknown"
    return "unknown"

def check_guest_access(ip):
    """فحص هل الـ IP استهلك فرصته اليوم"""
    guests = load_json(GUESTS_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if ip in guests:
        data = guests[ip]
        if data["last_day"] != today:
            # يوم جديد، تصفير العداد
            guests[ip] = {"last_day": today, "used": 0}
            save_json(GUESTS_FILE, guests)
            return True # مسموح
        else:
            if data["used"] >= 1: # الحد الأقصى للزوار: 1
                return False # ممنوع
    return True # مسموح (أول مرة)

def record_guest_usage(ip):
    """تسجيل استخدام الزائر"""
    guests = load_json(GUESTS_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    if ip in guests:
        if guests[ip]["last_day"] == today:
            guests[ip]["used"] += 1
        else:
            guests[ip] = {"last_day": today, "used": 1}
    else:
        guests[ip] = {"last_day": today, "used": 1}
    save_json(GUESTS_FILE, guests)

# --- دوال المسجلين ---
def can_convert_member(email):
    users = load_json(USERS_FILE)
    user = users.get(email)
    if not user: return False, "غير موجود"
    if user.get("blocked", False): return False, "محظور"
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0; user["last_day"] = today; save_json(USERS_FILE, users)
    if user["daily_used"] >= 7: return False, "انتهى رصيدك اليومي (7 ملفات)"
    return True, ""

def update_usage_member(email):
    users = load_json(USERS_FILE)
    if email in users: users[email]["daily_used"] += 1; save_json(USERS_FILE, users)

# =======================
# 4. Session & Remember Me
# =======================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "pending_file" not in st.session_state: st.session_state.pending_file = None
if "show_auth_popup" not in st.session_state: st.session_state.show_auth_popup = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

# تذكرني
tokens = load_json(TOKENS_FILE)
url_token = st.query_params.get("auth_token", None)
if not st.session_state.user_email and url_token:
    for email, token_data in tokens.items():
        if token_data == url_token:
            users = load_json(USERS_FILE)
            if email in users:
                st.session_state.user_email = email
                st.session_state.user_name = users[email]["name"]
                st.toast(f"مرحباً {users[email]['name']}", icon="👋")

# =======================
# 5. الواجهة (Logic)
# =======================

# --- أ: المستخدم المسجل ---
if st.session_state.user_email:
    c1, c2 = st.columns([4, 1])
    with c1: st.success(f"👋 أهلاً بك، **{st.session_state.user_name}**")
    with c2:
        if st.button("خروج"):
            st.session_state.user_email = None; st.session_state.user_name = None
            st.query_params.clear()
            st.rerun()

    users = load_json(USERS_FILE)
    curr_user = users.get(st.session_state.user_email, {})
    is_admin = curr_user.get("role") == "admin"

    tabs_list = ["🏠 تحويل الملفات", "📜 سجل نشاطي", "⚙️ الإعدادات"]
    if is_admin: tabs_list.append("🛠️ لوحة الأدمن")
    main_tabs = st.tabs(tabs_list)

    # 1. التحويل (مسجل)
    with main_tabs[0]:
        if st.session_state.pending_file:
            p = st.session_state.pending_file
            if os.path.exists(p["path"]):
                st.markdown(f"<div class='success-box'>🎉 ملفك جاهز: {p['name']}</div>", unsafe_allow_html=True)
                with open(p["path"], "rb") as f:
                    st.download_button("⬇️ تحميل PDF", f, file_name=p["pdf_name"], mime="application/pdf", type="primary", use_container_width=True)
                if st.button("تحويل ملف آخر"):
                    update_usage_member(st.session_state.user_email)
                    st.session_state.pending_file = None
                    st.rerun()
        else:
            used = curr_user.get('daily_used', 0)
            st.info(f"رصيدك اليومي: {used} / 7 ملفات")
            up = st.file_uploader("ارفع ملف للتحويل", type=["docx","xlsx","pptx"])
            if up and st.button("تحويل 🚀", use_container_width=True):
                ok, msg = can_convert_member(st.session_state.user_email)
                if not ok: st.error(msg); st.stop()
                with st.spinner("جاري العمل..."):
                    uid = str(uuid.uuid4()); wd = os.path.join(TEMP_DIR, uid); os.makedirs(wd, exist_ok=True)
                    ip = os.path.join(wd, up.name); 
                    with open(ip, "wb") as f: f.write(up.getbuffer())
                    arc = os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{st.session_state.user_email}_{up.name}")
                    shutil.copy(ip, arc)
                    try:
                        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                        pn = up.name.rsplit(".", 1)[0] + ".pdf"; pp = os.path.join(wd, pn)
                        if os.path.exists(pp):
                            st.session_state.pending_file = {"path": pp, "name": up.name, "pdf_name": pn}
                            add_log(st.session_state.user_email, st.session_state.user_name, up.name, "نجاح", arc)
                            st.rerun()
                    except: st.error("فشل التحويل")

    # 2. السجل
    with main_tabs[1]:
        my_logs = [l for l in load_json(LOGS_FILE) if l.get('email') == st.session_state.user_email]
        if my_logs:
            df = pd.DataFrame(my_logs)[['timestamp', 'filename', 'status']]
            df.columns = ['التوقيت', 'اسم الملف', 'الحالة']
            st.dataframe(df, use_container_width=True)
        else: st.info("لا توجد سجلات")

    # 3. الإعدادات
    with main_tabs[2]:
        with st.form("change_pass"):
            st.write("تغيير كلمة المرور")
            o_p = st.text_input("القديمة", type="password")
            n_p = st.text_input("الجديدة", type="password")
            if st.form_submit_button("حفظ"):
                if hash_pass(o_p) == curr_user['password']:
                    users[st.session_state.user_email]['password'] = hash_pass(n_p)
                    save_json(USERS_FILE, users); st.success("تم التغيير")
                else: st.error("خطأ")

    # 4. الأدمن
    if is_admin:
        with main_tabs[3]:
            st.write("لوحة التحكم")
            st.dataframe(pd.DataFrame(users).T.drop("password", axis=1))

# --- ب: الزائر (Guest) ---
else:
    # 1. القوائم العلوية
    if not st.session_state.show_auth_popup:
        with st.expander("🔐 تسجيل الدخول / حساب جديد (للحصول على 7 تحويلات)", expanded=False):
            t_login, t_signup = st.tabs(["دخول", "جديد"])
            with t_login:
                l_e = st.text_input("الإيميل", key="top_l_e")
                l_p = st.text_input("الرمز", type="password", key="top_l_p")
                remember = st.checkbox("تذكرني", key="top_rem")
                if st.button("دخول", key="top_btn"):
                    users = load_json(USERS_FILE)
                    if l_e in users and users[l_e]["password"] == hash_pass(l_p):
                        st.session_state.user_email = l_e; st.session_state.user_name = users[l_e]["name"]
                        if remember:
                            token = str(uuid.uuid4()); tokens = load_json(TOKENS_FILE); tokens[l_e] = token; save_json(TOKENS_FILE, tokens)
                            st.query_params["auth_token"] = token
                        st.rerun()
                    else: st.error("خطأ")
            with t_signup:
                st.caption("التسجيل يتيح لك 7 ملفات يومياً.")

    st.markdown("### 📄 تحويل الملفات")
    
    # الحصول على IP الزائر
    visitor_ip = get_remote_ip()
    is_allowed = check_guest_access(visitor_ip)

    # 2. أداة التحويل للزائر
    # إذا كان محظوراً بسبب الـ IP (يعني حول بالفعل اليوم)
    if not is_allowed:
        st.warning(f"⚠️ لقد استهلكت فرصتك المجانية اليوم من هذا الجهاز. يرجى تسجيل الدخول للحصول على المزيد.")
        st.session_state.show_auth_popup = True
    else:
        # إذا كان مسموحاً له، ولم يتم تفعيل البوب أب
        if not st.session_state.show_auth_popup:
            up_guest = st.file_uploader("ارفع ملفك هنا (مسموح بملف واحد للزوار)", type=["docx","xlsx","pptx"])
            if up_guest:
                if st.button("تحويل 🚀", type="primary", use_container_width=True):
                    if not check_libreoffice(): st.error("LibreOffice Missing"); st.stop()
                    
                    with st.spinner("جاري المعالجة..."):
                        uid = str(uuid.uuid4()); wd = os.path.join(TEMP_DIR, uid); os.makedirs(wd, exist_ok=True)
                        ip = os.path.join(wd, up_guest.name); 
                        with open(ip, "wb") as f: f.write(up_guest.getbuffer())
                        arc = os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_Guest_{up_guest.name}")
                        shutil.copy(ip, arc)
                        try:
                            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                            pn = up_guest.name.rsplit(".", 1)[0] + ".pdf"; pp = os.path.join(wd, pn)
                            if os.path.exists(pp):
                                # نجاح التحويل
                                st.session_state.pending_file = {"path": pp, "name": up_guest.name, "pdf_name": pn}
                                # تسجيل استخدام الـ IP في الملف
                                record_guest_usage(visitor_ip)
                                # إظهار البوب أب
                                st.session_state.show_auth_popup = True 
                                st.session_state.guest_log = {"name": "Guest", "email": "Pending", "file": up_guest.name, "arc": arc}
                                st.rerun()
                            else: st.error("فشل التحويل.")
                        except Exception as e: st.error(f"Error: {e}")

    # 3. بوب أب التسجيل (يظهر بعد استخدام الفرصة أو إذا كان الـ IP مستهلك)
    if st.session_state.show_auth_popup:
        # عرض زر التحميل (إذا كان هناك ملف تم تحويله للتو)
        if st.session_state.pending_file:
            p = st.session_state.pending_file
            if os.path.exists(p["path"]):
                st.markdown(f"<div class='success-box'>✅ تم تحويل الملف: {p['name']}</div>", unsafe_allow_html=True)
                with open(p["path"], "rb") as f:
                    st.download_button("⬇️ تحميل الملف PDF", f, file_name=p["pdf_name"], mime="application/pdf", type="primary", use_container_width=True)

        st.markdown("""
        <div class="auth-popup">
            <h3>🛑 انتهت التجربة المجانية لهذا الجهاز</h3>
            <p>للاستمتاع بـ <b>7 ملفات يومياً</b>، يرجى التسجيل (مجاناً).</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            t1, t2 = st.tabs(["دخول", "حساب جديد"])
            with t1:
                l_em = st.text_input("الإيميل", key="btm_l_e")
                l_pa = st.text_input("الرمز", type="password", key="btm_l_p")
                rem_btm = st.checkbox("تذكرني", key="btm_rem")
                if st.button("دخول", use_container_width=True, key="btm_btn"):
                    users = load_json(USERS_FILE)
                    if l_em in users and users[l_em]["password"] == hash_pass(l_pa):
                        st.session_state.user_email = l_em; st.session_state.user_name = users[l_em]["name"]
                        if rem_btm:
                            token = str(uuid.uuid4()); tokens = load_json(TOKENS_FILE); tokens[l_em] = token; save_json(TOKENS_FILE, tokens)
                            st.query_params["auth_token"] = token
                        if "guest_log" in st.session_state:
                            g = st.session_state.guest_log; add_log(l_em, users[l_em]["name"], g["file"], "نجاح", g["arc"])
                        st.session_state.show_auth_popup = False
                        st.rerun()
                    else: st.error("خطأ")

            with t2:
                if not st.session_state.get("otp_sent", False):
                    with st.form("btm_signup"):
                        r_nm = st.text_input("الاسم"); r_em = st.text_input("الإيميل (Gmail)"); r_pa = st.text_input("كلمة مرور")
                        if st.form_submit_button("إرسال كود التفعيل 📨", use_container_width=True):
                            users = load_json(USERS_FILE)
                            if r_em in users: st.warning("مسجل")
                            elif "@gmail.com" not in r_em: st.warning("استخدم Gmail")
                            else:
                                code = str(random.randint(1000, 9999))
                                if send_email_otp(r_em, code):
                                    st.session_state.otp_code = code; st.session_state.otp_sent = True; st.session_state.reg_data = {"name": r_nm, "email": r_em, "pass": r_pa}
                                    st.rerun()
                else:
                    st.info(f"الكود: {st.session_state.reg_data['email']}")
                    otp_in = st.text_input("الكود", max_chars=4)
                    if st.button("تأكيد وإنشاء الحساب", use_container_width=True):
                        if otp_in == st.session_state.otp_code:
                            users = load_json(USERS_FILE); d = st.session_state.reg_data
                            users[d["email"]] = {"name": d["name"], "password": hash_pass(d["pass"]), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "user", "blocked": False, "is_vip": False}
                            save_json(USERS_FILE, users)
                            st.session_state.user_email = d["email"]; st.session_state.user_name = d["name"]; st.session_state.otp_sent = False
                            if "guest_log" in st.session_state:
                                g = st.session_state.guest_log; add_log(d["email"], d["name"], g["file"], "نجاح", g["arc"])
                            st.session_state.show_auth_popup = False
                            st.rerun()
                        else: st.error("خطأ")
