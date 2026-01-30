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
# 1. إعداد الصفحة والستايل
# =======================
st.set_page_config(page_title="عون - محول الملفات", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
    .metric-card {
        background-color: #f0f2f6; padding: 15px; border-radius: 10px;
        border-right: 4px solid #ff4b4b; text-align: center; margin-bottom: 10px;
    }
    .metric-value {font-size: 24px; font-weight: bold; color: #333;}
    .metric-label {font-size: 14px; color: #666;}
    /* تنسيق جدول السجلات */
    .log-row {
        background-color: white; border: 1px solid #eee; padding: 10px; 
        border-radius: 5px; margin-bottom: 5px; display: flex; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. إدارة الملفات والبيانات
# =======================
USERS_FILE = "users.json"
LOGS_FILE = "logs.json"
TEMP_DIR = "temp_conversion"
ARCHIVE_DIR = "archive_files" # مجلد حفظ ملفات المستخدمين للأدمن

# إنشاء المجلدات الضرورية
for d in [TEMP_DIR, ARCHIVE_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

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

# --- دوال السجل (Logging) ---
def add_log(username, filename, status, archived_path=None):
    logs = load_json(LOGS_FILE)
    if not isinstance(logs, list): logs = []
    
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": username,
        "filename": filename,
        "status": status,
        "archived_path": archived_path # مسار الملف المحفوظ
    }
    logs.insert(0, entry) # إضافة الأحدث في البداية
    save_json(LOGS_FILE, logs)

# =======================
# 3. التأكد من وجود Admin
# =======================
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
# 4. دوال المنطق
# =======================
def check_libreoffice():
    if shutil.which("libreoffice") or shutil.which("soffice"): return True
    common_paths = [r"C:\Program Files\LibreOffice\program\soffice.exe", "/usr/bin/libreoffice", "/usr/bin/soffice"]
    for path in common_paths:
        if os.path.exists(path): return True
    return False

def can_convert(username):
    users = load_json(USERS_FILE)
    user = users.get(username)
    if not user: return False, "مستخدم غير موجود"
    
    if user.get("blocked", False): return False, "🚫 حسابك محظور."
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"

    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today
        save_json(USERS_FILE, users)

    if user["daily_used"] >= 5: return False, "⚠️ انتهى رصيدك اليومي (5 ملفات)."
    return True, ""

def update_usage(username):
    users = load_json(USERS_FILE)
    if username in users:
        users[username]["daily_used"] += 1
        save_json(USERS_FILE, users)

# =======================
# 5. القائمة الجانبية (Auth)
# =======================
with st.sidebar:
    st.title("👤 الملف الشخصي")
    if "user" not in st.session_state: st.session_state.user = None

    if st.session_state.user:
        u_data = users.get(st.session_state.user, {})
        st.success(f"مرحباً, **{st.session_state.user}**")
        if st.button("تسجيل خروج", type="primary"):
            st.session_state.user = None
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["دخول", "تسجيل"])
        with tab1:
            u = st.text_input("المستخدم", key="l_u")
            p = st.text_input("الرمز", type="password", key="l_p")
            if st.button("دخول"):
                if u in users and users[u]["password"] == hash_pass(p):
                    st.session_state.user = u
                    st.rerun()
                else: st.error("خطأ في البيانات")
        with tab2:
            nu = st.text_input("مستخدم جديد", key="n_u")
            np = st.text_input("رمز جديد", type="password", key="n_p")
            if st.button("إنشاء"):
                if nu not in users:
                    users[nu] = {"password": hash_pass(np), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "user", "blocked": False, "is_vip": False}
                    save_json(USERS_FILE, users)
                    st.success("تم التسجيل")
                else: st.warning("موجود مسبقاً")

# =======================
# 6. الواجهة الرئيسية
# =======================

# --- Admin Panel ---
if st.session_state.user and users.get(st.session_state.user, {}).get("role") == "admin":
    st.title("🛠️ لوحة الإدارة والرقابة")
    
    admin_tab1, admin_tab2 = st.tabs(["👥 إدارة المستخدمين", "📊 سجل التحويلات والملفات"])

    # تبويب المستخدمين
    with admin_tab1:
        users = load_json(USERS_FILE)
        df_users = pd.DataFrame(users).T.drop("password", axis=1)
        st.dataframe(df_users)
        
        st.markdown("### تحكم سريع")
        sel_user = st.selectbox("اختر مستخدم", [u for u in users.keys() if u != "admin"])
        if sel_user:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("فك/حظر", key="blk"):
                    users[sel_user]["blocked"] = not users[sel_user]["blocked"]
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c2:
                if st.button("تصفير العداد", key="rst"):
                    users[sel_user]["daily_used"] = 0
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c3:
                if st.button("تبديل VIP", key="vip"):
                    users[sel_user]["is_vip"] = not users[sel_user].get("is_vip", False)
                    save_json(USERS_FILE, users)
                    st.rerun()

    # تبويب السجلات والملفات
    with admin_tab2:
        logs = load_json(LOGS_FILE)
        
        if not logs:
            st.info("لا توجد سجلات حتى الآن.")
        else:
            st.markdown(f"**عدد العمليات:** {len(logs)}")
            
            # عرض السجلات كجدول تفاعلي مع زر التحميل
            for idx, log in enumerate(logs):
                # تصميم صف لكل سجل
                with st.container():
                    col_info, col_file = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        **👤 {log['user']}** | 🕒 {log['timestamp']} <br>
                        📄 الملف: `{log['filename']}` | الحالة: {log['status']}
                        """, unsafe_allow_html=True)
                        st.divider()

                    with col_file:
                        # التحقق من وجود الملف المؤرشف
                        archived = log.get("archived_path")
                        if archived and os.path.exists(archived):
                            with open(archived, "rb") as f:
                                st.download_button(
                                    label="📥 تحميل الملف الأصلي",
                                    data=f,
                                    file_name=f"ARCHIVE_{log['filename']}",
                                    key=f"dl_{idx}"
                                )
                        else:
                            st.caption("الملف غير متوفر (محذوف)")

            if st.button("🗑️ حذف جميع الملفات المؤرشفة (لتوفير المساحة)", type="primary"):
                shutil.rmtree(ARCHIVE_DIR)
                os.makedirs(ARCHIVE_DIR)
                st.success("تم تنظيف الأرشيف.")
                st.rerun()

# --- User View ---
else:
    st.markdown("## 🔁 عون - محول الملفات")
    
    if not check_libreoffice():
        st.error("الخادم يفتقد LibreOffice.")
        st.stop()

    uploaded_file = st.file_uploader("ارفع ملف (Word, PPT, Excel)", type=["docx", "doc", "pptx", "ppt", "xlsx", "xls"])

    if uploaded_file and st.button("تحويل"):
        if not st.session_state.user:
            st.error("يجب تسجيل الدخول أولاً.")
            st.stop()
            
        allowed, msg = can_convert(st.session_state.user)
        if not allowed:
            st.error(msg)
            add_log(st.session_state.user, uploaded_file.name, "فشل (تجاوز الحد)", None)
            st.stop()

        with st.spinner("جاري المعالجة..."):
            uid = str(uuid.uuid4())
            work_dir = os.path.join(TEMP_DIR, uid)
            os.makedirs(work_dir, exist_ok=True)
            
            input_path = os.path.join(work_dir, uploaded_file.name)
            
            # 1. حفظ الملف للعمل عليه
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 2. أرشفة الملف للأدمن (نسخة إضافية)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{timestamp_str}_{st.session_state.user}_{uploaded_file.name}"
            archive_path = os.path.join(ARCHIVE_DIR, archive_name)
            shutil.copy(input_path, archive_path) # نسخ للأرشيف

            # 3. التحويل
            try:
                subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", work_dir], check=True)
                pdf_name = uploaded_file.name.rsplit(".", 1)[0] + ".pdf"
                pdf_path = os.path.join(work_dir, pdf_name)
                
                if os.path.exists(pdf_path):
                    st.success("تم التحويل!")
                    with open(pdf_path, "rb") as f:
                        st.download_button("تحميل PDF", f, file_name=pdf_name)
                    
                    update_usage(st.session_state.user)
                    add_log(st.session_state.user, uploaded_file.name, "نجاح", archive_path)
                else:
                    st.error("فشل التحويل")
                    add_log(st.session_state.user, uploaded_file.name, "فشل تقني", archive_path)
                    
            except Exception as e:
                st.error(f"خطأ: {e}")
                add_log(st.session_state.user, uploaded_file.name, f"خطأ: {str(e)}", archive_path)
            
            shutil.rmtree(work_dir, ignore_errors=True)
