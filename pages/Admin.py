import streamlit as st
import pandas as pd
from utils.auth import init_session, hash_password, admin_reset_password
from utils.sheets import read_tab, append_row, update_row, delete_row, log_action
from utils.drive import (
    list_student_files, list_converted_sheets,
    convert_excel_to_sheets, delete_file, delete_converted_sheet, rename_file
)

st.set_page_config(page_title="لوحة المدير", page_icon="👑", layout="wide")
init_session()

user = st.session_state.get("user")
if not user or user["role"] != "مدير":
    st.error("🔐 هذه الصفحة للمدير فقط. سجّل الدخول من الصفحة الرئيسية.")
    st.stop()

st.title("👑 لوحة المدير")

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
    
    st.info("""
    ### 📤 لرفع ملف جديد:
    1. افتح **Google Drive** → مجلد **الإنذارات_الجديد**.
    2. اسحب ملف `.xlsx` وأفلته.
    3. اضغط **🔄 تحديث القائمة**.
    
    ### ⚡ لتسريع البحث:
    اضغط **"تحويل"** بجانب أي ملف Excel → سيتم إنشاء نسخة Google Sheets.
    **الملف الأصلي يبقى محفوظاً** — النظام يقرأ من النسخة السريعة.
    """)
    
    if st.button("🔄 تحديث القائمة", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # زر التحويل الشامل
    excel_files = list_student_files()
    converted = list_converted_sheets()
    converted_names = {f['name'] for f in converted}
    
    # تحقق من الملفات غير المحوّلة
    not_converted = []
    for ex in excel_files:
        base = ex['name']
        for ext in ['.xlsx', '.xls', '.XLSX', '.XLS']:
            base = base.replace(ext, '')
        if f"GS_{base}" not in converted_names:
            not_converted.append(ex)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if not_converted:
            if st.button(f"⚡ تحويل كل الملفات ({len(not_converted)})", use_container_width=True, type="primary"):
                progress = st.progress(0)
                success_count = 0
                for i, ex in enumerate(not_converted):
                    result = convert_excel_to_sheets(ex['id'], ex['name'])
                    if "success" in result:
                        success_count += 1
                        log_action("تحويل Excel → Sheets", target=ex['name'], details=result['name'])
                    progress.progress((i + 1) / len(not_converted))
                st.cache_data.clear()
                st.success(f"✅ تم تحويل {success_count} من {len(not_converted)} ملف")
                st.rerun()
        else:
            st.success("✅ كل الملفات محوّلة إلى Google Sheets")
    with col_b:
        st.metric("📄 ملفات Excel", len(excel_files))
        st.metric("📗 Google Sheets", len(converted))
    
    st.markdown("---")
    st.markdown("### 📋 الملفات الحالية")
    
    if not excel_files:
        st.warning("لا توجد ملفات Excel في المجلد.")
    else:
        for ex in excel_files:
            base = ex['name']
            for ext in ['.xlsx', '.xls', '.XLSX', '.XLS']:
                base = base.replace(ext, '')
            gs_name = f"GS_{base}"
            gs_file = next((f for f in converted if f['name'] == gs_name), None)
            
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                
                with c1:
                    size = int(ex.get('size', 0)) / 1024
                    st.write(f"📄 **{ex['name']}** — {size:.0f} KB")
                
                with c2:
                    if gs_file:
                        st.success(f"✅ محوّل → Sheets")
                    else:
                        st.warning("⚠️ غير محوّل")
                
                with c3:
                    if not gs_file:
                        if st.button("⚡ تحويل", key=f"conv_{ex['id']}", use_container_width=True):
                            with st.spinner("جاري التحويل..."):
                                result = convert_excel_to_sheets(ex['id'], ex['name'])
                                if "success" in result:
                                    log_action("تحويل Excel → Sheets", target=ex['name'])
                                    st.cache_data.clear()
                                    st.success(f"✅ تم")
                                    st.rerun()
                                else:
                                    st.error(result.get("error", "فشل"))
                    else:
                        if st.button("🗑️ حذف النسخة", key=f"del_gs_{ex['id']}", use_container_width=True, help="حذف نسخة Sheets فقط (يبقى Excel)"):
                            if delete_converted_sheet(gs_file['id']):
                                log_action("حذف نسخة Sheets", target=gs_name)
                                st.cache_data.clear()
                                st.success("✅")
                                st.rerun()
                
                with c4:
                    if st.button("🗑️ حذف الكل", key=f"del_all_{ex['id']}", use_container_width=True, help="حذف Excel + نسخة Sheets"):
                        st.session_state[f"confirm_del_all_{ex['id']}"] = True
                
                # تأكيد حذف الكل
                if st.session_state.get(f"confirm_del_all_{ex['id']}"):
                    st.error(f"⚠️ سيتم حذف **{ex['name']}** و**{gs_name if gs_file else ''}** نهائياً!")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("✅ نعم احذف الكل", key=f"yes_all_{ex['id']}", use_container_width=True, type="primary"):
                        try:
                            if gs_file:
                                delete_converted_sheet(gs_file['id'])
                            delete_file(ex['id'])
                            log_action("حذف ملف كامل", target=ex['name'])
                            st.session_state[f"confirm_del_all_{ex['id']}"] = False
                            st.cache_data.clear()
                            st.success("✅ تم الحذف")
                            st.rerun()
                        except Exception as e:
                            st.error(f"خطأ: {e}")
                    if cc2.button("❌ إلغاء", key=f"no_all_{ex['id']}", use_container_width=True):
                        st.session_state[f"confirm_del_all_{ex['id']}"] = False
                        st.rerun()
                
                st.markdown("---")

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
                    st.error("⚠️ البريد موجود بالفعل")
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
                    if c4.button("🔑", key=f"reset_pw_{idx}", help="إعادة تعيين كلمة المرور"):
                        st.session_state[f"resetting_pw_{idx}"] = True
                    if c5.button("🗑️", key=f"del_user_{idx}", help="حذف الموظف"):
                        st.session_state[f"confirm_del_user_{idx}"] = True
                    
                    if st.session_state.get(f"resetting_pw_{idx}"):
                        st.markdown(f"**🔑 إعادة تعيين كلمة المرور لـ {row['الاسم']}**")
                        new_pw = st.text_input("كلمة المرور الجديدة", type="password", key=f"new_pw_{idx}")
                        cc1, cc2 = st.columns(2)
                        if cc1.button("✅ تعيين", key=f"confirm_reset_{idx}", use_container_width=True, type="primary"):
                            if not new_pw or len(new_pw) < 6:
                                st.error("⚠️ كلمة المرور 6 أحرف على الأقل")
                            else:
                                result = admin_reset_password(row['الإيميل'], new_pw)
                                if "error" in result:
                                    st.error(result["error"])
                                else:
                                    log_action("إعادة تعيين كلمة مرور", target=row['الإيميل'])
                                    st.success(result["message"])
                                    st.session_state[f"resetting_pw_{idx}"] = False
                                    st.rerun()
                        if cc2.button("❌ إلغاء", key=f"cancel_reset_{idx}", use_container_width=True):
                            st.session_state[f"resetting_pw_{idx}"] = False
                            st.rerun()
                    
                    if st.session_state.get(f"confirm_del_user_{idx}"):
                        st.warning(f"⚠️ سيتم حذف **{row['الاسم']}** نهائياً.")
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
    sig_df = read_tab("signatures")
    if sig_df.empty:
        st.info("لا توجد توقيعات مسجلة بعد")
    else:
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
