import streamlit as st
import io
import pandas as pd
from utils.sheets import get_drive_service
from googleapiclient.http import MediaIoBaseDownload


def list_student_files():
    """قائمة ملفات Excel في المجلد (باستثناء بيانات_النظام)"""
    folder_id = st.secrets["settings"]["folder_id"]
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"
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


def read_excel_from_drive(file_id: str) -> pd.DataFrame:
    """قراءة ملف Excel من Drive"""
    drive = get_drive_service()
    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
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
