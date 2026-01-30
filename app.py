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
st.set_page_config(page_title="عون - لوحة التحكم", page_icon="🛠️", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] {direction: rtl; font-family: 'Cairo', sans-serif;}
    .stButton>button {width: 100%; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# =======================
# 2. الدوال الأساسية
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

# =======================
# 3. إصلاح وتجهيز الأدمن (Auto-Fix)
# =======================
users = load_json(USERS_FILE)

# هذا الجزء يقوم بإجبار النظام على تحديث بيانات الأدمن لتكون صحيحة دائماً
# حتى لو كانت كلمة المرور القديمة خطأ، سيتم إصلاحها الآن
users["admin"] = {
    "password": hash_pass("admin123"), # كلمة المرور ثابتة هنا
    "daily_used": 0,
    "last_day": datetime.now().strftime("%Y-%m-%d"),
    "role": "admin",
    "blocked": False,
    "is_vip": True
}
save_json(USERS_FILE, users)

# =======================
# 4. دوال الفحص والتحقق
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
# 5. الواجهة والقائمة الجانبية
# =======================
page_view = "Main" 

with st.sidebar:
    st.title("👤 الحساب")
    
    if "user" not in st.session_state: st.session_state.user = None

    if st.session_state.user:
        u_data = users.get(st.session_state.user, {})
        st.success(f"أهلاً، **{st.session_state.user}**")
        
        if u_data.get("role") == "admin":
            st.markdown("---")
            st.subheader("🔧 الأدمن")
            admin_choice = st.radio("اذهب إلى:", ["👥 إدارة الأعضاء", "📊 السجلات"], index=0)
            page_view = admin_choice
            
        st.markdown("---")
        if st.button("خروج", type="primary"):
            st.session_state.user = None
            st.rerun()

    else:
        tab1, tab2 = st.tabs(["دخول", "جديد"])
        with tab1:
            u = st.text_input("اسم المستخدم", key="l_u")
            p = st.text_input("كلمة المرور", type="password", key="l_p")
            if st.button("تسجيل الدخول"):
                # إعادة التحميل للتأكد من التحديثات
                users = load_json(USERS_FILE) 
                if u in users and users[u]["password"] == hash_pass(p):
                    st.session_state.user = u
                    st.rerun()
                else: st.error("بيانات خاطئة")
        with tab2:
            nu = st.text_input("اسم جديد", key="n_u")
            np = st.text_input("رمز جديد", type="password", key="n_p")
            if st.button("إنشاء حساب"):
                if nu not in users:
                    users[nu] = {"password": hash_pass(np), "daily_used": 0, "last_day": datetime.now().strftime("%Y-%m-%d"), "role": "user", "blocked": False, "is_vip": False}
                    save_json(USERS_FILE, users)
                    st.success("تم الإنشاء")
                else: st.warning("الاسم موجود")

# =======================
# 6. المحتوى الرئيسي
# =======================

if st.session_state.user and users.get(st.session_state.user, {}).get("role") == "admin":
    
    if page_view == "👥 إدارة الأعضاء":
        st.title("👥 إدارة المستخدمين")
        users = load_json(USERS_FILE)
        
        # جدول البيانات
        df_users = pd.DataFrame(users).T.drop("password", axis=1)
        st.dataframe(df_users, use_container_width=True)
        
        st.divider()
        st.write("##### تعديل صلاحيات:")
        sel_user = st.selectbox("اختر عضو:", [u for u in users.keys() if u != "admin"])
        
        if sel_user:
            c1, c2, c3 = st.columns(3)
            with c1:
                is_blk = users[sel_user]["blocked"]
                if st.button(f"{'فك الحظر' if is_blk else '🚫 حظر'}", key="blk", use_container_width=True):
                    users[sel_user]["blocked"] = not is_blk
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c2:
                if st.button("🔄 تصفير العداد", key="rst", use_container_width=True):
                    users[sel_user]["daily_used"] = 0
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c3:
                is_vip = users[sel_user].get("is_vip", False)
                if st.button(f"{'إلغاء VIP' if is_vip else '⭐ ترقية VIP'}", key="vip", use_container_width=True):
                    users[sel_user]["is_vip"] = not is_vip
                    save_json(USERS_FILE, users)
                    st.rerun()

    elif page_view == "📊 السجلات":
        st.title("📊 السجلات والأرشيف")
        logs = load_json(LOGS_FILE)
        if logs:
            for idx, log in enumerate(logs):
                with st.expander(f"{log['timestamp']} - {log['user']}"):
                    st.write(f"الملف: `{log['filename']}` - الحالة: {log['status']}")
                    archived = log.get("archived_path")
                    if archived and os.path.exists(archived):
                        with open(archived, "rb") as f:
                            st.download_button("📥 تحميل الأصل", f, file_name=f"ARCHIVE_{log['filename']}", key=f"dl_{idx}")
            if st.button("تنظيف الأرشيف", type="primary"):
                shutil.rmtree(ARCHIVE_DIR)
                os.makedirs(ARCHIVE_DIR)
                st.rerun()
        else:
            st.info("لا توجد سجلات.")

else:
    # واجهة المستخدم العادي
    st.markdown("## 🔁 محول الملفات")
    if not check_libreoffice():
        st.error("LibreOffice غير مثبت.")
        st.stop()

    uploaded_file = st.file_uploader("اختر ملف", type=["docx", "doc", "pptx", "ppt", "xlsx", "xls"])

    if uploaded_file and st.button("تحويل 🚀", type="primary"):
        if not st.session_state.user:
            st.error("سجل دخولك أولاً.")
            st.stop()
            
        allowed, msg = can_convert(st.session_state.user)
        if not allowed:
            st.error(msg)
            add_log(st.session_state.user, uploaded_file.name, "فشل (الحد)", None)
            st.stop()

        with st.spinner("جاري العمل..."):
            uid = str(uuid.uuid4())
            work = os.path.join(TEMP_DIR, uid)
            os.makedirs(work, exist_ok=True)
            
            in_path = os.path.join(work, uploaded_file.name)
            with open(in_path, "wb") as f: f.write(uploaded_file.getbuffer())
            
            # أرشفة
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            arc_path = os.path.join(ARCHIVE_DIR, f"{ts}_{st.session_state.user}_{uploaded_file.name}")
            shutil.copy(in_path, arc_path)

            try:
                subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", in_path, "--outdir", work], check=True)
                pdf_name = uploaded_file.name.rsplit(".", 1)[0] + ".pdf"
                pdf_path = os.path.join(work, pdf_name)
                
                if os.path.exists(pdf_path):
                    st.success("تم!")
                    with open(pdf_path, "rb") as f: st.download_button("تحميل PDF", f, file_name=pdf_name)
                    update_usage(st.session_state.user)
                    add_log(st.session_state.user, uploaded_file.name, "نجاح", arc_path)
                else:
                    st.error("فشل التحويل")
            except Exception as e:
                st.error(f"خطأ: {e}")
                add_log(st.session_state.user, uploaded_file.name, str(e), arc_path)
            shutil.rmtree(work, ignore_errors=True)
