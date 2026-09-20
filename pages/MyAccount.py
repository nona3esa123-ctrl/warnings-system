import streamlit as st
from utils.auth import init_session, change_own_password

st.set_page_config(page_title="حسابي", page_icon="🔑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user:
    st.error("🔐 سجّل الدخول أولاً من الصفحة الرئيسية.")
    st.stop()

st.title("🔑 حسابي")

c1, c2, c3 = st.columns(3)
if c1.button("🏠 الصفحة الرئيسية", use_container_width=True):
    st.switch_page("app.py")
c2.markdown(f"👤 **{user['name']}**")
if c3.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state["user"] = None
    st.switch_page("app.py")

st.markdown("---")

st.markdown("### 👤 معلوماتي")
c1, c2 = st.columns(2)
c1.write(f"**الاسم:** {user['name']}")
c1.write(f"**البريد الإلكتروني:** {user['email']}")
c2.write(f"**الدور:** {user['role']}")

st.markdown("---")

st.markdown("### 🔐 تغيير كلمة المرور")
st.info("💡 يُنصح بتغيير كلمة المرور بشكل دوري، وبعد أول دخول لك.")

with st.form("change_password_form"):
    old_pass = st.text_input("كلمة المرور الحالية", type="password")
    new_pass = st.text_input("كلمة المرور الجديدة (6 أحرف على الأقل)", type="password")
    confirm_pass = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
    
    submitted = st.form_submit_button("🔑 تغيير كلمة المرور", use_container_width=True)
    
    if submitted:
        if not old_pass or not new_pass or not confirm_pass:
            st.error("⚠️ املأ جميع الحقول")
        elif new_pass != confirm_pass:
            st.error("⚠️ كلمتا المرور غير متطابقتين")
        elif len(new_pass) < 6:
            st.error("⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
        else:
            result = change_own_password(user["email"], old_pass, new_pass)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["message"])
                st.balloons()
