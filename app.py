import streamlit as st
import subprocess
import os
import shutil
import uuid
import json
import hashlib
from datetime import datetime
import pandas as pd

# =======================
# 1. إعداد الصفحة
# =======================
st.set_page_config(page_title="عون - محول الملفات", page_icon="🛠️", layout="centered")

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    
    .login-container {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        text-align: center;
    }
    .guest-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffeeba;
        margin-bottom: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. إدارة البيانات
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

def add_log(username, filename, status, archived_path=None):
    logs = load_json(LOGS_FILE)
    if not isinstance(logs, list): logs = []
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "filename": filename,
        "status": status,
        "archived_path": archived_path
    }
    logs.insert(0, entry)
    save_json(LOGS_FILE, logs)

# التأكد من وجود أدمن
users = load_json(USERS_FILE)
if "admin" not in users:
    users["admin"] = {
        "password": hash_pass("admin123"),
        "daily_used": 0,
        "last_day": datetime.now().strftime("%Y-%m-%d"),
        "role": "admin",
        "blocked": False,
        "is_vip": True
    }
    save_json(USERS_FILE, users)

# =======================
# 3. دوال المنطق
# =======================
def check_libreoffice():
    if shutil.which("libreoffice") or shutil.which("soffice"): return True
    return False

def can_convert(username):
    users = load_json(USERS_FILE)
    user = users.get(username)
    if not user: return False, "غير موجود"
    if user.get("blocked", False): return False, "محظور"
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today
        save_json(USERS_FILE, users)
    
    if user["daily_used"] >= 5: return False, "انتهى الرصيد"
    return True, ""

def update_usage(username):
    users = load_json(USERS_FILE)
    if username in users:
        users[username]["daily_used"] += 1
        save_json(USERS_FILE, users)

# =======================
# 4. إدارة الجلسة (Session)
# =======================
if "user" not in st.session_state:
    st.session_state.user = None

# متغير لتتبع تجربة الزائر (المرة الواحدة)
if "guest_used" not in st.session_state:
    st.session_state.guest_used = False

# =======================
# 5. الواجهة الرئيسية
# =======================

# ---------------------------------------------------------
# الحالة A: المستخدم غير مسجل دخول + واستهلك التجربة المجانية
# (يتم إجباره على التسجيل هنا)
# ---------------------------------------------------------
if st.session_state.user is None and st.session_state.guest_used:
    st.markdown("<h1 style='text-align: center;'>🛑 انتهت التجربة المجانية</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>لقد قمت بتحويل ملف واحد كزائر. يرجى تسجيل الدخول أو إنشاء حساب للمتابعة.</p>", unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["🔑 تسجيل الدخول", "✨ إنشاء حساب جديد"])
    
    with tab_login:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        l_u = st.text_input("اسم المستخدم", key="l_u")
        l_p = st.text_input("كلمة المرور", type="password", key="l_p")
        if st.button("دخول", type="primary"):
            users = load_json(USERS_FILE)
            if l_u in users and users[l_u]["password"] == hash_pass(l_p):
                st.session_state.user = l_u
                st.rerun()
            else:
                st.error("بيانات خاطئة")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_signup:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        n_u = st.text_input("اختر اسم مستخدم", key="n_u")
        n_p = st.text_input("اختر كلمة مرور", type="password", key="n_p")
        if st.button("تسجيل حساب جديد"):
            users = load_json(USERS_FILE)
            if n_u in users:
                st.warning("الاسم مستخدم")
            elif not n_u or not n_p:
                st.warning("أكمل البيانات")
            else:
                users[n_u] = {
                    "password": hash_pass(n_p),
                    "daily_used": 0,
                    "last_day": datetime.now().strftime("%Y-%m-%d"),
                    "role": "user",
                    "blocked": False,
                    "is_vip": False
                }
                save_json(USERS_FILE, users)
                st.success("تم الإنشاء! سجل دخولك الآن.")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# الحالة B: المستخدم مسجل دخول (أو زائر لم يستهلك فرصته بعد)
# ---------------------------------------------------------
else:
    # Header
    c1, c2 = st.columns([5,1])
    with c1:
        if st.session_state.user:
            st.success(f"مرحباً **{st.session_state.user}**")
        else:
            st.warning("👤 أنت تستخدم وضع الزائر (ملف واحد فقط)")
    
    with c2:
        if st.session_state.user:
            if st.button("خروج"):
                st.session_state.user = None
                st.rerun()
        else:
            # زر إضافي لمن يريد التسجيل طواعية قبل التجربة
            if st.button("دخول"):
                st.session_state.guest_used = True # خدعة لتحويله لشاشة الدخول
                st.rerun()

    # --- Admin View ---
    if st.session_state.user and users.get(st.session_state.user, {}).get("role") == "admin":
        st.title("🛠️ لوحة التحكم")
        admin_view = st.radio("القائمة:", ["👥 الأعضاء", "📊 السجلات"], horizontal=True)
        
        if admin_view == "👥 الأعضاء":
            users = load_json(USERS_FILE)
            df = pd.DataFrame(users).T.drop("password", axis=1)
            st.dataframe(df, use_container_width=True)
            sel_user = st.selectbox("تعديل عضو:", [u for u in users.keys() if u != "admin"])
            if sel_user:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("حظر/فك", key="blk", use_container_width=True):
                        users[sel_user]["blocked"] = not users[sel_user]["blocked"]
                        save_json(USERS_FILE, users)
                        st.rerun()
                with c2:
                    if st.button("تصفير", key="rst", use_container_width=True):
                        users[sel_user]["daily_used"] = 0
                        save_json(USERS_FILE, users)
                        st.rerun()
                with c3:
                    is_vip = users[sel_user].get("is_vip", False)
                    if st.button("VIP", key="vip", use_container_width=True):
                        users[sel_user]["is_vip"] = not is_vip
                        save_json(USERS_FILE, users)
                        st.rerun()

        elif admin_view == "📊 السجلات":
            logs = load_json(LOGS_FILE)
            for l in logs:
                with st.expander(f"{l['timestamp']} - {l['user']}"):
                    st.write(f"ملف: {l['filename']} - حالة: {l['status']}")
                    if l.get("archived_path") and os.path.exists(l["archived_path"]):
                        with open(l["archived_path"], "rb") as f:
                            st.download_button("تحميل", f, file_name=f"ARC_{l['filename']}")
            if st.button("مسح الأرشيف"):
                shutil.rmtree(ARCHIVE_DIR)
                os.makedirs(ARCHIVE_DIR)
                st.rerun()

    # --- Converter View ---
    else:
        st.markdown("## 🔁 محول الملفات")
        if not check_libreoffice():
            st.error("النظام يفتقد LibreOffice")
            st.stop()
            
        uploaded_file = st.file_uploader("ارفع ملفك (Word, Excel, PPT)", type=["docx", "doc", "pptx", "ppt", "xlsx", "xls"])

        if uploaded_file and st.button("تحويل 🚀", type="primary"):
            
            # 1. التحقق من الصلاحيات
            if st.session_state.user:
                # للمسجلين: تطبيق قوانين الحد اليومي
                allowed, msg = can_convert(st.session_state.user)
                if not allowed:
                    st.error(msg)
                    add_log(st.session_state.user, uploaded_file.name, "فشل (الحد)", None)
                    st.stop()
                current_user_name = st.session_state.user
            else:
                # للزوار: السماح بالمرور (سنقوم بالحظر بعد التحويل)
                current_user_name = "Guest_User"

            with st.spinner("جاري التحويل..."):
                uid = str(uuid.uuid4())
                work = os.path.join(TEMP_DIR, uid)
                os.makedirs(work, exist_ok=True)
                
                in_path = os.path.join(work, uploaded_file.name)
                with open(in_path, "wb") as f: f.write(uploaded_file.getbuffer())
                
                # أرشفة
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                arc_path = os.path.join(ARCHIVE_DIR, f"{ts}_{current_user_name}_{uploaded_file.name}")
                shutil.copy(in_path, arc_path)

                try:
                    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", in_path, "--outdir", work], check=True)
                    pdf_name = uploaded_file.name.rsplit(".", 1)[0] + ".pdf"
                    pdf_path = os.path.join(work, pdf_name)
                    
                    if os.path.exists(pdf_path):
                        st.success("✅ تم التحويل بنجاح!")
                        
                        # زر التحميل
                        with open(pdf_path, "rb") as f:
                            st.download_button("📥 تحميل PDF", f, file_name=pdf_name)
                        
                        # تحديث السجلات
                        if st.session_state.user:
                            update_usage(st.session_state.user)
                        else:
                            # ⚠️ هنا اللحظة الحاسمة للزائر
                            # نقوم بتسجيل أنه استخدم فرصته
                            st.session_state.guest_used = True
                            st.warning("⚠️ كانت هذه تجربتك المجانية الوحيدة. يرجى تحميل الملف الآن، لأنه سيطلب منك التسجيل في المرة القادمة.")
                        
                        add_log(current_user_name, uploaded_file.name, "نجاح", arc_path)
                    else:
                        st.error("فشل التحويل")
                except Exception as e:
                    st.error(f"خطأ: {e}")
                
                shutil.rmtree(work, ignore_errors=True)

