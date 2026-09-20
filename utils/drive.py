import streamlit as st
import io
import time
import pandas as pd
from utils.sheets import get_drive_service
from googleapiclient.http import MediaIoBaseDownload


def list_student_files():
    """قائمة ملفات Excel في المجلد (مع إعادة المحاولة عند فشل SSL)"""
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
            st.error(f"خطأ في الوصول للمجلد بعد {max_attempts} محاولات: {e}")
            return []


def download_file_with_retry(file_id: str, max_attempts: int = 3) -> io.BytesIO:
    """تحميل ملف من Drive مع إعادة المحاولة عند فشل SSL"""
    drive = get_drive_service()
    
    last_error = None
    for attempt in range(max_attempts):
        try:
            request = drive.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            raise last_error


def read_excel_from_drive(file_id: str) -> pd.DataFrame:
    """قراءة ملف Excel من Drive"""
    fh = download_file_with_retry(file_id, max_attempts=3)
    df = pd.read_excel(fh, header=7)
    return df


def delete_file(file_id: str) -> bool:
    """حذف ملف من Drive"""
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
    """إعادة تسمية ملف"""
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
