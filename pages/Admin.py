import streamlit as st
from utils.auth import init_session, hash_password, admin_reset_password
from utils.sheets import read_tab, append_row, delete_row, log_action
from utils.drive import list_converted_sheets, delete_file

st.set_page_config(page_title="لوحة المدير", page_icon="👑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user or user["role"] != "مدير":
    st.error("🔐 للمدير فقط.")
    st.stop()

st.title("👑 لوحة المدير")

c1, c2, c3 = st.columns(3)
if c1.button("🏠 الرئيسية", use_container_width=True):
    st.switch_page("app.py")
c2.markdown(f"👤 **{user['name']}**")
if c3.button("🚪 خروج", use_container_width=True):
    st.session_state["user"] = None
    st.switch_page("app.py")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📁 ملفات الطلاب", "👥 الموظفون", "✍️ التوقيعات", "📜 سجل النشاط"])

# ============ 1. ملفات الطلاب ============
with tab1:
    st.markdown("### 📁 ملفات الطلاب (Google Sheets)")
    st.info("""
    **لإضافة ملفات جديدة:**
    1. افتح Google Colab → شغّل Notebook التحويل.
    2. ارجع هنا واضغط **🔄 تحديث القائمة**.
    """)
    
    if st.button("🔄 تحديث القائمة", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    files = list_converted_sheets()
    st.metric("📗 إجمالي الملفات", len(files))
    
    st.markdown("### 📋 القائمة")
    if not files:
        st.warning("لا توجد ملفات.")
    else:
        for f in files:
            with st.container():
                c1, c2 = st.columns([5, 1])
                with c1:
                    modified = f.get('modifiedTime', '')[:10]
                    st.write(f"📄 **{f['name']}** — {modified}")
                with c2:
                    if st.button("🗑️ حذف", key=f"del_{f['id']}"):
                        st.session_state[f"confirm_del_{f['id']}"] = True
                
                if st.session_state.get(f"confirm_del_{f['id']}"):
                    st.warning(f"⚠️ حذف **{f['name']}** نهائياً؟")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("✅ نعم", key=f"yes_{f['id']}", use_container_width=True, type="primary"):
                        if delete_file(f['id']):
                            log_action("حذف ملف", target=f['name'])
                            st.session_state[f"confirm_del_{f['id']}"] = False
                            st.cache_data.clear()
                            st.rerun()
                    if cc2.button("❌ لا", key=f"no_{f['id']}", use_container_width=True):
                        st.session_state[f"confirm_del_{f['id']}"] = False
                        st.rerun()
                st.markdown("---")

# ============ 2. الموظفون ============
with tab2:
    with st.form("add_user_form"):
        st.markdown("### ➕ إضافة موظف")
        c1, c2 = st.columns(2)
        new_email = c1.text_input("البريد الإلكتروني")
        new_name = c2.text_input("الاسم")
        new_password = c1.text_input("كلمة المرور", type="password")
        new_role = c2.selectbox("الدور", ["موظف", "مدير"])
        
        if st.form_submit_button("➕ إضافة", use_container_width=True):
            if new_email and new_name and new_password:
                users_df = read_tab("users")
                if not users_df.empty and new_email in users_df["الإيميل"].astype(str).values:
                    st.error("⚠️ موجود بالفعل")
                else:
                    append_row("users", {
                        "الإيميل": new_email,
                        "كلمة المرور": hash_password(new_password),
                        "الاسم": new_name,
                        "الدور": new_role
                    })
                    log_action("إضافة موظف", target=new_email, details=new_role)
                    st.success(f"✅ تمت الإضافة")
                    st.rerun()
            else:
                st.error("⚠️ املأ الحقول")
    
    st.markdown("---")
    st.markdown("### 👥 القائمة")
    
    users_df = read_tab("users")
    if users_df.empty:
        st.info("لا يوجد مستخدمون")
    else:
        for idx, row in users_df.iterrows():
            real_row_num = idx + 2
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
                c1.write(f"📧 **{row['الإيميل']}**")
                c2.write(f"👤 {row['الاسم']}")
                c3.write(f"🏷️ {row['الدور']}")
                
                is_self = row['الإيميل'] == user['email']
                if is_self:
                    c4.write("🔒")
                    c5.write("(أنت)")
                else:
                    if c4.button("🔑", key=f"reset_{idx}", help="إعادة تعيين كلمة المرور"):
                        st.session_state[f"resetting_{idx}"] = True
                    if c5.button("🗑️", key=f"del_{idx}", help="حذف"):
                        st.session_state[f"confirm_del_user_{idx}"] = True
                    
                    if st.session_state.get(f"resetting_{idx}"):
                        new_pw = st.text_input("كلمة المرور الجديدة", type="password", key=f"new_pw_{idx}")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("✅ تعيين", key=f"ok_reset_{idx}", use_container_width=True, type="primary"):
                            r = admin_reset_password(row['الإيميل'], new_pw)
                            if "error" in r:
                                st.error(r["error"])
                            else:
                                log_action("إعادة تعيين كلمة مرور", target=row['الإيميل'])
                                st.success(r["message"])
                                st.session_state[f"resetting_{idx}"] = False
                                st.rerun()
                        if cc2.button("❌ إلغاء", key=f"cancel_reset_{idx}", use_container_width=True):
                            st.session_state[f"resetting_{idx}"] = False
                            st.rerun()
                    
                    if st.session_state.get(f"confirm_del_user_{idx}"):
                        st.warning(f"⚠️ حذف **{row['الاسم']}** نهائياً؟")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("✅ نعم", key=f"ok_del_{idx}", use_container_width=True, type="primary"):
                            delete_row("users", real_row_num)
                            log_action("حذف موظف", target=str(row['الإيميل']))
                            st.session_state[f"confirm_del_user_{idx}"] = False
                            st.rerun()
                        if cc2.button("❌ لا", key=f"cancel_del_{idx}", use_container_width=True):
                            st.session_state[f"confirm_del_user_{idx}"] = False
                            st.rerun()
                st.markdown("---")

# ============ 3. التوقيعات ============
with tab3:
    st.markdown("### ✍️ التوقيعات")
    sig_df = read_tab("signatures")
    if sig_df.empty:
        st.info("لا توجد توقيعات")
    else:
        search = st.text_input("🔍 بحث", key="sig_search")
        if search:
            mask = sig_df.astype(str).apply(
                lambda r: r.str.contains(search, case=False, na=False).any(), axis=1
            )
            filtered = sig_df[mask]
        else:
            filtered = sig_df
        st.markdown(f"**العدد: {len(filtered)}**")
        st.dataframe(filtered, use_container_width=True)
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
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
