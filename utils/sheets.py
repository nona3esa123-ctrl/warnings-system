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
def get_creds():
    return Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES
    )


@st.cache_resource
def get_gspread_client():
    return gspread.authorize(get_creds())


@st.cache_resource
def get_drive_service():
    return build('drive', 'v3', credentials=get_creds())


def get_or_create_system_file():
    """الحصول على ملف 'بيانات_النظام' أو إنشاؤه تلقائياً"""
    folder_id = st.secrets["settings"]["folder_id"]
    client = get_gspread_client()
    drive = get_drive_service()
    
    # البحث عن الملف في المجلد
    try:
        results = drive.files().list(
            q=f"name='بيانات_النظام' and '{folder_id}' in parents and trashed=false",
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        if files:
            return client.open_by_key(files[0]['id'])
    except Exception as e:
        st.error(f"خطأ في البحث عن الملف: {e}")
        return None
    
    # إنشاء ملف جديد
    try:
        new_ss = client.create("بيانات_النظام")
        
        file = drive.files().get(fileId=new_ss.id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        drive.files().update(
            fileId=new_ss.id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents',
            supportsAllDrives=True
        ).execute()
        
        sheet1 = new_ss.sheet1
        sheet1.update_title("users")
        sheet1.append_row(["الإيميل", "كلمة المرور", "الاسم", "الدور"])
        
        ws_audit = new_ss.add_worksheet(title="audit", rows=1000, cols=10)
        ws_audit.append_row(["التاريخ", "الإيميل", "الاسم", "نوع العملية", "الهدف", "التفاصيل"])
        
        ws_sig = new_ss.add_worksheet(title="signatures", rows=1000, cols=10)
        ws_sig.append_row(["الرقم القومي", "التاريخ", "الموظف", "ملاحظات"])
        
        return new_ss
    except Exception as e:
        st.error(f"خطأ في إنشاء الملف: {e}")
        return None


def get_system_tab(tab_name):
    ss = get_or_create_system_file()
    if ss is None:
        return None
    try:
        return ss.worksheet(tab_name)
    except Exception:
        return None


def read_tab(tab_name):
    try:
        ws = get_system_tab(tab_name)
        if ws is None:
            return pd.DataFrame()
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"خطأ في قراءة {tab_name}: {e}")
        return pd.DataFrame()


def append_row(tab_name, row_dict):
    try:
        ws = get_system_tab(tab_name)
        if ws is None:
            return False
        headers = ws.row_values(1)
        row = [row_dict.get(h, "") for h in headers]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"خطأ في الإضافة: {e}")
        return False


def update_row(tab_name, row_index, row_dict):
    try:
        ws = get_system_tab(tab_name)
        if ws is None:
            return False
        headers = ws.row_values(1)
        row = [row_dict.get(h, "") for h in headers]
        ws.update(f"A{row_index}", [row])
        return True
    except Exception as e:
        st.error(f"خطأ في التحديث: {e}")
        return False


def delete_row(tab_name, row_index):
    try:
        ws = get_system_tab(tab_name)
        if ws is None:
            return False
        ws.delete_rows(row_index)
        return True
    except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
        return False


def log_action(action_type, target="", details=""):
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
