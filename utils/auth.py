import streamlit as st
import bcrypt
from utils.sheets import read_tab, update_row, append_row


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return password == hashed


def authenticate(email, password):
    users_df = read_tab("users")
    if users_df.empty:
        return None
    user = users_df[users_df["الإيميل"].astype(str) == email]
    if user.empty:
        return None
    row = user.iloc[0]
    if verify_password(password, str(row["كلمة المرور"])):
        return {
            "email": email,
            "name": row["الاسم"],
            "role": row["الدور"]
        }
    return None


def init_session():
    if "user" not in st.session_state:
        st.session_state["user"] = None


def create_default_admin():
    try:
        users_df = read_tab("users")
        if users_df.empty:
            append_row("users", {
                "الإيميل": "admin@warnings.com",
                "كلمة المرور": hash_password("admin123"),
                "الاسم": "مدير النظام",
                "الدور": "مدير"
            })
    except Exception:
        pass


def change_own_password(email, old_password, new_password):
    users_df = read_tab("users")
    if users_df.empty:
        return {"error": "لا يوجد مستخدمون"}
    match = users_df[users_df["الإيميل"].astype(str) == email]
    if match.empty:
        return {"error": "المستخدم غير موجود"}
    row = match.iloc[0]
    if not verify_password(old_password, str(row["كلمة المرور"])):
        return {"error": "❌ كلمة المرور الحالية غير صحيحة"}
    if len(new_password) < 6:
        return {"error": "⚠️ كلمة المرور 6 أحرف على الأقل"}
    real_row_num = match.index[0] + 2
    updated = row.to_dict()
    updated["كلمة المرور"] = hash_password(new_password)
    update_row("users", real_row_num, updated)
    return {"success": True, "message": "✅ تم تغيير كلمة المرور"}


def admin_reset_password(target_email, new_password):
    users_df = read_tab("users")
    if users_df.empty:
        return {"error": "لا يوجد مستخدمون"}
    match = users_df[users_df["الإيميل"].astype(str) == target_email]
    if match.empty:
        return {"error": "المستخدم غير موجود"}
    if len(new_password) < 6:
        return {"error": "⚠️ كلمة المرور 6 أحرف على الأقل"}
    real_row_num = match.index[0] + 2
    updated = match.iloc[0].to_dict()
    updated["كلمة المرور"] = hash_password(new_password)
    update_row("users", real_row_num, updated)
    return {"success": True, "message": f"✅ تم التعيين لـ {target_email}"}
