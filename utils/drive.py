import streamlit as st
import io
import time
import requests
import pandas as pd
from google.auth.transport.requests import Request
from utils.sheets import get_drive_service, get_creds


def list_student_files():
    """قائمة ملفات Excel في المجلد (مع إعادة المحاولة)"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"

    max_attempts = 3
    for attempt in range(max_attempts):
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
                if f['name'].lower().endswith(('.xlsx', '.xls')):
                    result.append(f)
            return result
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(2)
                continue
            st.error(f"خطأ في الوصول للمجلد: {e}")
            return []


def download_file_via_requests(file_id: str, max_attempts: int = 5) -> bytes:
    """تحميل ملف من Google Drive باستخدام requests مباشرة (بدون google-api-client)"""
    last_error = None
    for attempt in range(max_attempts):
        try:
            creds = get_creds()
            if not creds.valid:
                creds.refresh(Request())
            
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
            headers = {"Authorization": f"Bearer {creds.token}"}
            
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # تأخير تصاعدي: 1، 2، 4، 8 ثواني
                continue
            raise last_error
    raise last_error


def read_excel_from_drive(file_id: str) -> pd.DataFrame:
    """قراءة ملف Excel من Drive باستخدام requests"""
    file_bytes = download_file_via_requests(file_id, max_attempts=5)
    df = pd.read_excel(io.BytesIO(file_bytes), header=7)
    return df


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
