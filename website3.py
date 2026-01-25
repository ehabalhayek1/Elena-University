import streamlit as st
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- 1. إعدادات الأمان والذكاء الاصطناعي ---
st.set_page_config(page_title="Elena AI - Professional Portal", page_icon="🎓", layout="wide")

# استدعاء مفتاح الـ API بشكل آمن من إعدادات السيرفر
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ يرجى ضبط GEMINI_API_KEY في إعدادات Secrets")

# تهيئة Gemini
if "chat_session" not in st.session_state:
    model = genai.GenerativeModel("models/gemini-flash-latest")
    st.session_state.chat_session = model.start_chat(history=[])

if "courses" not in st.session_state:
    st.session_state.courses = {}

# --- 2. محرك البحث (ضبط السيرفر) ---
def run_selenium_task(username, password, task_type="timeline", course_url=None):
    options = Options()
    options.add_argument('--headless')  # ضروري جداً للسيرفر
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # استخدام DriverManager لتسهيل التشغيل على أي سيرفر
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # تسجيل الدخول
        driver.get("https://sso.iugaza.edu.ps/saml/module.php/core/loginuserpass")
        time.sleep(3)
        
        user_input = driver.find_element(By.ID, "username")
        pass_input = driver.find_element(By.ID, "password")
        
        user_input.send_keys(username)
        pass_input.send_keys(password)
        pass_input.send_keys(Keys.ENTER)
        
        time.sleep(10) # انتظار التحميل في الموديل

        if task_type == "timeline":
            timeline_text = driver.find_element(By.TAG_NAME, "body").text
            course_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='course/view.php?id=']")
            # تصفية الروابط لضمان جودتها
            courses = {el.text.strip(): el.get_attribute("href") for el in course_elements if len(el.text) > 5}
            return {"text": timeline_text, "courses": courses}

        elif task_type == "course_deep_dive":
            driver.get(course_url)
            time.sleep(5)
            course_content = driver.find_element(By.TAG_NAME, "body").text
            return {"text": course_content}

    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

# --- 3. واجهة المستخدم ---
st.title("🎓 Elena Academic AI Assistant")
st.caption("Created by Ethan Marten")

with st.sidebar:
    st.header("🔐 User Portal")
    u_id = st.text_input("Student ID")
    u_pass = st.text_input("Password", type="password")
    
    if st.button("🚀 Sync My Data"):
        with st.spinner("Elena is connecting to IUG Portal..."):
            result = run_selenium_task(u_id, u_pass, "timeline")
            if "error" in result:
                st.error(f"خطأ في الاتصال: {result['error']}")
            else:
                st.session_state.timeline_data = result['text']
                st.session_state.courses = result['courses']
                st.success("تم المزامنة بنجاح!")

tab1, tab2, tab3 = st.tabs(["📅 Timeline", "📚 Course Deep Dive", "💬 Ask Elena"])

with tab1:
    if "timeline_data" in st.session_state:
        if st.button("Analyze My Deadlines"):
            resp = st.session_state.chat_session.send_message(f"Extract deadlines from: {st.session_state.timeline_data}")
            st.info(resp.text)
    else:
        st.write("سجل دخولك من القائمة الجانبية")

with tab2:
    if st.session_state.courses:
        st.subheader("إدارة المساقات")
        selected_course = st.selectbox("اختر المساق:", list(st.session_state.courses.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Summarize {selected_course}"):
                url = st.session_state.courses[selected_course]
                res = run_selenium_task(u_id, u_pass, "course_deep_dive", url)
                if "text" in res:
                    summary = st.session_state.chat_session.send_message(f"Summarize this: {res['text']}")
                    st.success(summary.text)
        with col2:
            # إضافة زر يفتح رابط المساق مباشرة
            st.link_button("🌐 فتح المساق في الموديل", st.session_state.courses[selected_course])
    else:
        st.info("لا توجد بيانات مساقات حالياً.")

with tab3:
    if chat_input := st.chat_input("Ask about your courses..."):
        ctx = st.session_state.get("timeline_data", "")
        response = st.session_state.chat_session.send_message(f"Context: {ctx}\nUser: {chat_input}")
        st.write(response.text)