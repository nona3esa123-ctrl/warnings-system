import streamlit as st
import io
import pandas as pd
from utils.sheets import get_drive_service


def list_student_files():
    """قائمة ملفات Excel في المجلد (باستثناء بيانات_النظام)"""
    folder_id = st.secrets["folder_id"]
    drive = get_drive_service()
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive.files().list(
        q=query,
        fields="files(id, name, mimeType, size, modifiedTime)"
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
    from googleapiclient.http import MediaIoBaseDownload
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    df = pd.read_excel(fh, header=7)
    return df


def upload_file_to_folder(file_bytes: bytes, filename: str) -> str:
    """رفع ملف Excel إلى المجلد"""
    from googleapiclient.http import MediaIoBaseUpload
    folder_id = st.secrets["folder_id"]
    drive = get_drive_service()
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    file = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    return file.get('id')


def delete_file(file_id: str) -> bool:
    try:
        get_drive_service().files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في الحذف: {e}")
        return False


def rename_file(file_id: str, new_name: str) -> bool:
    try:
        get_drive_service().files().update(
            fileId=file_id,
            body={'name': new_name}
        ).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في التسمية: {e}")
        return False
