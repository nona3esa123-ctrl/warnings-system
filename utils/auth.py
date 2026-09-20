import streamlit as st
import bcrypt
from utils.sheets import read_tab, append_row, update_row


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return password == hashed


def authenticate(email: str, password: str):
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
    """إنشاء مدير افتراضي إذا كانت الأوراق فارغة"""
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


def change_own_password(email: str, old_password: str, new_password: str):
    """تغيير كلمة مرور المستخدم بنفسه"""
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
        return {"error": "⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل"}
    
    real_row_num = match.index[0] + 2  # +2 لأن الصف 1 هو الهيدر
    updated_data = row.to_dict()
    updated_data["كلمة المرور"] = hash_password(new_password)
    update_row("users", real_row_num, updated_data)
    return {"success": True, "message": "✅ تم تغيير كلمة المرور بنجاح"}


def admin_reset_password(target_email: str, new_password: str):
    """إعادة تعيين كلمة مرور مستخدم (للمدير فقط)"""
    users_df = read_tab("users")
    if users_df.empty:
        return {"error": "لا يوجد مستخدمون"}
    
    match = users_df[users_df["الإيميل"].astype(str) == target_email]
    if match.empty:
        return {"error": "المستخدم غير موجود"}
    
    if len(new_password) < 6:
        return {"error": "⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل"}
    
    real_row_num = match.index[0] + 2
    updated_data = match.iloc[0].to_dict()
    updated_data["كلمة المرور"] = hash_password(new_password)
    update_row("users", real_row_num, updated_data)
    return {"success": True, "message": f"✅ تم إعادة تعيين كلمة المرور لـ {target_email}"}
