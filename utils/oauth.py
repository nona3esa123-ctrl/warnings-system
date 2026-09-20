import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_oauth_flow():
    """إنشاء كائن Flow لإدارة عملية OAuth"""
    client_config = {
        "web": {
            "client_id": st.secrets["oauth"]["client_id"],
            "client_secret": st.secrets["oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["oauth"]["redirect_uri"]]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["oauth"]["redirect_uri"]
    )


def get_authorization_url() -> str:
    """الحصول على رابط تسجيل الدخول من Google"""
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    return auth_url


def exchange_code_for_credentials(code: str):
    """تبادل الكود للحصول على credentials"""
    flow = get_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def save_credentials(creds: Credentials):
    """حفظ credentials في الجلسة"""
    st.session_state["google_credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }


def load_credentials():
    """استرجاع credentials من الجلسة"""
    if "google_credentials" not in st.session_state:
        return None
    data = st.session_state["google_credentials"]
    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes")
    )
    # تجديد تلقائي إذا انتهت صلاحية التوكن
    if not creds.valid and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
        except Exception:
            return None
    return creds


def is_logged_in() -> bool:
    """هل المدير مسجل دخول؟"""
    return load_credentials() is not None


def logout():
    """تسجيل الخروج من حساب Google"""
    if "google_credentials" in st.session_state:
        del st.session_state["google_credentials"]
