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
    
    .locked-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =======================
# 2. إدارة البيانات (JSON)
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

def add_log(phone, name, filename, status, archived_path=None):
    logs = load_json(LOGS_FILE)
    if not isinstance(logs, list): logs = []
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "phone": phone,
        "name": name,
        "filename": filename,
        "status": status,
        "archived_path": archived_path
    }
    logs.insert(0, entry)
    save_json(LOGS_FILE, logs)

# إعداد الأدمن (رقم الهاتف: admin)
users = load_json(USERS_FILE)
if "admin" not in users:
    users["admin"] = {
        "name": "المدير العام",
        "password": hash_pass("admin123"),
        "daily_used": 0,
        "last_day": datetime.now().strftime("%Y-%m-%d"),
        "role": "admin",
        "blocked": False,
        "is_vip": True
    }
    save_json(USERS_FILE, users)

# =======================
# 3. دوال النظام
# =======================
def check_libreoffice():
    if shutil.which("libreoffice") or shutil.which("soffice"): return True
    return False

def can_convert(phone):
    users = load_json(USERS_FILE)
    user = users.get(phone)
    if not user: return False, "غير موجود"
    if user.get("blocked", False): return False, "محظور"
    if user.get("is_vip", False) or user.get("role") == "admin": return True, "VIP"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_day"] != today:
        user["daily_used"] = 0
        user["last_day"] = today
        save_json(USERS_FILE, users)
    
    if user["daily_used"] >= 5: return False, "انتهى رصيدك اليومي (5 ملفات)"
    return True, ""

def update_usage(phone):
    users = load_json(USERS_FILE)
    if phone in users:
        users[phone]["daily_used"] += 1
        save_json(USERS_FILE, users)

# =======================
# 4. إدارة الجلسة (Session)
# =======================
if "user_phone" not in st.session_state:
    st.session_state.user_phone = None # رقم الهاتف هو المعرف
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# متغير لتخزين الملف المحول الذي ينتظر التسجيل
if "pending_file" not in st.session_state:
    st.session_state.pending_file = None # {path: "...", name: "..."}

# =======================
# 5. الواجهة الرئيسية
# =======================

# --- شريط علوي ---
if st.session_state.user_phone:
    c1, c2 = st.columns([5,1])
    with c1: st.success(f"👤 أهلاً، **{st.session_state.user_name}**")
    with c2: 
        if st.button("خروج"):
            st.session_state.user_phone = None
            st.session_state.user_name = None
            st.session_state.pending_file = None
            st.rerun()
else:
    st.markdown("<h3 style='text-align: center;'>🔁 عون - محول الملفات</h3>", unsafe_allow_html=True)

# =======================
# 6. لوحة الأدمن (فقط للمدير)
# =======================
users = load_json(USERS_FILE)
if st.session_state.user_phone and users.get(st.session_state.user_phone, {}).get("role") == "admin":
    st.markdown("---")
    st.title("🛠️ لوحة التحكم")
    view = st.radio("القسم:", ["👥 المستخدمين", "📊 السجلات"], horizontal=True)
    
    if view == "👥 المستخدمين":
        # عرض البيانات بشكل نظيف
        clean_data = []
        for ph, data in users.items():
            if ph == "admin": continue
            clean_data.append({
                "رقم الهاتف": ph,
                "الاسم": data.get("name", ""),
                "الاستهلاك": data.get("daily_used", 0),
                "محظور": data.get("blocked", False),
                "VIP": data.get("is_vip", False)
            })
        st.dataframe(pd.DataFrame(clean_data), use_container_width=True)
        
        st.divider()
        st.caption("تعديل مستخدم:")
        sel_ph = st.selectbox("اختر برقم الهاتف:", [k for k in users.keys() if k != "admin"])
        if sel_ph:
            c1, c2, c3 = st.columns(3)
            with c1:
                is_blk = users[sel_ph]["blocked"]
                if st.button(f"{'فك الحظر' if is_blk else '⛔ حظر'}", key="blk", use_container_width=True):
                    users[sel_ph]["blocked"] = not is_blk
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c2:
                if st.button("🔄 تصفير العداد", key="rst", use_container_width=True):
                    users[sel_ph]["daily_used"] = 0
                    save_json(USERS_FILE, users)
                    st.rerun()
            with c3:
                is_vip = users[sel_ph].get("is_vip", False)
                if st.button(f"{'إلغاء VIP' if is_vip else '⭐ ترقية VIP'}", key="vip", use_container_width=True):
                    users[sel_ph]["is_vip"] = not is_vip
                    save_json(USERS_FILE, users)
                    st.rerun()

    elif view == "📊 السجلات":
        logs = load_json(LOGS_FILE)
        for l in logs:
            with st.expander(f"{l['timestamp']} | {l['name']} ({l['phone']})"):
                st.write(f"📂 الملف: {l['filename']}")
                st.write(f"النتيجة: {l['status']}")
                if l.get("archived_path") and os.path.exists(l["archived_path"]):
                    with open(l["archived_path"], "rb") as f:
                        st.download_button("📥 تحميل الأصل", f, file_name=f"ARC_{l['filename']}")
        
        if st.button("🗑️ حذف الأرشيف", type="primary"):
            shutil.rmtree(ARCHIVE_DIR)
            os.makedirs(ARCHIVE_DIR)
            st.rerun()

# =======================
# 7. واجهة التحويل (للكل)
# =======================
else:
    # التحقق من LibreOffice
    if not check_libreoffice():
        st.error("⚠️ خطأ بالنظام: LibreOffice غير مثبت.")
        st.stop()

    # إذا كان هناك ملف معلق (تم تحويله ولكن لم يسجل الدخول بعد)
    if st.session_state.pending_file and not st.session_state.user_phone:
        st.markdown(f"""
        <div class="success-box">
            ✅ تم تحويل الملف: <b>{st.session_state.pending_file['name']}</b> بنجاح!
        </div>
        <div class="locked-box">
            🔒 <b>الملف جاهز للتحميل</b><br>
            من فضلك قم بتسجيل بياناتك بالأسفل لتحميل الملف فوراً.
        </div>
        """, unsafe_allow_html=True)

        # فورم التسجيل/الدخول الإجباري
        t1, t2 = st.tabs(["تسجيل جديد (أول مرة)", "دخول (لدي حساب)"])
        
        with t1:
            r_name = st.text_input("الاسم الثلاثي", key="r_n")
            r_phone = st.text_input("رقم الهاتف (سيكون اسم المستخدم)", key="r_ph")
            r_pass = st.text_input("كلمة المرور", type="password", key="r_p")
            
            if st.button("تسجيل وتحميل الملف 🚀", type="primary"):
                users = load_json(USERS_FILE)
                if r_phone in users:
                    st.warning("رقم الهاتف مسجل مسبقاً، حاول تسجيل الدخول.")
                elif not r_name or not r_phone or not r_pass:
                    st.warning("جميع البيانات مطلوبة.")
                else:
                    # إنشاء حساب
                    users[r_phone] = {
                        "name": r_name,
                        "password": hash_pass(r_pass),
                        "daily_used": 0, # سيتم خصم 1 لاحقاً
                        "last_day": datetime.now().strftime("%Y-%m-%d"),
                        "role": "user",
                        "blocked": False,
                        "is_vip": False
                    }
                    save_json(USERS_FILE, users)
                    # تسجيل دخول تلقائي
                    st.session_state.user_phone = r_phone
                    st.session_state.user_name = r_name
                    st.rerun()

        with t2:
            l_phone = st.text_input("رقم الهاتف", key="l_ph")
            l_pass = st.text_input("كلمة المرور", type="password", key="l_p")
            if st.button("دخول وتحميل"):
                users = load_json(USERS_FILE)
                if l_phone in users and users[l_phone]["password"] == hash_pass(l_pass):
                    st.session_state.user_phone = l_phone
                    st.session_state.user_name = users[l_phone].get("name", "مستخدم")
                    st.rerun()
                else:
                    st.error("بيانات خاطئة")

    # إذا كان المستخدم مسجل دخول ولديه ملف معلق (أو يرفع ملف جديد)
    else:
        # إذا كان هناك ملف معلق وتم تسجيل الدخول للتو -> أظهر زر التحميل
        if st.session_state.pending_file:
            st.markdown(f"<div class='success-box'>🎉 أهلاً {st.session_state.user_name}، ملفك جاهز!</div>", unsafe_allow_html=True)
            
            p_file = st.session_state.pending_file
            if os.path.exists(p_file["path"]):
                with open(p_file["path"], "rb") as f:
                    st.download_button(
                        label="⬇️ تحميل الملف الآن",
                        data=f,
                        file_name=p_file["pdf_name"],
                        mime="application/pdf",
                        type="primary"
                    )
                
                # زر لبدء ملف جديد
                if st.button("تحويل ملف آخر"):
                    st.session_state.pending_file = None
                    update_usage(st.session_state.user_phone) # خصم الرصيد عند استلام الملف
                    st.rerun()
            else:
                st.error("عذراً، انتهت صلاحية الملف. حاول رفعه مرة أخرى.")
                st.session_state.pending_file = None

        # واجهة الرفع العادية (إذا لم يكن هناك ملف جاهز)
        else:
            if st.session_state.user_phone:
                st.info(f"رصيدك اليومي المتبقي: {5 - users[st.session_state.user_phone].get('daily_used', 0)}")
            
            uploaded_file = st.file_uploader("ارفع ملف (Word, Excel, PPT)", type=["docx", "doc", "pptx", "ppt", "xlsx", "xls"])

            if uploaded_file and st.button("تحويل 🚀", type="primary"):
                # 1. إذا كان مسجل دخول، تحقق من الرصيد أولاً
                if st.session_state.user_phone:
                    allowed, msg = can_convert(st.session_state.user_phone)
                    if not allowed:
                        st.error(msg)
                        st.stop()

                # 2. عملية التحويل (تتم للجميع سواء زائر أو مسجل)
                with st.spinner("جاري التحويل..."):
                    uid = str(uuid.uuid4())
                    work_dir = os.path.join(TEMP_DIR, uid)
                    os.makedirs(work_dir, exist_ok=True)
                    
                    in_path = os.path.join(work_dir, uploaded_file.name)
                    with open(in_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    
                    # الأرشفة (مطلوبة للأدمن) - نسجلها باسم مؤقت إذا كان زائر
                    u_name = st.session_state.user_name if st.session_state.user_name else "Guest"
                    u_phone = st.session_state.user_phone if st.session_state.user_phone else "Unknown"
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    arc_path = os.path.join(ARCHIVE_DIR, f"{ts}_{u_phone}_{uploaded_file.name}")
                    shutil.copy(in_path, arc_path)

                    try:
                        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", in_path, "--outdir", work_dir], check=True)
                        pdf_name = uploaded_file.name.rsplit(".", 1)[0] + ".pdf"
                        pdf_path = os.path.join(work_dir, pdf_name)
                        
                        if os.path.exists(pdf_path):
                            # تم التحويل بنجاح!
                            # حفظ البيانات في الـ Session
                            st.session_state.pending_file = {
                                "path": pdf_path,
                                "name": uploaded_file.name,
                                "pdf_name": pdf_name,
                                "archive": arc_path
                            }
                            
                            # تسجيل السجل
                            add_log(u_phone, u_name, uploaded_file.name, "نجاح (بانتظار التحميل)", arc_path)
                            
                            # إعادة تشغيل الصفحة لتفعيل منطق "الملف المعلق"
                            st.rerun()
                        else:
                            st.error("فشل التحويل من المصدر.")
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")

