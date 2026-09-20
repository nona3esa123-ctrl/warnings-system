import streamlit as st
from utils.auth import init_session, authenticate, create_default_admin
from utils.warnings import find_student, get_signature

st.set_page_config(page_title="نظام الإنذارات", page_icon="📘", layout="wide")
init_session()

st.markdown("""
<style>
    * { font-family: 'Cairo', 'Tahoma', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1a3a5c, #2b7a62);
        color: white; padding: 25px; border-radius: 15px;
        text-align: center; margin-bottom: 25px;
    }
    .stButton > button {
        background-color: #2b7a62; color: white;
        border-radius: 8px; padding: 10px 20px; font-weight: bold;
    }
    .student-alert {
        background: #fff5f5; border: 2px solid #e53e3e;
        border-radius: 10px; padding: 20px; margin-top: 20px;
        text-align: center; color: #9b2c2c; font-size: 18px;
    }
    .success-box { background:#d1fae5; color:#065f46; padding:15px; border-radius:8px; text-align:center; font-weight:bold; margin:10px 0;}
    .error-box { background:#fee2e2; color:#991b1b; padding:15px; border-radius:8px; text-align:center; font-weight:bold; margin:10px 0;}
    .warning-box { background:#fef3c7; color:#92400e; padding:15px; border-radius:8px; text-align:center; font-weight:bold; margin:10px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📘 نظام متابعة الإنذارات الأكاديمية</h1>
    <p>كلية علوم الرياضة - بنين</p>
</div>
""", unsafe_allow_html=True)

try:
    create_default_admin()
except Exception:
    pass

tab1, tab2 = st.tabs(["🔍 عرض بياناتي (طالب)", "🖊️ تسجيل توقيع (موظف)"])

# ============ تبويب الطالب ============
with tab1:
    col1, col2 = st.columns([4, 1])
    with col1:
        student_id = st.text_input("الرقم القومي", max_chars=14, placeholder="أدخل الرقم القومي (14 رقم)", label_visibility="collapsed")
    with col2:
        search_btn = st.button("🔍 عرض بياناتي", use_container_width=True, key="search_student")

    if search_btn:
        if not student_id:
            st.warning("⚠️ الرجاء إدخال الرقم القومي")
        else:
            with st.spinner("جاري البحث..."):
                student = find_student(student_id)
                signature = get_signature(student_id)
            if student is None:
                st.markdown('<div class="error-box">⚠️ لم يتم العثور على طالب بهذا الرقم القومي</div>', unsafe_allow_html=True)
            else:
                st.markdown("### 📄 بياناتك")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**الاسم:** {student.get('اسم الطالب', '')}")
                    st.write(f"**كود الطالب:** {student.get('كود الطالب', '')}")
                    st.write(f"**المستوى:** {student.get('المستوى', '')}")
                with c2:
                    st.write(f"**الشعبة:** {student.get('القسم/ الشعبة', '')}")
                    st.write(f"**ساعات الاجتياز:** {student.get('ساعات الاجتياز', '')}")
                    st.write(f"**تراكمى الطالب:** {student.get('تراكمى الطالب', '')}")
                
                if signature is not None:
                    st.markdown(f'<div class="success-box">✅ تم العلم بالإنذار بتاريخ: {signature["التاريخ"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warning-box">⏳ لم يتم التوقيع على علم الإنذار بعد</div>', unsafe_allow_html=True)
                
                try:
                    wc = float(student.get("عدد الانذارات المنفصله", 0))
                except (ValueError, TypeError):
                    wc = 0
                if wc > 0:
                    st.markdown("""
                    <div class="student-alert">
                        <h3>📢 تنبيه هام</h3>
                        <p style="font-size:18px;">
                        برجاء التوجه للإرشاد الأكاديمي لفك الحظر،<br>
                        مع ضرورة إحضار نسخة من إثبات الشخصية.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

# ============ تبويب الموظف ============
with tab2:
    if st.session_state.get("user") is None:
        st.markdown("### 🔐 تسجيل دخول الموظف")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("staff_login"):
                email = st.text_input("📧 البريد الإلكتروني")
                password = st.text_input("🔒 كلمة المرور", type="password")
                if st.form_submit_button("🔓 دخول", use_container_width=True):
                    user = authenticate(email, password)
                    if user and user["role"] in ["مدير", "موظف"]:
                        st.session_state["user"] = user
                        st.rerun()
                    else:
                        st.error("❌ بيانات غير صحيحة")
    else:
        user = st.session_state["user"]
        st.markdown(f"### 👤 مرحباً {user['name']}")
        sid = st.text_input("الرقم القومي للطالب", max_chars=14, key="sign_id")
        if st.button("✅ تسجيل توقيع الطالب", use_container_width=True, key="sign_btn"):
            if not sid:
                st.warning("⚠️ أدخل الرقم القومي")
            else:
                res = sign_warning(sid)
                if "error" in res:
                    st.markdown(f'<div class="error-box">{res["error"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">{res["message"]}</div>', unsafe_allow_html=True)
                    st.balloons()
        
        st.markdown("---")
        if user["role"] == "مدير":
            st.page_link("pages/Admin.py", label="👑 لوحة المدير", icon="👑")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#94a3b8; padding:15px; font-size:14px;">جميع الحقوق محفوظة © كلية علوم الرياضة بنين</div>', unsafe_allow_html=True)
