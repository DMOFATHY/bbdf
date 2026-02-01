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
# 📧 إعدادات البريد
# =======================
SENDER_EMAIL = "Dmofathy@gmail.com"
SENDER_PASSWORD = "fxns iuta umlu fprn"

def send_email_otp(receiver_email, otp_code):
    msg = MIMEText(f"كود التفعيل: {otp_code}", 'plain', 'utf-8')
    msg['Subject'] = "كود تفعيل حساب عون"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        return False

# =======================
# 1. إعداد الصفحة
# =======================
st.set_page_config(page_title="عون - مفتوح للجميع", page_icon="🤲", layout="centered")

# تذكرني
if "token" not in st.session_state:
    st.session_state.token = st.query_params.get("token", None)

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    
    .features-banner {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white; padding: 15px; border-radius: 10px;
        text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dedication-box {
        background-color: #f0fdf4; border: 2px solid #bbf7d0;
        color: #14532d; padding: 20px; border-radius: 12px;
        text-align: center; margin-bottom: 25px;
    }
    .history-card {
        background: white; border: 1px solid #e5e7eb; padding: 10px;
        border-radius: 8px; margin-bottom: 8px; display: flex;
        justify-content: space-between; align-items: center;
    }
    .vip-badge {
        color: #3b82f6; font-weight: bold; margin-right: 5px;
    }
    .blocked-user {
        background-color: #fef2f2; border: 1px solid #fee2e2;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. اللافتات
# =======================
st.markdown("""
<div class="features-banner">
    🚀 <b>أهلاً بك في عون (خدمة مجانية بالكامل)</b><br>
    ✅ <b>تحويل غير محدود للجميع (زوار وأعضاء).</b><br>
    📂 <b>سجل حساباً الآن لتحفظ ملفاتك وتعود إليها لاحقاً!</b>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="dedication-box">
    <div style="font-size: 1.3rem; font-weight: bold; margin-bottom: 10px;">🤲 صدقة جارية</div>
    <p>موهوب ثوابه إلى أرواح المغفور لهم بإذن الله:</p>
    <p style="font-weight:bold; color:#15803d;">جدتي، والأستاذ/ أحمد أمجد، والأستاذ/ محمود جمال</p>
</div>
""", unsafe_allow_html=True)

# =======================
# 3. الملفات والدوال
# =======================
USERS_FILE = "users.json"
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
        except: return {} if filename != LOGS_FILE else []
    return {} if filename != LOGS_FILE else []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

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

users = load_json(USERS_FILE)
# التأكد من وجود الأدمن
if "admin" not in users:
    users["admin"] = {"name": "Admin", "password": hash_pass("admin123"), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "admin", "blocked": False, "is_vip": True}
    save_json(USERS_FILE, users)

def check_libreoffice(): return shutil.which("libreoffice") or shutil.which("soffice")

def increment_stats(email):
    users = load_json(USERS_FILE)
    if email in users:
        users[email]["daily_used"] += 1
        save_json(USERS_FILE, users)

# =======================
# 4. Session & Remember Me
# =======================
if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

# Auto Login
tokens = load_json(TOKENS_FILE)
url_token = st.query_params.get("auth_token", None)
if not st.session_state.user_email and url_token:
    for email, token_data in tokens.items():
        if token_data == url_token:
            users = load_json(USERS_FILE)
            if email in users:
                # التحقق من الحظر أثناء الدخول التلقائي
                if users[email].get("blocked", False):
                    st.error("⛔ هذا الحساب محظور من قبل الإدارة.")
                    st.stop()
                st.session_state.user_email = email
                st.session_state.user_name = users[email]["name"]
                st.toast(f"مرحباً {users[email]['name']}", icon="👋")

# =======================
# 5. الواجهة
# =======================

# --- إذا كان المستخدم مسجلاً ---
if st.session_state.user_email:
    users = load_json(USERS_FILE)
    curr_user = users.get(st.session_state.user_email, {})
    
    # التحقق المزدوج من الحظر (في حال تم الحظر وهو داخل الموقع)
    if curr_user.get("blocked", False):
        st.error("⛔ تم حظر حسابك. يرجى التواصل مع الإدارة.")
        st.session_state.user_email = None
        st.rerun()

    is_admin = curr_user.get("role") == "admin"
    is_vip = curr_user.get("is_vip", False)
    vip_badge = "🔹" if is_vip else ""

    c1, c2 = st.columns([4, 1])
    with c1: st.success(f"👤 مرحباً، **{st.session_state.user_name}** {vip_badge}")
    with c2:
        if st.button("خروج"):
            st.session_state.user_email = None; st.session_state.user_name = None
            st.query_params.clear()
            st.rerun()

    tabs_list = ["🏠 تحويل جديد", "📂 سجل ملفاتي (History)", "⚙️ الإعدادات"]
    if is_admin: tabs_list.append("🛠️ لوحة الأدمن")
    main_tabs = st.tabs(tabs_list)

    # 1. التحويل (عضو)
    with main_tabs[0]:
        up = st.file_uploader("ارفع ملف للتحويل", type=["docx","xlsx","pptx"], key="member_up")
        if up and st.button("تحويل 🚀", key="member_btn", type="primary", use_container_width=True):
            if not check_libreoffice(): st.error("LibreOffice Missing"); st.stop()
            with st.spinner("جاري التحويل..."):
                uid = str(uuid.uuid4()); wd = os.path.join(TEMP_DIR, uid); os.makedirs(wd, exist_ok=True)
                ip = os.path.join(wd, up.name); 
                with open(ip, "wb") as f: f.write(up.getbuffer())
                
                # حفظ نسخة في الأرشيف
                arc = os.path.join(ARCHIVE_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{st.session_state.user_email}_{up.name}")
                shutil.copy(ip, arc)
                
                try:
                    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                    pn = up.name.rsplit(".", 1)[0] + ".pdf"; pp = os.path.join(wd, pn)
                    if os.path.exists(pp):
                        add_log(st.session_state.user_email, st.session_state.user_name, up.name, "نجاح ✅", arc)
                        increment_stats(st.session_state.user_email)
                        
                        st.success(f"تم التحويل: {up.name}")
                        with open(pp, "rb") as f:
                            st.download_button("⬇️ تحميل PDF", f, file_name=pn, mime="application/pdf", type="primary")
                    else: st.error("فشل التحويل")
                except Exception as e: st.error(f"Error: {e}")

    # 2. السجل
    with main_tabs[1]:
        st.subheader("📜 أرشيف ملفاتك")
        all_logs = load_json(LOGS_FILE)
        my_logs = [l for l in all_logs if l.get('email') == st.session_state.user_email]
        
        if my_logs:
            for l in my_logs:
                with st.container():
                    st.markdown(f"""
                    <div class="history-card">
                        <div>
                            <b>{l['filename']}</b><br>
                            <span style="font-size:0.8em; color:gray">{l['timestamp']}</span>
                        </div>
                        <div style="color:{'green' if 'نجاح' in l['status'] else 'red'}">
                            {l['status']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if l.get('archived_path') and os.path.exists(l['archived_path']) and 'نجاح' in l['status']:
                         with open(l['archived_path'], "rb") as f:
                             st.download_button("📥 تحميل الأصل", f, file_name=l['filename'], key=f"dl_{l['timestamp']}")
        else:
            st.info("لا توجد تحويلات سابقة.")

    # 3. الإعدادات
    with main_tabs[2]:
        st.write(f"إجمالي تحويلاتك: {curr_user.get('daily_used', 0)}")
        if is_vip: st.success("🌟 أنت عضو موثق (VIP)")
        
        with st.form("pass_change"):
            st.write("تغيير كلمة المرور")
            n_p = st.text_input("كلمة مرور جديدة", type="password")
            if st.form_submit_button("حفظ"):
                users[st.session_state.user_email]['password'] = hash_pass(n_p)
                save_json(USERS_FILE, users)
                st.success("تم التحديث")

    # 4. الأدمن (المحدثة)
    if is_admin:
        with main_tabs[3]:
            admin_tabs = st.tabs(["👥 إدارة الأعضاء", "📂 كل الملفات"])
            
            # --- تبويب إدارة الأعضاء ---
            with admin_tabs[0]:
                st.write("### التحكم بالأعضاء")
                
                # تحويل القاموس لقائمة لسهولة العرض
                for u_email, u_data in users.items():
                    if u_data['role'] == 'admin': continue # تخطي الأدمن
                    
                    with st.expander(f"{u_data['name']} ({u_email})", expanded=False):
                        c1, c2, c3 = st.columns(3)
                        
                        # حالة العضو
                        is_blocked = u_data.get('blocked', False)
                        is_user_vip = u_data.get('is_vip', False)
                        
                        with c1:
                            st.write(f"**الحالة:** {'⛔ محظور' if is_blocked else '✅ نشط'}")
                            st.write(f"**التوثيق:** {'🔹 VIP' if is_user_vip else 'عادي'}")
                        
                        with c2:
                            # زر الحظر/فك الحظر
                            btn_label = "🔓 فك الحظر" if is_blocked else "⛔ حظر العضو"
                            if st.button(btn_label, key=f"blk_{u_email}"):
                                users[u_email]['blocked'] = not is_blocked
                                save_json(USERS_FILE, users)
                                st.rerun()
                        
                        with c3:
                            # زر التوثيق/إلغاء التوثيق
                            vip_label = "➖ إلغاء VIP" if is_user_vip else "🌟 منح VIP"
                            if st.button(vip_label, key=f"vip_{u_email}"):
                                users[u_email]['is_vip'] = not is_user_vip
                                save_json(USERS_FILE, users)
                                st.rerun()

            # --- تبويب إدارة الملفات ---
            with admin_tabs[1]:
                st.write("### 📂 أرشيف جميع الملفات")
                all_logs_admin = load_json(LOGS_FILE)
                
                if not all_logs_admin:
                    st.info("لا توجد ملفات في السجل")
                else:
                    # تحويل السجل لإطار بيانات للعرض السريع
                    df_logs = pd.DataFrame(all_logs_admin)
                    st.dataframe(df_logs[['timestamp', 'name', 'email', 'filename', 'status']], use_container_width=True)
                    
                    st.divider()
                    st.write("**📥 تحميل ملفات الأعضاء:**")
                    
                    # حلقة لعرض أزرار التحميل
                    for log in all_logs_admin:
                        path = log.get('archived_path')
                        if path and os.path.exists(path):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.text(f"📄 {log['filename']} - {log['name']}")
                            with col_b:
                                with open(path, "rb") as f:
                                    st.download_button("تحميل", f, file_name=f"ADMIN_COPY_{log['filename']}", key=f"adm_dl_{log['timestamp']}")
                            st.divider()

# --- إذا كان زائراً (Guest) ---
else:
    with st.expander("🔓 لديك حساب؟ تسجيل الدخول (لعرض السجل)", expanded=False):
        t1, t2 = st.tabs(["دخول", "إنشاء حساب"])
        with t1:
            l_e = st.text_input("الإيميل", key="g_l_e")
            l_p = st.text_input("الرمز", type="password", key="g_l_p")
            rem = st.checkbox("تذكرني")
            if st.button("دخول", key="g_btn"):
                users = load_json(USERS_FILE)
                if l_e in users and users[l_e]["password"] == hash_pass(l_p):
                    # التحقق من الحظر
                    if users[l_e].get("blocked", False):
                        st.error("⛔ عذراً، تم حظر هذا الحساب. تواصل مع الدعم.")
                    else:
                        st.session_state.user_email = l_e
                        st.session_state.user_name = users[l_e]["name"]
                        if rem:
                            tk = str(uuid.uuid4()); ts = load_json(TOKENS_FILE); ts[l_e] = tk; save_json(TOKENS_FILE, ts)
                            st.query_params["auth_token"] = tk
                        st.rerun()
                else: st.error("خطأ في البيانات")
        with t2:
            if not st.session_state.otp_sent:
                r_n = st.text_input("الاسم"); r_e = st.text_input("الإيميل"); r_p = st.text_input("رمز جديد")
                if st.button("إرسال الكود 📨"):
                    users = load_json(USERS_FILE)
                    if r_e in users: st.warning("مسجل مسبقاً")
                    else:
                        c = str(random.randint(1000,9999))
                        if send_email_otp(r_e, c):
                            st.session_state.otp_code = c; st.session_state.otp_sent = True; st.session_state.reg_data = {"name":r_n, "email":r_e, "pass":r_p}
                            st.rerun()
            else:
                o_in = st.text_input("الكود")
                if st.button("تفعيل"):
                    if o_in == st.session_state.otp_code:
                        d = st.session_state.reg_data; users = load_json(USERS_FILE)
                        users[d["email"]] = {"name":d["name"], "password":hash_pass(d["pass"]), "daily_used":0, "last_day":"", "role":"user", "blocked":False, "is_vip":False}
                        save_json(USERS_FILE, users)
                        st.session_state.user_email = d["email"]; st.session_state.user_name = d["name"]; st.session_state.otp_sent = False
                        st.rerun()
                    else: st.error("الكود غير صحيح")

    st.markdown("### 📄 تحويل ملفات (غير محدود)")
    up_guest = st.file_uploader("ارفع ملفك هنا", type=["docx","xlsx","pptx"])
    
    if up_guest:
        if st.button("تحويل 🚀", type="primary", use_container_width=True):
            if not check_libreoffice(): st.error("LibreOffice Missing"); st.stop()
            with st.spinner("جاري التحويل..."):
                uid = str(uuid.uuid4()); wd = os.path.join(TEMP_DIR, uid); os.makedirs(wd, exist_ok=True)
                ip = os.path.join(wd, up_guest.name); 
                with open(ip, "wb") as f: f.write(up_guest.getbuffer())
                
                try:
                    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", ip, "--outdir", wd], check=True)
                    pn = up_guest.name.rsplit(".", 1)[0] + ".pdf"; pp = os.path.join(wd, pn)
                    if os.path.exists(pp):
                        st.success("✅ تم التحويل بنجاح")
                        with open(pp, "rb") as f:
                            st.download_button("⬇️ تحميل PDF", f, file_name=pn, mime="application/pdf", type="primary", use_container_width=True)
                        st.info("💡 نصيحة: هل تريد حفظ هذا الملف في سجلك؟ قم بتسجيل الدخول بالأعلى.")
                    else: st.error("فشل التحويل")
                except Exception as e: st.error(f"Error: {e}")

