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
# 📧 إعدادات البريد (تأكد من صحتها)
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
# 1. إعداد الصفحة والستايل
# =======================
st.set_page_config(page_title="عون - صدقة جارية", page_icon="🤲", layout="centered")

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    
    .dedication-box {
        background-color: #f0fdf4; border: 2px solid #bbf7d0;
        color: #14532d; padding: 20px; border-radius: 12px;
        text-align: center; margin-bottom: 25px;
    }
    .auth-popup {
        background-color: #ffffff; border: 2px solid #3b82f6;
        padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-top: 20px; animation: slideUp 0.5s ease-out;
    }
    @keyframes slideUp { from {transform: translateY(20px); opacity: 0;} to {transform: translateY(0); opacity: 1;} }
    .success-box {
        background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724;
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;
    }
    .admin-card {
        background-color: #f8f9fa; border: 1px solid #e9ecef;
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. لافتة الصدقة
# =======================
st.markdown("""
<div class="dedication-box">
    <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">🤲 صدقة جارية</div>
    <p>موهوب ثوابه إلى أرواح المغفور لهم بإذن الله:</p>
    <p style="font-weight:bold; color:#15803d;">جدتي، والأستاذ/ أحمد أمجد، والأستاذ/ محمود جمال</p>
    <hr style="border-top: 1px solid #bbf7d0; margin: 10px 0;">
    <p style="font-family:'Amiri'; font-size:1.1rem;">"اللهم اغفر لهم وارحمهم، وأكرم نزلهم، واجعل قبورهم روضة من رياض الجنة."</p>
</div>
""", unsafe_allow_html=True)

# =======================
# 3. البيانات
# =======================
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
TEMP_DIR = "temp_conversion"
ARCHIVE_DIR = "archive_files"

for d in [TEMP_DIR, ARCHIVE_DIR]: os.makedirs(d, exist_ok=True)

def hash_pass(password): return hashlib.sha256(password.encode()).hexdigest()

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f: return json.load(f)
        except: return {} if filename == USERS_FILE else []
    return {} if filename == USERS_FILE else []

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

# =======================
# 4. الدوال
# =======================
def check_libreoffice(): return shutil.which("libreoffice") or shutil.which("soffice")

def can_convert(email):
    users = load_json(USERS_FILE)
    user = users.get(email)
    if not user: return False, "غير موجود"
    if user.get("blocked", False): return False, "محظور"
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0; user["last_day"] = today; save_json(USERS_FILE, users)
    if user["daily_used"] >= 5: return False, "انتهى الرصيد"
    return True, ""

def update_usage(email):
    users = load_json(USERS_FILE)
    if email in users: users[email]["daily_used"] += 1; save_json(USERS_FILE, users)

# =======================
# 5. Session
# =======================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "pending_file" not in st.session_state: st.session_state.pending_file = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "reg_data" not in st.session_state: st.session_state.reg_data = {}
if "show_auth" not in st.session_state: st.session_state.show_auth = False

# =======================
# 6. الواجهة الرئيسية
# =======================
if st.session_state.user_email:
    # --- المسجلين ---
    c1, c2 = st.columns([4, 1])
    with c1: st.success(f"👋 أهلاً بك، **{st.session_state.user_name}**")
    with c2:
        if st.button("خروج"):
            st.session_state.user_email = None; st.session_state.user_name = None; st.session_state.pending_file = None; st.rerun()

    # فحص صلاحية الأدمن
    users = load_json(USERS_FILE)
    curr_user = users.get(st.session_state.user_email, {})
    is_admin = curr_user.get("role") == "admin"

    # التبويبات
    tabs_list = ["🏠 تحويل الملفات", "📜 سجل نشاطي", "⚙️ الإعدادات"]
    if is_admin: tabs_list.append("🛠️ لوحة الأدمن")
    
    main_tabs = st.tabs(tabs_list)

    # 1. التحويل
    with main_tabs[0]:
        if st.session_state.pending_file:
            p = st.session_state.pending_file
            if os.path.exists(p["path"]):
                st.markdown(f"<div class='success-box'>🎉 ملفك جاهز: {p['name']}</div>", unsafe_allow_html=True)
                with open(p["path"], "rb") as f:
                    st.download_button("⬇️ تحميل PDF", f, file_name=p["pdf_name"], mime="application/pdf", type="primary", use_container_width=True)
                if st.button("تحويل ملف آخر"):
                    update_usage(st.session_state.user_email)
                    st.session_state.pending_file = None
                    st.rerun()
        else:
            up = st.file_uploader("ارفع ملف للتحويل", type=["docx","xlsx","pptx"])
            if up and st.button("تحويل 🚀", use_container_width=True):
                ok, msg = can_convert(st.session_state.user_email)
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
        used = curr_user.get('daily_used', 0)
        st.metric("الاستهلاك اليومي", f"{used} / 5")
        st.divider()
        with st.form("change_pass"):
            o_p = st.text_input("القديمة", type="password")
            n_p = st.text_input("الجديدة", type="password")
            if st.form_submit_button("تغيير كلمة المرور"):
                if hash_pass(o_p) == curr_user['password']:
                    users[st.session_state.user_email]['password'] = hash_pass(n_p)
                    save_json(USERS_FILE, users)
                    st.success("تم التغيير")
                else: st.error("كلمة المرور خطأ")

    # 4. لوحة الأدمن (المطورة)
    if is_admin:
        with main_tabs[3]:
            st.header("🛠️ تحكم المدير")
            
            admin_subtabs = st.tabs(["👥 إدارة الأعضاء", "➕ إنشاء حساب", "📊 سجلات النظام"])
            
            # --- إدارة الأعضاء ---
            with admin_subtabs[0]:
                st.dataframe(pd.DataFrame(users).T.drop("password", axis=1), use_container_width=True)
                st.divider()
                
                sel_user = st.selectbox("🔍 اختر مستخدم للتحكم به:", [u for u in users.keys() if u != "admin"])
                
                if sel_user:
                    st.markdown(f"<div class='admin-card'>تعديل المستخدم: <b>{sel_user}</b></div>", unsafe_allow_html=True)
                    
                    # تعديل البيانات الأساسية
                    with st.expander("✏️ تعديل البيانات (الاسم / الباسورد)"):
                        new_name = st.text_input("تعديل الاسم", value=users[sel_user].get("name", ""))
                        new_pass_admin = st.text_input("تعيين كلمة مرور جديدة (اتركه فارغاً للإبقاء)", type="password")
                        if st.button("حفظ التعديلات"):
                            users[sel_user]["name"] = new_name
                            if new_pass_admin:
                                users[sel_user]["password"] = hash_pass(new_pass_admin)
                            save_json(USERS_FILE, users)
                            st.success("تم التحديث")
                            time.sleep(1)
                            st.rerun()

                    # أزرار التحكم السريع
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        is_blk = users[sel_user]["blocked"]
                        if st.button(f"{'فك الحظر' if is_blk else '🚫 حظر'}", use_container_width=True):
                            users[sel_user]["blocked"] = not is_blk; save_json(USERS_FILE, users); st.rerun()
                    with col_b:
                        if st.button("🔄 تصفير", use_container_width=True):
                            users[sel_user]["daily_used"] = 0; save_json(USERS_FILE, users); st.rerun()
                    with col_c:
                        is_vip = users[sel_user].get("is_vip", False)
                        if st.button(f"{'لغي VIP' if is_vip else '⭐ VIP'}", use_container_width=True):
                            users[sel_user]["is_vip"] = not is_vip; save_json(USERS_FILE, users); st.rerun()
                    with col_d:
                        # زر الحذف الخطير
                        if st.button("🗑️ حذف الحساب", type="primary", use_container_width=True):
                            del users[sel_user]
                            save_json(USERS_FILE, users)
                            st.warning(f"تم حذف المستخدم {sel_user}")
                            time.sleep(1)
                            st.rerun()

            # --- إنشاء حساب يدوي ---
            with admin_subtabs[1]:
                with st.form("admin_create_user"):
                    st.write("إضافة مستخدم جديد مباشرة (بدون تفعيل)")
                    c_name = st.text_input("الاسم")
                    c_email = st.text_input("البريد الإلكتروني")
                    c_pass = st.text_input("كلمة المرور", type="password")
                    c_vip = st.checkbox("حساب VIP؟")
                    
                    if st.form_submit_button("إضافة المستخدم"):
                        if c_email in users:
                            st.error("موجود مسبقاً")
                        elif not c_email or not c_pass:
                            st.error("أكمل البيانات")
                        else:
                            users[c_email] = {
                                "name": c_name, "password": hash_pass(c_pass),
                                "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"),
                                "role": "user", "blocked": False, "is_vip": c_vip
                            }
                            save_json(USERS_FILE, users)
                            st.success(f"تم إضافة {c_email} بنجاح")

            # --- السجلات ---
            with admin_subtabs[2]:
                all_logs = load_json(LOGS_FILE)
                st.write(f"عدد العمليات: {len(all_logs)}")
                for l in all_logs[:50]: # عرض آخر 50 فقط
                    with st.expander(f"{l['timestamp']} | {l['email']}"):
                        st.write(f"الملف: {l['filename']}")
                        if l.get('archived_path') and os.path.exists(l['archived_path']):
                            with open(l['archived_path'], "rb") as f:
                                st.download_button("تحميل الملف الأصلي", f, file_name=f"ARC_{l['filename']}")

# --- الزوار ---
else:
    st.markdown("### 📄 تحويل الملفات إلى PDF")
    
    up_guest = st.file_uploader("ارفع ملفك هنا", type=["docx","xlsx","pptx"])
    if up_guest:
        if st.button("بدء التحويل 🚀", type="primary", use_container_width=True):
            if not check_libreoffice(): st.error("LibreOffice Missing"); st.stop()
            with st.spinner("جاري معالجة الملف..."):
                uid = str(uuid.uuid4()); wd = os.path.join(TEMP_DIR, uid); os.makedirs(wd, exist_ok=True)
                ip = os.path.join(wd, up_guest.name); 
                with open(ip, "wb") as f: f.write(up_guest.getbuffer())
                arc = os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_Guest_{up_guest.name}")
                shutil.copy(ip, arc)
                try:
                    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                    pn = up_guest.name.rsplit(".", 1)[0] + ".pdf"; pp = os.path.join(wd, pn)
                    if os.path.exists(pp):
                        st.session_state.pending_file = {"path": pp, "name": up_guest.name, "pdf_name": pn}
                        st.session_state.show_auth = True 
                        st.session_state.guest_log = {"name": "Guest", "email": "Pending", "file": up_guest.name, "arc": arc}
                    else: st.error("فشل التحويل.")
                except Exception as e: st.error(f"Error: {e}")

    if st.session_state.show_auth:
        st.markdown("""
        <div class="auth-popup">
            <h3 style="text-align:center; color:#3b82f6;">✅ تم التحويل بنجاح!</h3>
            <p style="text-align:center;">الملف جاهز. يرجى تسجيل الدخول أو إنشاء حساب لتحميله فوراً.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            t1, t2 = st.tabs(["🔐 تسجيل دخول", "✨ حساب جديد"])
            with t1:
                l_em = st.text_input("البريد الإلكتروني", key="l_em_guest")
                l_pa = st.text_input("كلمة المرور", type="password", key="l_pa_guest")
                if st.button("دخول وتحميل الملف", use_container_width=True):
                    users = load_json(USERS_FILE)
                    if l_em in users and users[l_em]["password"] == hash_pass(l_pa):
                        st.session_state.user_email = l_em; st.session_state.user_name = users[l_em].get("name", "")
                        if "guest_log" in st.session_state:
                            g = st.session_state.guest_log
                            add_log(l_em, users[l_em]["name"], g["file"], "نجاح", g["arc"])
                        st.rerun()
                    else: st.error("بيانات خاطئة")

            with t2:
                if not st.session_state.otp_sent:
                    with st.form("guest_signup"):
                        r_nm = st.text_input("الاسم"); r_em = st.text_input("الإيميل (Gmail)"); r_pa = st.text_input("كلمة مرور")
                        if st.form_submit_button("إرسال كود التفعيل 📨", use_container_width=True):
                            users = load_json(USERS_FILE)
                            if r_em in users: st.warning("مسجل مسبقاً")
                            elif "@gmail.com" not in r_em: st.warning("استخدم Gmail")
                            else:
                                code = str(random.randint(1000, 9999))
                                if send_email_otp(r_em, code):
                                    st.session_state.otp_code = code; st.session_state.otp_sent = True; st.session_state.reg_data = {"name": r_nm, "email": r_em, "pass": r_pa}
                                    st.rerun()
                else:
                    st.info(f"الكود مرسل إلى: {st.session_state.reg_data['email']}")
                    otp_in = st.text_input("الكود", max_chars=4)
                    if st.button("تأكيد وإنشاء الحساب", use_container_width=True):
                        if otp_in == st.session_state.otp_code:
                            users = load_json(USERS_FILE); d = st.session_state.reg_data
                            users[d["email"]] = {"name": d["name"], "password": hash_pass(d["pass"]), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "user", "blocked": False, "is_vip": False}
                            save_json(USERS_FILE, users)
                            st.session_state.user_email = d["email"]; st.session_state.user_name = d["name"]; st.session_state.otp_sent = False
                            if "guest_log" in st.session_state:
                                g = st.session_state.guest_log; add_log(d["email"], d["name"], g["file"], "نجاح", g["arc"])
                            st.rerun()
                        else: st.error("الكود خطأ")

