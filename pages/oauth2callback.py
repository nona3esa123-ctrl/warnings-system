import streamlit as st
from utils.oauth import exchange_code_for_credentials, save_credentials

st.set_page_config(page_title="جاري تسجيل الدخول...", page_icon="🔐")

st.markdown("""
<div style="text-align:center; padding:50px;">
    <h2>🔐 جاري إتمام تسجيل الدخول...</h2>
</div>
""", unsafe_allow_html=True)

# استقبال الكود من URL
query_params = st.query_params
code = query_params.get("code")
error = query_params.get("error")

if error:
    st.error(f"❌ فشل تسجيل الدخول: {error}")
    if st.button("🏠 العودة للصفحة الرئيسية"):
        st.switch_page("pages/Admin.py")
    st.stop()

if not code:
    st.error("⚠️ لم يتم العثور على كود التفويض")
    if st.button("🏠 العودة للصفحة الرئيسية"):
        st.switch_page("pages/Admin.py")
    st.stop()

try:
    creds = exchange_code_for_credentials(code)
    save_credentials(creds)
    # مسح الكود من URL
    st.query_params.clear()
    st.success("✅ تم تسجيل الدخول بنجاح! جاري تحويلك...")
    st.balloons()
    import time
    time.sleep(1.5)
    st.switch_page("pages/Admin.py")
except Exception as e:
    st.error(f"❌ خطأ: {e}")
    if st.button("🏠 العودة للصفحة الرئيسية"):
        st.switch_page("pages/Admin.py")
