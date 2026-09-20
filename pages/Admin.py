import streamlit as st
import pandas as pd
from utils.auth import init_session, hash_password
from utils.sheets import read_tab, append_row, update_row, delete_row, log_action
from utils.drive import list_student_files, upload_file_to_folder, delete_file, rename_file

st.set_page_config(page_title="لوحة المدير", page_icon="👑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user or user["role"] != "مدير":
    st.error("🔐 هذه الصفحة للمدير فقط. سجّل الدخول من الصفحة الرئيسية.")
    st.stop()

st.title("👑 لوحة المدير")

# شريط علوي
c1, c2, c3 = st.columns(3)
if c1.button("🏠 الصفحة الرئيسية", use_container_width=True):
    st.switch_page("app.py")
c2.markdown(f"👤 **{user['name']}**")
if c3.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state["user"] = None
    st.switch_page("app.py")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📁 ملفات الطلاب", "👥 الموظفون", "✍️ التوقيعات", "📜 سجل النشاط"])

# ============ 1. ملفات الطلاب ============
with tab1:
    st.markdown("### 📁 إدارة ملفات الطلاب")
    
    with st.expander("➕ رفع ملف طلاب جديد", expanded=True):
        uploaded = st.file_uploader("اختر ملف Excel (.xlsx)", type=["xlsx"], key="student_file_upload")
        if uploaded is not None:
            st.info(f"📄 الملف: **{uploaded.name}** — الحجم: {uploaded.size/1024:.1f} KB")
            if st.button("📤 رفع الملف", use_container_width=True, type="primary"):
                with st.spinner("جاري الرفع..."):
                    try:
                        fid = upload_file_to_folder(uploaded.getvalue(), uploaded.name)
                        log_action("رفع ملف طلاب", target=uploaded.name, details=f"ID: {fid}")
                        st.cache_data.clear()
                        st.success(f"✅ تم رفع {uploaded.name} بنجاح")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ خطأ في الرفع: {e}")
    
    st.markdown("### 📋 الملفات الحالية")
    files = list_student_files()
    if not files:
        st.info("لا توجد ملفات طلاب في المجلد بعد")
    else:
        for f in files:
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                size = int(f.get('size', 0)) / 1024
                st.write(f"📄 **{f['name']}** — {size:.0f} KB")
            with col2:
                if st.button("✏️ تسمية", key=f"rename_{f['id']}"):
                    st.session_state[f"renaming_{f['id']}"] = True
            with col3:
                if st.button("🗑️ حذف", key=f"delete_{f['id']}"):
                    st.session_state[f"deleting_{f['id']}"] = True
            
            # نموذج التسمية
            if st.session_state.get(f"renaming_{f['id']}"):
                new_name = st.text_input("الاسم الجديد", value=f['name'], key=f"newname_{f['id']}")
                c1, c2 = st.columns(2)
                if c1.button("✅ حفظ", key=f"save_rename_{f['id']}", use_container_width=True):
                    if rename_file(f['id'], new_name):
                        log_action("إعادة تسمية ملف", target=f['name'], details=f"→ {new_name}")
                        st.session_state[f"renaming_{f['id']}"] = False
                        st.cache_data.clear()
                        st.success("✅ تم التحديث")
                        st.rerun()
                if c2.button("❌ إلغاء", key=f"cancel_rename_{f['id']}", use_container_width=True):
                    st.session_state[f"renaming_{f['id']}"] = False
                    st.rerun()
            
            # تأكيد الحذف
            if st.session_state.get(f"deleting_{f['id']}"):
                st.warning(f"⚠️ هل أنت متأكد من حذف **{f['name']}**؟ لا يمكن التراجع!")
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
    st.markdown("### ➕ إضافة موظف جديد")
    with st.form("add_user_form"):
        c1, c2 = st.columns(2)
        new_email = c1.text_input("البريد الإلكتروني", key="new_user_email")
        new_name = c2.text_input("الاسم", key="new_user_name")
        new_password = c1.text_input("كلمة المرور", type="password", key="new_user_pass")
        new_role = c2.selectbox("الدور", ["موظف", "مدير"], key="new_user_role")
        
        if st.form_submit_button("➕ إضافة موظف", use_container_width=True):
            if new_email and new_name and new_password:
                users_df = read_tab("users")
                if not users_df.empty and new_email in users_df["الإيميل"].astype(str).values:
                    st.error("⚠️ هذا البريد موجود بالفعل")
                else:
                    append_row("users", {
                        "الإيميل": new_email,
                        "كلمة المرور": hash_password(new_password),
                        "الاسم": new_name,
                        "الدور": new_role
                    })
                    log_action("إضافة موظف", target=new_email, details=f"الدور: {new_role}")
                    st.success(f"✅ تمت إضافة {new_name}")
                    st.rerun()
            else:
                st.error("⚠️ املأ جميع الحقول")
    
    st.markdown("---")
    st.markdown("### 👥 قائمة الموظفين")
    
    users_df = read_tab("users")
    if users_df.empty:
        st.info("لا يوجد مستخدمون")
    else:
        # عرض كل مستخدم مع زر حذف
        for idx, row in users_df.iterrows():
            real_row_num = idx + 2  # الصف 1 هو الهيدر
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 1, 1])
                c1.write(f"📧 **{row['الإيميل']}**")
                c2.write(f"👤 {row['الاسم']}")
                c3.write(f"🏷️ {row['الدور']}")
                
                # لا يمكن حذف نفسك
                if row['الإيميل'] == user['email']:
                    c4.write("🔒")
                    c5.write("(أنت)")
                else:
                    if c4.button("🗑️", key=f"del_user_{idx}", help="حذف الموظف"):
                        st.session_state[f"confirm_del_user_{idx}"] = True
                    
                    if st.session_state.get(f"confirm_del_user_{idx}"):
                        st.warning(f"⚠️ سيتم حذف **{row['الاسم']}** ({row['الإيميل']}) نهائياً.")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("✅ نعم احذف", key=f"confirm_yes_{idx}", use_container_width=True, type="primary"):
                            try:
                                delete_row("users", real_row_num)
                                log_action("حذف موظف", target=str(row['الإيميل']))
                                st.session_state[f"confirm_del_user_{idx}"] = False
                                st.success("✅ تم الحذف")
                                st.rerun()
                            except Exception as e:
                                st.error(f"خطأ: {e}")
                        if cc2.button("❌ إلغاء", key=f"confirm_no_{idx}", use_container_width=True):
                            st.session_state[f"confirm_del_user_{idx}"] = False
                            st.rerun()
                st.markdown("---")

# ============ 3. التوقيعات ============
with tab3:
    st.markdown("### ✍️ التوقيعات المسجلة")
    st.caption("هذه قائمة بكل الطلاب الذين وقّعوا على علم الإنذار، مع التاريخ والموظف الذي سجّل التوقيع.")
    
    sig_df = read_tab("signatures")
    if sig_df.empty:
        st.info("لا توجد توقيعات مسجلة بعد")
    else:
        # فلترة
        c1, c2 = st.columns(2)
        with c1:
            search = st.text_input("🔍 ابحث بالرقم القومي أو الموظف", key="sig_search")
        
        if search:
            mask = sig_df.astype(str).apply(
                lambda r: r.str.contains(search, case=False, na=False).any(), axis=1
            )
            filtered = sig_df[mask]
        else:
            filtered = sig_df
        
        st.markdown(f"**العدد: {len(filtered)} توقيع**")
        st.dataframe(filtered, use_container_width=True)
        
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 تحميل CSV", csv, "signatures.csv", "text/csv", use_container_width=True)

# ============ 4. سجل النشاط ============
with tab4:
    st.markdown("### 📜 آخر 200 عملية")
    audit_df = read_tab("audit")
    if audit_df.empty:
        st.info("لا توجد عمليات")
    else:
        st.dataframe(audit_df.tail(200).iloc[::-1], use_container_width=True)
        csv = audit_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 تحميل السجل", csv, "audit.csv", "text/csv", use_container_width=True)
