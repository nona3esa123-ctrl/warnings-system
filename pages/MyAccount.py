import streamlit as st
from utils.auth import init_session, change_own_password

st.set_page_config(page_title="حسابي", page_icon="🔑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user:
    st.error("🔐 سجّل الدخول أولاً")
    st.stop()

st.title("🔑 حسابي")

c1, c2, c3 = st.columns(3)
if c1.button("🏠 الرئيسية", use_container_width=True):
    st.switch_page("app.py")
c2.markdown(f"👤 **{user['name']}**")
if c3.button("🚪 خروج", use_container_width=True):
    st.session_state["user"] = None
    st.switch_page("app.py")

st.markdown("---")

st.markdown("### 👤 معلوماتي")
c1, c2 = st.columns(2)
c1.write(f"**الاسم:** {user['name']}")
c1.write(f"**البريد:** {user['email']}")
c2.write(f"**الدور:** {user['role']}")

st.markdown("---")
st.markdown("### 🔐 تغيير كلمة المرور")

with st.form("change_password"):
    old_pass = st.text_input("كلمة المرور الحالية", type="password")
    new_pass = st.text_input("كلمة المرور الجديدة (6 أحرف على الأقل)", type="password")
    confirm_pass = st.text_input("تأكيد كلمة المرور", type="password")
    
    if st.form_submit_button("🔑 تغيير", use_container_width=True):
        if not old_pass or not new_pass or not confirm_pass:
            st.error("⚠️ املأ الحقول")
        elif new_pass != confirm_pass:
            st.error("⚠️ الكلمتان غير متطابقتين")
        elif len(new_pass) < 6:
            st.error("⚠️ 6 أحرف على الأقل")
        else:
            result = change_own_password(user["email"], old_pass, new_pass)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(result["message"])
