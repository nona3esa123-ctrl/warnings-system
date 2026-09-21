import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


@st.cache_resource
def _get_creds():
    return Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES
    )


@st.cache_resource
def get_gspread_client():
    return gspread.authorize(_get_creds())


@st.cache_resource
def get_drive_service():
    return build('drive', 'v3', credentials=_get_creds())


@st.cache_resource
def get_system_spreadsheet():
    """فتح ملف 'بيانات_النظام' (يُفترض أنه موجود مسبقاً)"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    results = drive.files().list(
        q=f"name='بيانات_النظام' and '{folder_id}' in parents and trashed=false",
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    if not files:
        return None
    return get_gspread_client().open_by_key(files[0]['id'])


def _get_worksheet(tab_name):
    ss = get_system_spreadsheet()
    if ss is None:
        return None
    try:
        return ss.worksheet(tab_name)
    except Exception:
        return None


def read_tab(tab_name):
    """قراءة ورقة كاملة كـ DataFrame"""
    try:
        ws = _get_worksheet(tab_name)
        if ws is None:
            return pd.DataFrame()
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"خطأ في قراءة {tab_name}: {e}")
        return pd.DataFrame()


def append_row(tab_name, row_dict):
    """إضافة صف جديد"""
    try:
        ws = _get_worksheet(tab_name)
        if ws is None:
            return False
        headers = ws.row_values(1)
        ws.append_row([row_dict.get(h, "") for h in headers])
        return True
    except Exception as e:
        st.error(f"خطأ في الإضافة: {e}")
        return False


def update_row(tab_name, row_index, row_dict):
    """تحديث صف موجود (row_index يبدأ من 2)"""
    try:
        ws = _get_worksheet(tab_name)
        if ws is None:
            return False
        headers = ws.row_values(1)
        ws.update(f"A{row_index}", [[row_dict.get(h, "") for h in headers]])
        return True
    except Exception as e:
        st.error(f"خطأ في التحديث: {e}")
        return False


def delete_row(tab_name, row_index):
    """حذف صف"""
    try:
        ws = _get_worksheet(tab_name)
        if ws is None:
            return False
        ws.delete_rows(row_index)
        return True
    except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
        return False


def log_action(action_type, target="", details=""):
    """تسجيل عملية في سجل النشاط"""
    try:
        user = st.session_state.get("user")
        append_row("audit", {
            "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "الإيميل": user.get("email", "") if user else "",
            "الاسم": user.get("name", "") if user else "",
            "نوع العملية": action_type,
            "الهدف": target,
            "التفاصيل": details
        })
    except Exception:
        pass
