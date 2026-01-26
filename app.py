import streamlit as st
import smtplib
import random
import json
import os
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from email.message import EmailMessage
import time

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="Elena AI", page_icon="👑", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: white; }
    [data-testid="stSidebar"] { background-color: rgba(15, 12, 41, 0.8); }
    .login-box {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 215, 0, 0.3);
        text-align: center;
    }
    .prime-badge { background: linear-gradient(45deg, #f39c12, #f1c40f); color: black; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الجلسة والداتا ---
if "is_logged_in" not in st.session_state: st.session_state.is_logged_in = False
if "user_status" not in st.session_state: st.session_state.user_status = "Standard"
if "courses" not in st.session_state: st.session_state.courses = {}
if "timeline_data" not in st.session_state: st.session_state.timeline_data = ""
if "IF_VALID_CODES" not in st.session_state: st.session_state.IF_VALID_CODES = ["ELENA-PRO-2026", "ETHAN-VIP"]

EMAIL_ADDRESS = "ehabalhayekm@gmail.com" 
EMAIL_PASSWORD = "hvvh duch onfd xxdv" 
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

def send_otp(target_email, code):
    msg = EmailMessage()
    msg.set_content(f"كود التحقق الخاص بك لمنصة إيلينا هو: {code}")
    msg['Subject'] = "تفعيل حساب إيلينا AI"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = target_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except: return False

def run_selenium_task(username, password, task_type="timeline", target_url=None):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.binary_location = "/usr/bin/chromium" 
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://sso.iugaza.edu.ps/saml/module.php/core/loginuserpass")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(username)
        p_field = driver.find_element(By.ID, "password")
        p_field.send_keys(password)
        p_field.send_keys(Keys.ENTER)
        time.sleep(8)
        if task_type == "timeline":
            body = driver.find_element(By.TAG_NAME, "body").text
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='course/view.php?id=']")
            course_map = {l.text.strip(): l.get_attribute("href") for l in links if len(l.text) > 5}
            return {"text": body, "courses": course_map}
        elif task_type == "grades":
            g_url = target_url.replace("course/view.php", "grade/report/user/index.php")
            driver.get(g_url)
            time.sleep(4)
            return {"data": driver.find_element(By.TAG_NAME, "table").text}
    except Exception as e: return {"error": str(e)}
    finally: driver.quit()

# --- 4. واجهة تسجيل الدخول المطورة ---
if not st.session_state.is_logged_in:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h1 style='color: #FFD700;'>👑 Elena AI Portal</h1>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 تسجيل دخول", "📝 تسجيل جديد"])
        db = load_db()

        with tab_login:
            u = st.text_input("اسم المستخدم", key="l_u")
            p = st.text_input("كلمة السر", type="password", key="l_p")
            col_in, col_forgot = st.columns(2)
            
            if col_in.button("دخول للنظام", use_container_width=True):
                if u == "ethan" and p == "EM2006":
                    st.session_state.update({"is_logged_in": True, "user_role": "developer", "user_status": "Prime", "username": "Ethan"})
                    st.rerun()
                elif u in db and db[u]['password'] == p:
                    st.session_state.update({"is_logged_in": True, "user_role": "user", "user_status": db[u]['status'], "username": u})
                    st.rerun()
                else: st.error("بيانات خاطئة!")

            if col_forgot.button("نسيت كلمة السر؟", use_container_width=True):
                st.session_state.show_reset = True

            if st.session_state.get("show_reset"):
                st.markdown("---")
                re_e = st.text_input("إيميلك المسجل:")
                if st.button("إرسال كود الاستعادة"):
                    user_found = next((user for user, info in db.items() if info.get('email') == re_e), None)
                    if user_found:
                        otp = random.randint(1000, 9999)
                        if send_otp(re_e, otp):
                            st.session_state.reset_otp, st.session_state.reset_user = otp, user_found
                            st.success("تم إرسال الكود!")
                        else: st.error("خطأ في الإرسال")
                    else: st.error("الإيميل غير مسجل")
                
                if "reset_otp" in st.session_state:
                    c_in = st.text_input("الكود:")
                    n_p = st.text_input("كلمة سر جديدة:", type="password")
                    if st.button("تأكيد التغيير"):
                        if c_in == str(st.session_state.reset_otp):
                            db[st.session_state.reset_user]['password'] = n_p
                            save_db(db)
                            st.success("تم التحديث!")
                            del st.session_state.show_reset
                        else: st.error("الكود خطأ")

        with tab_signup:
            nu, ne, np = st.text_input("اسم مستخدم"), st.text_input("Gmail"), st.text_input("كلمة سر", type="password")
            if st.button("إرسال كود التحقق 📧"):
                if nu in db: st.error("موجود مسبقاً")
                elif not ne.endswith("@gmail.com"): st.warning("استخدم Gmail")
                else:
                    otp = random.randint(1000, 9999)
                    if send_otp(ne, otp):
                        st.session_state.temp_otp, st.session_state.temp_data = otp, {"u": nu, "p": np, "e": ne}
                        st.success("تفقد إيميلك")
            
            if "temp_otp" in st.session_state:
                otp_in = st.text_input("أدخل الكود:")
                if st.button("تأكيد الحساب"):
                    if otp_in == str(st.session_state.temp_otp):
                        d = st.session_state.temp_data
                        db[d['u']] = {"password": d['p'], "email": d['e'], "status": "Standard", "sync_count": 0}
                        save_db(db)
                        st.success("تم! سجل دخولك الآن.")
                        del st.session_state.temp_otp
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. الواجهة الرئيسية ---
db = load_db()
current_u = st.session_state.get("username", "user")
if current_u in db:
    st.session_state.user_status = db[current_u].get("status", "Standard")
    user_syncs = db[current_u].get("sync_count", 0)
else: user_syncs = 0

badge = '<span class="prime-badge">PRIME 👑</span>' if st.session_state.user_status == "Prime" else ""
st.markdown(f"## Elena Student AI {badge}", unsafe_allow_html=True)

# حماية الليمت
if st.session_state.user_role != "developer" and st.session_state.user_status != "Prime":
    remaining = 10 - user_syncs
    st.sidebar.metric("المزامنات المتبقية", f"{remaining} / 10")
    if remaining <= 0:
        st.error("🚫 انتهت محاولاتك المجانية. يرجى الترقية.")
        up_c = st.text_input("كود التفعيل:")
        if st.button("تفعيل"):
            if up_c in st.session_state.IF_VALID_CODES:
                db[current_u]["status"] = "Prime"
                save_db(db)
                st.rerun()
        st.stop()

tabs = st.tabs(["📅 المخطط الذكي", "📚 المقررات", "📊 الدرجات", "💬 Ask Elena", "🛠️ الإدارة"])

with tabs[2]: # الدرجات
    if st.session_state.courses:
        sel_g = st.selectbox("المادة:", list(st.session_state.courses.keys()))
        if st.button("جلب الدرجات 📈"):
            res = run_selenium_task(st.session_state.u_id, st.session_state.u_pass, "grades", st.session_state.courses[sel_g])
            if "data" in res: st.text_area("الدرجات:", res['data'], height=200)
    else: st.info("قم بالمزامنة أولاً.")

with st.sidebar:
    st.header("⚙️ المزامنة")
    uid = st.text_input("الرقم الجامعي")
    upass = st.text_input("كلمة المرور", type="password")
    if st.button("🚀 Sync Now"):
        res = run_selenium_task(uid, upass, "timeline")
        if "courses" in res:
            st.session_state.update({"courses": res['courses'], "timeline_data": res['text'], "u_id": uid, "u_pass": upass})
            if st.session_state.user_role != "developer":
                db[current_u]["sync_count"] = db.get(current_u, {}).get("sync_count", 0) + 1
                save_db(db)
            st.rerun()

    if st.session_state.user_status == "Standard":
        c_in = st.text_input("كود البريميوم")
        if st.button("تفعيل"):
            if c_in in st.session_state.IF_VALID_CODES:
                st.session_state.user_status = "Prime"
                st.session_state.IF_VALID_CODES.remove(c_in) # استخدام لمرة واحدة
                st.rerun()








