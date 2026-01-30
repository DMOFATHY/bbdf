import streamlit as st
import subprocess
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ===================== إعدادات =====================
APP_TITLE_AR = "📄 محول الملفات إلى PDF"
APP_TITLE_EN = "📄 Offline Office-to-PDF Converter"
DEVELOPER = "تطوير: محمد فتحي أبو الجيلاني | Developed by Mohamed Fathy Abu El-Gelany"

WORK_DIR = Path("temp_convert")
USERS_FILE = Path("users.json")
HISTORY_FILE = Path("history.json")
ALLOWED_TYPES = ['docx','doc','pptx','ppt','xlsx','xls']

GUEST_FIRST_FILE = 1
GUEST_LIMIT = 5
PAID_FILES = 100
PAID_PRICE = 25  # EGP

# ===================== أدوات =====================
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def load_json(file): return json.load(open(file,"r",encoding="utf-8")) if file.exists() else {}
def save_json(file, data): json.dump(data, open(file,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

users = load_json(USERS_FILE)
history = load_json(HISTORY_FILE)

# ===================== إعداد الصفحة =====================
st.set_page_config(page_title=APP_TITLE_EN, page_icon="📄")

st.markdown("""
<style>
.stApp { background:#F8FAFC; color:#0F172A; font-family:Arial; }
h1,h2,h3 { color:#0F172A; }
.stButton>button { background:#22C55E; color:black; border-radius:10px; font-weight:bold }
.card { background:#FFFFFF; border:1px solid #22C55E; padding:15px; border-radius:12px; margin-bottom:10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# ===================== Session =====================
if "login" not in st.session_state: st.session_state.login = False
if "guest_used" not in st.session_state: st.session_state.guest_used = 0
if "visited" not in st.session_state: st.session_state.visited = False
if "lang" not in st.session_state: st.session_state.lang = "ar"

# ===================== لغة =====================
lang = st.session_state.lang
col1, col2 = st.columns(2)
with col1: 
    if st.button("🇦🇪 عربي"): st.session_state.lang="ar"; st.experimental_rerun()
with col2: 
    if st.button("🇬🇧 English"): st.session_state.lang="en"; st.experimental_rerun()

def t(ar,en): return ar if st.session_state.lang=="ar" else en

# ===================== تسجيل / إنشاء =====================
if not st.session_state.login:
    t1,t2 = st.tabs([t("🔐 تسجيل الدخول","🔐 Login"), t("🆕 إنشاء حساب","🆕 Register")])
    with t1:
        u = st.text_input(t("اسم المستخدم","Username"))
        p = st.text_input(t("كلمة السر","Password"), type="password")
        if st.button(t("دخول","Login")):
            if u in users and users[u]["pw"]==hash_pw(p):
                st.session_state.login=True
                st.session_state.user=u
                st.rerun()
            else: st.error(t("بيانات غير صحيحة","Invalid credentials"))
    with t2:
        nu = st.text_input(t("اسم مستخدم جديد","New Username"))
        np = st.text_input(t("كلمة سر","New Password"), type="password")
        if st.button(t("إنشاء الحساب","Create Account")):
            if nu in users: st.warning(t("الاسم موجود","Username already exists"))
            elif len(np)<4: st.warning(t("كلمة السر قصيرة","Password too short"))
            else:
                users[nu] = {
                    "pw": hash_pw(np),
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "files_remaining": PAID_FILES,
                    "total_converted": 0,
                    "subscription_status": "Active",
                    "subscription_date": datetime.now().strftime("%Y-%m-%d")
                }
                save_json(USERS_FILE, users)
                st.success(t("تم إنشاء الحساب! يمكنك التحويل الآن","Account created! Unlimited conversions activated."))
    st.stop()

# ===================== Sidebar =====================
with st.sidebar:
    st.write(f"👤 {st.session_state.user if st.session_state.login else t('زائر','Guest')}")
    if st.session_state.login:
        if st.button(t("🗑️ حذف الحساب","🗑️ Delete Account")):
            del users[st.session_state.user]
            save_json(USERS_FILE, users)
            st.session_state.login=False
            st.rerun()
    if st.button(t("🚪 تسجيل الخروج","🚪 Logout")):
        st.session_state.login=False
        st.rerun()

# ===================== رسالة الصدقة =====================
if not st.session_state.visited:
    st.session_state.visited=True
    st.markdown(f"<div class='card'>🕊️ {t('صدقة جارية على روح جدتي','Sadaqa Jariya for my grandmother 💖')}</div>", unsafe_allow_html=True)

# ===================== Header =====================
st.title(t(APP_TITLE_AR,APP_TITLE_EN))
st.caption(DEVELOPER)
st.divider()

# ===================== التحويل =====================
uploaded = st.file_uploader(t("📤 اختر الملف","📤 Select your file"), type=ALLOWED_TYPES)

def convert(file):
    WORK_DIR.mkdir(exist_ok=True)
    path = WORK_DIR / file.name.replace(" ","_")
    open(path,"wb").write(file.getbuffer())
    subprocess.run(["libreoffice","--headless","--convert-to","pdf", str(path),"--outdir",str(WORK_DIR)])
    pdf = WORK_DIR / (path.stem+".pdf")
    shutil.rmtree(WORK_DIR)
    return pdf if pdf.exists() else None

can_convert = True
if not st.session_state.login:
    if st.session_state.guest_used < GUEST_FIRST_FILE:
        st.info(t("يمكنك تحويل ملف واحد مجانًا","You can convert 1 file for free"))
    elif st.session_state.guest_used < GUEST_LIMIT:
        st.info(t(f"لديك {GUEST_LIMIT-st.session_state.guest_used} تحويلات مجانية قبل الاشتراك",
                  f"You have {GUEST_LIMIT-st.session_state.guest_used} free conversions before subscription"))
    else:
        st.warning(t(f"لقد وصلت للحد المجاني. اشترك {PAID_PRICE} جنيه لتحويل {PAID_FILES} ملف",
                      f"You reached free limit. Subscribe {PAID_PRICE} EGP for {PAID_FILES} conversions"))
        can_convert=False

if uploaded and can_convert and st.button(t("🚀 تحويل","🚀 Convert to PDF")):
    pdf = convert(uploaded)
    if pdf:
        st.success(t("تم التحويل بنجاح!","Conversion successful!"))
        st.download_button(t("📥 تحميل PDF","📥 Download PDF"), open(pdf,"rb"), pdf.name)
        # Update counts
        if st.session_state.login:
            users[st.session_state.user]["total_converted"]+=1
            if users[st.session_state.user]["subscription_status"]=="Active":
                users[st.session_state.user]["files_remaining"]-=1
            save_json(USERS_FILE, users)
            user=st.session_state.user
        else:
            st.session_state.guest_used+=1
            user=f"Guest_{st.session_state.guest_used}"
        history.setdefault(user,[]).append({"file":uploaded.name,"time":datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_json(HISTORY_FILE,history)
    else: st.error(t("فشل التحويل","Conversion failed!"))

# ===================== البروفايل =====================
if st.session_state.login:
    st.divider()
    st.markdown(t("## 👤 البروفايل","## 👤 Profile"))
    u=users[st.session_state.user]
    st.markdown(f"<div class='card'>📅 {t('تاريخ الحساب','Account created')}: {u['created']}<br>📄 {t('إجمالي التحويلات','Total conversions')}: {u['total_converted']}<br>🗂️ {t('عدد الملفات المتبقية','Files remaining')}: {u['files_remaining']}</div>", unsafe_allow_html=True)
    if st.session_state.user in history:
        st.markdown(t("## 🗂️ سجل التحويلات","## 🗂️ Conversion History"))
        for h in history[st.session_state.user][::-1]:
            st.markdown(f"<div class='card'>📄 {h['file']}<br>🕒 {h['time']}</div>", unsafe_allow_html=True)

# ===================== مشاركة =====================
st.divider()
st.markdown(t("## 🔗 شارك التطبيق","## 🔗 Share this app"))
st.code(t("شارك التطبيق – ولك الأجر 🤍","Share the link and earn rewards 🤍"))

st.caption("© 2026 | Sadaqa Jariya")
