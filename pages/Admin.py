import streamlit as st
import pandas as pd
from utils.auth import init_session, hash_password
from utils.sheets import read_tab, append_row, delete_row, log_action
from utils.drive import list_student_files, upload_file_to_folder, delete_file, rename_file
from utils.warnings import load_all_students

st.set_page_config(page_title="لوحة المدير", page_icon="👑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user or user["role"] != "مدير":
    st.error("🔐 هذه الصفحة للمدير فقط. سجّل الدخول من الصفحة الرئيسية.")
    st.stop()

st.title("👑 لوحة المدير")

# قائمة سريعة في الأعلى
c1, c2, c3 = st.columns(3)
if c1.button("🏠 الصفحة الرئيسية", use_container_width=True):
    st.switch_page("app.py")
c2.markdown(f"👤 {user['name']}")
if c3.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state["user"] = None
    st.switch_page("app.py")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📁 ملفات الطلاب", "👥 الموظفون", "✍️ التوقيعات", "📜 سجل النشاط"])

# ============ 1. ملفات الطلاب ============
with tab1:
    st.markdown("### 📁 إدارة ملفات الطلاب")
    
    # رفع ملف جديد
    with st.expander("➕ رفع ملف طلاب جديد"):
        uploaded = st.file_uploader("اختر ملف Excel (.xlsx)", type=["xlsx"])
        if uploaded is not None:
            if st.button("📤 رفع الملف", use_container_width=True):
                with st.spinner("جاري الرفع..."):
                    try:
                        fid = upload_file_to_folder(uploaded.getvalue(), uploaded.name)
                        log_action("رفع ملف طلاب", target=uploaded.name, details=f"ID: {fid}")
                        st.cache_data.clear()
                        st.success(f"✅ تم رفع {uploaded.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطأ: {e}")
    
    # قائمة الملفات
    st.markdown("### 📋 الملفات الحالية")
    files = list_student_files()
    if not files:
        st.info("لا توجد ملفات طلاب في المجلد بعد")
    else:
        for f in files:
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                st.write(f"📄 **{f['name']}**")
            with col2:
                if st.button("✏️ تسمية", key=f"rename_{f['id']}"):
                    st.session_state[f"renaming_{f['id']}"] = True
            with col3:
                if st.button("🗑️ حذف", key=f"delete_{f['id']}"):
                    st.session_state[f"deleting_{f['id']}"] = True
            with col4:
                size = int(f.get('size', 0)) / 1024
                st.write(f"{size:.0f} KB")
            
            # نموذج التسمية
            if st.session_state.get(f"renaming_{f['id']}"):
                new_name = st.text_input("الاسم الجديد", value=f['name'], key=f"newname_{f['id']}")
                c1, c2 = st.columns(2)
                if c1.button("حفظ", key=f"save_rename_{f['id']}", use_container_width=True):
                    if rename_file(f['id'], new_name):
                        log_action("إعادة تسمية ملف", target=f['name'], details=f"→ {new_name}")
                        st.session_state[f"renaming_{f['id']}"] = False
                        st.cache_data.clear()
                        st.success("✅ تم التحديث")
                        st.rerun()
                if c2.button("إلغاء", key=f"cancel_rename_{f['id']}", use_container_width=True):
                    st.session_state[f"renaming_{f['id']}"] = False
                    st.rerun()
            
            # تأكيد الحذف
            if st.session_state.get(f"deleting_{f['id']}"):
                st.warning(f"⚠️ هل أنت متأكد من حذف **{f['name']}**؟")
                c1, c2 = st.columns(2)
                if c1.button("✅ نعم احذف", key=f"confirm_del_{f['id']}", use_container_width=True, type="primary"):
                    if delete_file(f['id']):
                        log_action("حذف ملف طلاب", target=f['name'])
                        st.session_state[f"deleting_{f['id']}"] = False
                        st.cache_data.clear()
                        st.success("✅ تم الحذف")
                        st.rerun()
                if c2.button("❌ إلغاء", key=f"cancel_del_{f['id']}", use_container_width=True):
                    st.session_state[f"deleting_{f['id']}"] = False
                    st.rerun()

# ============ 2. الموظفون ============
with tab2:
    with st.form("add_user"):
        st.markdown("### ➕ إضافة موظف")
        c1, c2 = st.columns(2)
        email = c1.text_input("البريد الإلكتروني")
        name = c2.text_input("الاسم")
        password = c1.text_input("كلمة المرور", type="password")
        role = c2.selectbox("الدور", ["موظف", "مدير"])
        if st.form_submit_button("إضافة", use_container_width=True):
            if email and name and password:
                users_df = read_tab("users")
                if not users_df.empty and email in users_df["الإيميل"].astype(str).values:
                    st.error("⚠️ البريد موجود")
                else:
                    append_row("users", {
                        "الإيميل": email,
                        "كلمة المرور": hash_password(password),
                        "الاسم": name,
                        "الدور": role
                    })
                    log_action("إضافة موظف", target=email, details=role)
                    st.success(f"✅ تمت إضافة {name}")
                    st.rerun()
    
    st.markdown("### 👥 الموظفون الحاليون")
    users_df = read_tab("users")
    if users_df.empty:
        st.info("لا يوجد مستخدمون")
    else:
        display = users_df.drop(columns=["كلمة المرور"], errors="ignore")
        st.dataframe(display, use_container_width=True)

# ============ 3. التوقيعات ============
with tab3:
    st.markdown("### ✍️ التوقيعات المسجلة")
    sig_df = read_tab("signatures")
    if sig_df.empty:
        st.info("لا توجد توقيعات بعد")
    else:
        st.dataframe(sig_df, use_container_width=True)
        csv = sig_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 تحميل CSV", csv, "signatures.csv", "text/csv")

# ============ 4. سجل النشاط ============
with tab4:
    st.markdown("### 📜 آخر 200 عملية")
    audit_df = read_tab("audit")
    if audit_df.empty:
        st.info("لا توجد عمليات")
    else:
        st.dataframe(audit_df.tail(200).iloc[::-1], use_container_width=True)
        csv = audit_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 تحميل السجل", csv, "audit.csv", "text/csv")
