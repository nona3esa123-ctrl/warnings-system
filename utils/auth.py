import streamlit as st
import bcrypt
from utils.sheets import read_tab, append_row


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
