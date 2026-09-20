import streamlit as st
import io
import time
import requests
import pandas as pd
from google.auth.transport.requests import Request
from utils.sheets import get_drive_service, get_creds, get_gspread_client
from utils.oauth import load_credentials


def list_student_files():
    """قائمة ملفات Excel الأصلية (بـ Service Account)"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"
    for attempt in range(3):
        try:
            results = drive.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])
            result = []
            for f in files:
                if f['name'] == 'بيانات_النظام':
                    continue
                if f['name'].startswith('GS_'):
                    continue
                if f['name'].lower().endswith(('.xlsx', '.xls')):
                    result.append(f)
            return result
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            return []


def list_converted_sheets():
    """قائمة ملفات Google Sheets المحوّلة"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.spreadsheet'"
    try:
        results = drive.files().list(
            q=query,
            fields="files(id, name, modifiedTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = results.get('files', [])
        return [f for f in files if f['name'].startswith('GS_')]
    except Exception:
        return []


def read_excel_from_drive(file_id: str) -> pd.DataFrame:
    """قراءة ملف Excel بـ requests (بدون google-api-client)"""
    last_error = None
    for attempt in range(3):
        try:
            creds = get_creds()
            if not creds.valid:
                creds.refresh(Request())
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
            headers = {"Authorization": f"Bearer {creds.token}"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return pd.read_excel(io.BytesIO(response.content), header=7)
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(2)
                continue
            raise last_error
    raise last_error


def read_sheet_by_id(file_id: str) -> pd.DataFrame:
    """قراءة Google Sheets بواسطة ID (سريع)"""
    client = get_gspread_client()
    sh = client.open_by_key(file_id)
    ws = sh.sheet1
    all_values = ws.get_all_values()
    if len(all_values) < 8:
        return pd.DataFrame()
    headers = all_values[7]
    data = all_values[8:]
    return pd.DataFrame(data, columns=headers)


def convert_excel_to_sheets(excel_file_id: str, excel_name: str) -> dict:
    """تحويل Excel → Google Sheets باستخدام OAuth (يستخدم مساحة المدير)"""
    creds = load_credentials()
    if not creds:
        return {"error": "🔐 يجب تسجيل الدخول بحساب Google أولاً (من لوحة المدير)"}
    
    from googleapiclient.discovery import build
    drive = build('drive', 'v3', credentials=creds)
    folder_id = st.secrets["settings"]["folder_id"]
    
    base_name = excel_name
    for ext in ['.xlsx', '.xls', '.XLSX', '.XLS']:
        base_name = base_name.replace(ext, '')
    new_name = f"GS_{base_name}"
    
    # تحقق إن كانت موجودة
    existing = list_converted_sheets()
    for f in existing:
        if f['name'] == new_name:
            return {"error": f"⚠️ موجودة مسبقاً: {new_name}", "id": f['id']}
    
    try:
        body = {
            'name': new_name,
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        new_file = drive.files().copy(
            fileId=excel_file_id,
            body=body,
            supportsAllDrives=True
        ).execute()
        return {"success": True, "id": new_file.get('id'), "name": new_name}
    except Exception as e:
        return {"error": f"❌ فشل التحويل: {e}"}


def delete_file(file_id: str) -> bool:
    try:
        get_drive_service().files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
        return False


def rename_file(file_id: str, new_name: str) -> bool:
    try:
        get_drive_service().files().update(
            fileId=file_id,
            body={'name': new_name},
            supportsAllDrives=True
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في التسمية: {e}")
        return False
