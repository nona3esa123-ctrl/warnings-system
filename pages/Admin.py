# ============ 1. ملفات الطلاب ============
with tab1:
    st.markdown("### 📁 إدارة ملفات الطلاب")
    
    # تعليمات الرفع
    st.info("""
    ### 📤 لرفع ملف طلاب جديد:
    1. افتح **Google Drive** → مجلد **الإنذارات_الجديد**.
    2. اسحب ملف `.xlsx` وأفلته داخل المجلد (أو استخدم زر "New").
    3. ارجع إلى هنا واضغط **🔄 تحديث القائمة** بالأسفل.
    
    ⚠️ **تنبيه**: لا يمكن الرفع من داخل التطبيق لأن حساب النظام (Service Account) لا يملك مساحة تخزين. الرفع يجب أن يتم يدوياً عبر Drive.
    """)
    
    if st.button("🔄 تحديث القائمة", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📋 الملفات الحالية")
    
    files = list_student_files()
    if not files:
        st.warning("لا توجد ملفات طلاب في المجلد بعد. ارفع ملفاتك عبر Google Drive.")
    else:
        for f in files:
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                size = int(f.get('size', 0)) / 1024
                modified = f.get('modifiedTime', '')[:10]
                st.write(f"📄 **{f['name']}** — {size:.0f} KB — آخر تعديل: {modified}")
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
