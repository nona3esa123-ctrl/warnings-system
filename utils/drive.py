import streamlit as st
from utils.sheets import get_gspread_client, get_drive_service


def list_converted_sheets():
    """قائمة كل ملفات Google Sheets في المجلد (باستثناء بيانات_النظام)"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    try:
        results = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.spreadsheet'",
            fields="files(id, name, modifiedTime)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        return [f for f in files if f['name'] != 'بيانات_النظام']
    except Exception as e:
        st.error(f"خطأ في جلب الملفات: {e}")
        return []


def read_sheet_by_id(file_id):
    """قراءة ملف Google Sheets كامل كـ DataFrame (بدون headers)"""
    try:
        client = get_gspread_client()
        sh = client.open_by_key(file_id)
        ws = sh.get_worksheet(0)
        all_values = ws.get_all_values()
        if len(all_values) < 9:
            return None
        return all_values
    except Exception:
        return None


def delete_file(file_id):
    try:
        get_drive_service().files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
        return False
