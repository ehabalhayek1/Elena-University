import streamlit as st
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time

# --- 1. إعدادات الأمان والذكاء الاصطناعي ---
st.set_page_config(page_title="Elena AI - Professional Portal", page_icon="🎓", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ يرجى ضبط GEMINI_API_KEY في إعدادات Secrets")

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel("models/gemini-flash-latest")
    st.session_state.chat_session = model.start_chat(history=[])

if "courses" not in st.session_state:
    st.session_state.courses = {}

if "sync_count" not in st.session_state:
    st.session_state.sync_count = 0

# --- 2. محرك البحث المطور ---
def run_selenium_task(username, password, task_type="timeline", course_url=None):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = "/usr/bin/chromium" 
    
    try:
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://sso.iugaza.edu.ps/saml/module.php/core/loginuserpass")
        time.sleep(3)
        
        driver.find_element(By.ID, "username").send_keys(username)
        pass_input = driver.find_element(By.ID, "password")
        pass_input.send_keys(password)
        pass_input.send_keys(Keys.ENTER)
        
        time.sleep(12) 

        if task_type == "timeline":
            timeline_text = driver.find_element(By.TAG_NAME, "body").text
            course_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='course/view.php?id=']")
            courses = {el.text.strip(): el.get_attribute("href") for el in course_elements if len(el.text) > 5}
            return {"text": timeline_text, "courses": courses}

        elif task_type == "course_deep_dive":
            driver.get(course_url)
            time.sleep(5)
            all_links = driver.find_elements(By.CSS_SELECTOR, "a.aalink")
            resources = [{"name": link.text, "url": link.get_attribute("href")} for link in all_links if link.text]
            content = driver.find_element(By.TAG_NAME, "body").text
            return {"text": content, "resources": resources}

        elif task_type == "get_grades":
            grade_url = course_url.replace("course/view.php", "grade/report/user/index.php")
            driver.get(grade_url)
            time.sleep(5)
            grades_table = driver.find_element(By.TAG_NAME, "table").text
            return {"grades": grades_table}

    except Exception as e:
        return {"error": str(e)}
    finally:
        if 'driver' in locals():
            driver.quit()

# --- 3. نظام حماية براءة الاختراع والتحقق من المستخدم ---
def check_login():
    if "is_logged_in" not in st.session_state:
        st.session_state.is_logged_in = False
        st.session_state.user_role = None

    if not st.session_state.is_logged_in:
        st.title("🔐 Elena Protected Portal")
        st.write("مرحباً بك في إيلينا. هذا المشروع محمي بحقوق الملكية للمطور **ايهاب الحايك**.")
        
        user_input = st.text_input("اسم المستخدم", key="login_user")
        pass_input = st.text_input("كلمة السر", type="password", key="login_pass")
        
        if st.button("دخول للنظام"):
            # دخول المطور (إيثان)
            if user_input == "ethan" and pass_input == "EM2006":
                st.session_state.is_logged_in = True
                st.session_state.user_role = "developer"
                st.rerun()
            # دخول المستخدم العادي
            elif user_input == "user" and pass_input == "user1234":
                st.session_state.is_logged_in = True
                st.session_state.user_role = "user"
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة.")
        return False
    return True

# --- 4. واجهة المستخدم الرئيسية ---
if check_login():
    # ترحيب مخصص
    if st.session_state.user_role == "developer":
        st.title("👨‍💻 أهلاً بك يا مطوري (إيثان)")
        limit_text = "Infinity ♾️"
    else:
        st.title("🎓 أهلاً بك في إيلينا")
        remaining = 10 - st.session_state.sync_count
        limit_text = f"{remaining} / 10"
        if remaining <= 0:
            st.error("🚫 استنفدت محاولاتك المجانية. تواصل مع المطور للترقية.")
            st.stop()

    st.caption(f"Role: {st.session_state.user_role} | Sync Limit: {limit_text}")

    with st.sidebar:
        st.header("🔐 User Portal")
        u_id = st.text_input("Student ID")
        u_pass = st.text_input("Password", type="password")
        
        if st.button("🚀 Sync My Data"):
            st.session_state.sync_count += 1
            with st.spinner("Connecting to IUG Portal..."):
                result = run_selenium_task(u_id, u_pass, "timeline")
                if "error" in result:
                    st.error(f"خطأ: {result['error']}")
                else:
                    st.session_state.timeline_data = result['text']
                    st.session_state.courses = result['courses']
                    st.success("تمت المزامنة!")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Smart Planner", "📚 Course Resources", "📊 Grades", "💬 Ask Elena"])

    with tab1:
        if "timeline_data" in st.session_state:
            st.subheader("📝 Study Priority Planner")
            if st.button("📅 Generate My Study Plan"):
                with st.spinner("إيلينا تحلل مواعيدك..."):
                    prompt = f"Extract all deadlines from this text and organize them into a study plan table with (Task, Course, Deadline, Priority): {st.session_state.timeline_data}"
                    resp = st.session_state.chat_session.send_message(prompt)
                    st.session_state.study_plan = resp.text
            
            if "study_plan" in st.session_state:
                st.markdown(st.session_state.study_plan)
        else: st.info("سجل دخولك من القائمة الجانبية أولاً.")

    with tab2:
        if st.session_state.courses:
            selected_course = st.selectbox("اختر المساق للمعاينة:", list(st.session_state.courses.keys()))
            if st.button(f"Fetch Resources for {selected_course}"):
                with st.spinner("Fetching links..."):
                    res = run_selenium_task(u_id, u_pass, "course_deep_dive", st.session_state.courses[selected_course])
                    if "resources" in res:
                        st.session_state.current_content = res['text']
                        for link in res['resources']:
                            st.markdown(f"- [{link['name']}]({link['url']})")
        else: st.info("قم بالمزامنة أولاً.")

    with tab3:
        if st.session_state.courses:
            sel_course_grade = st.selectbox("اختر المساق للدرجات:", list(st.session_state.courses.keys()), key="grade_sel")
            if st.button("Check My Grades"):
                with st.spinner("Accessing Grades..."):
                    grade_res = run_selenium_task(u_id, u_pass, "get_grades", st.session_state.courses[sel_course_grade])
                    if "grades" in grade_res:
                        st.text_area("Grade Report:", grade_res['grades'], height=200)
                        ai_analysis = st.session_state.chat_session.send_message(f"Analyze these grades and give me feedback: {grade_res['grades']}")
                        st.success(ai_analysis.text)
        else: st.info("Sync data first.")

    with tab4:
        if chat_input := st.chat_input("Ask Elena..."):
            response = st.session_state.chat_session.send_message(chat_input)
            st.write(response.text)
