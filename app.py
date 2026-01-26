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

# --- 1. إعدادات الصفحة والتصميم الفخم ---
st.set_page_config(page_title="Elena AI - Professional", page_icon="👑", layout="wide")

st.markdown("""
    <style>
    /* إخفاء العناصر الافتراضية مع بقاء زر القائمة الجانبية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header { background: rgba(0,0,0,0) !important; }
    
    /* خلفية بريميوم */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }
    
    /* زر الاشتراك فوق على اليمين */
    .upgrade-btn {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: black !important;
        font-weight: bold;
        padding: 8px 15px;
        border-radius: 20px;
        float: right;
    }
    
    .prime-badge {
        background: linear-gradient(45deg, #f39c12, #f1c40f);
        color: black;
        padding: 2px 10px;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. تهيئة الجلسة (البيانات) ---
if "is_logged_in" not in st.session_state: st.session_state.is_logged_in = False
if "user_status" not in st.session_state: st.session_state.user_status = "Standard"
if "courses" not in st.session_state: st.session_state.courses = {}
if "IF_VALID_CODES" not in st.session_state: st.session_state.IF_VALID_CODES = ["ELENA-PRO-2026", "ETHAN-VIP"]

# --- 3. محرك السيلينيوم (Data Engine) ---
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
        p_in = driver.find_element(By.ID, "password")
        p_in.send_keys(password)
        p_in.send_keys(Keys.ENTER)
        time.sleep(10)
        
        if task_type == "timeline":
            body = driver.find_element(By.TAG_NAME, "body").text
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='course/view.php?id=']")
            course_map = {l.text.strip(): l.get_attribute("href") for l in links if len(l.text) > 5}
            return {"text": body, "courses": course_map}
        
        elif task_type == "grades":
            g_url = target_url.replace("course/view.php", "grade/report/user/index.php")
            driver.get(g_url)
            time.sleep(5)
            return {"data": driver.find_element(By.TAG_NAME, "table").text}
            
    except Exception as e: return {"error": str(e)}
    finally: driver.quit()

# --- 4. نظام تسجيل الدخول ---
if not st.session_state.is_logged_in:
    st.markdown("<h1 style='text-align:center;'>🔐 Elena Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            if u == "ethan" and p == "EM2006":
                st.session_state.update({"is_logged_in": True, "user_role": "developer", "user_status": "Prime"})
                st.rerun()
            elif u == "user" and p == "user1234":
                st.session_state.update({"is_logged_in": True, "user_role": "user"})
                st.rerun()
            else: st.error("خطأ في البيانات")
    st.stop()

# --- 5. الواجهة الرئيسية والتبويبات ---
st.markdown(f"### Elena Dashboard " + (f"<span class='prime-badge'>PRIME 👑</span>" if st.session_state.user_status == "Prime" else ""), unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 المخطط", "📚 المقررات", "📊 العلامات", "💬 إيلينا", "🛠️ الإدارة"])

# المخطط
with tab1:
    if st.session_state.courses:
        st.success(f"تم العثور على {len(st.session_state.courses)} مواد مسجلة.")
        st.write("بيانات الجدول الزمني جاهزة للتحليل.")
    else:
        st.info("💡 ابدأ بعمل 'Sync Data' من القائمة الجانبية لسحب بياناتك من الجامعة.")

# المقررات
with tab2:
    if st.session_state.courses:
        st.subheader("📚 روابط المواد والمصادر")
        sel = st.selectbox("اختر المادة:", list(st.session_state.courses.keys()))
        st.info(f"رابط المادة المباشر: [اضغط هنا لدخول المودل]({st.session_state.courses[sel]})")
    else: st.warning("لا توجد بيانات مقررات حالياً.")

# العلامات
with tab3:
    if st.session_state.courses:
        st.subheader("📊 كشف درجات المساقات")
        sel_g = st.selectbox("اختر المادة لعرض علاماتها:", list(st.session_state.courses.keys()), key="grade_sel")
        if st.button("جلب العلامات الآن 🔍"):
            with st.spinner("جاري جلب الدرجات..."):
                res = run_selenium_task(st.session_state.u_id, st.session_state.u_pass, "grades", st.session_state.courses[sel_g])
                if "data" in res: st.text_area("الدرجات:", res['data'], height=200)
                else: st.error("فشل في الوصول لصفحة الدرجات.")
    else: st.error("يرجى عمل مزامنة أولاً لتفعيل صفحة العلامات.")

# إيلينا
with tab4:
    st.chat_input("اسأل إيلينا أي شيء عن دراستك...")

# الإدارة
with tab5:
    if st.session_state.user_role == "developer":
        st.write("أهلاً يا إيثان. إدارة الأكواد:")
        st.write(st.session_state.IF_VALID_CODES)
        new_c = st.text_input("أضف كود جديد")
        if st.button("حفظ الكود"):
            st.session_state.IF_VALID_CODES.append(new_c)
            st.rerun()
    else: st.warning("خاص بالمطور فقط.")

# --- 6. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("⚙️ University Sync")
    st.session_state.u_id = st.text_input("الرقم الجامعي")
    st.session_state.u_pass = st.text_input("كلمة المرور الجامعية", type="password")
    
    if st.button("🚀 Sync My Data"):
        with st.spinner("Elena is fetching data..."):
            res = run_selenium_task(st.session_state.u_id, st.session_state.u_pass, "timeline")
            if "courses" in res:
                st.session_state.courses = res['courses']
                st.success("تم التحديث بنجاح!")
                time.sleep(1)
                st.rerun() # هذا السطر هو اللي بيخلي التبويبات تظهر فوراً
            else: st.error("خطأ في المزامنة")
            
    st.markdown("---")
    if st.session_state.user_status == "Standard":
        with st.expander("👑 Upgrade to Prime"):
            st.write("ادفع عبر جوال باي: 059XXXXXXX")
            code = st.text_input("أدخل كود التفعيل")
            if st.button("تفعيل"):
                if code in st.session_state.IF_VALID_CODES:
                    st.session_state.user_status = "Prime"
                    st.rerun()
