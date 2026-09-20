import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import read_tab, append_row, log_action
from utils.drive import list_student_files, read_excel_from_drive


# خريطة أعمدة ملف الطلاب (مبنية على ترتيب الأعمدة في الملف)
COL_MAP = {
    "عدد الانذارات المنفصله": 2,
    "ساعات الاجتياز": 4,
    "تراكمى الفصل": 5,
    "تراكمى الطالب": 6,
    "اللائحه": 7,
    "القسم/ الشعبة": 11,
    "المستوى": 14,
    "الرقم القومى": 15,
    "كود الطالب": 16,
    "اسم الطالب": 17,
}


@st.cache_data(ttl=300, show_spinner=False)
def load_all_students():
    """تحميل جميع الطلاب من كل ملفات Excel في المجلد"""
    files = list_student_files()
    rows = []
    for f in files:
        try:
            df = read_excel_from_drive(f['id'])
            for _, row in df.iterrows():
                student = {}
                for name, idx in COL_MAP.items():
                    try:
                        val = row.iloc[idx] if idx < len(row) else ""
                        # تنظيف NaN
                        if pd.isna(val):
                            val = ""
                        student[name] = val
                    except Exception:
                        student[name] = ""
                if str(student.get("الرقم القومى", "")).strip() not in ("", "nan"):
                    student["_file_name"] = f['name']
                    student["_file_id"] = f['id']
                    rows.append(student)
        except Exception:
            continue
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def find_student(national_id: str):
    if not national_id:
        return None
    df = load_all_students()
    if df.empty:
        return None
    df["الرقم القومى"] = df["الرقم القومى"].astype(str).str.strip()
    match = df[df["الرقم القومى"] == str(national_id).strip()]
    if match.empty:
        return None
    return match.iloc[0]


def get_signature(national_id: str):
    sig_df = read_tab("signatures")
    if sig_df.empty:
        return None
    sig_df["الرقم القومي"] = sig_df["الرقم القومي"].astype(str).str.strip()
    match = sig_df[sig_df["الرقم القومي"] == str(national_id).strip()]
    if match.empty:
        return None
    return match.iloc[0]


def sign_warning(national_id: str):
    student = find_student(national_id)
    if student is None:
        return {"error": "⚠️ لم يتم العثور على طالب بهذا الرقم القومي"}
    
    existing = get_signature(national_id)
    if existing is not None:
        return {"error": f"⚠️ الطالب وقّع مسبقاً بتاريخ: {existing['التاريخ']}"}
    
    user = st.session_state.get("user")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_row("signatures", {
        "الرقم القومي": national_id,
        "التاريخ": now,
        "الموظف": user.get("name", "") if user else "",
        "ملاحظات": ""
    })
    log_action("تسجيل توقيع", target=str(student.get("اسم الطالب", "")), details=f"الرقم: {national_id}")
    return {"success": True, "message": f"✅ تم تسجيل التوقيع بتاريخ {now}", "timestamp": now}


def generate_warning_statement(student, signature=None) -> str:
    """توليد بيان إنذار رسمي قابل للطباعة"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # عدد الإنذارات
    try:
        warnings_count = int(float(str(student.get("عدد الانذارات المنفصله", 0))))
    except (ValueError, TypeError):
        warnings_count = 0
    
    # حالة التوقيع
    if signature is not None:
        sign_status = f"✅ تم العلم بالإنذار بتاريخ: {signature['التاريخ']}"
        sign_status_plain = f"تم العلم بالإنذار بتاريخ: {signature['التاريخ']}"
    else:
        sign_status = "⏳ لم يتم التوقيع على علم الإنذار بعد"
        sign_status_plain = "لم يتم التوقيع على علم الإنذار بعد"
    
    statement = f"""
================================================================
                     كلية علوم الرياضة - بنين
================================================================
                     بيان إنذار أكاديمي
================================================================

  📅 التاريخ: {now}

  ─────────────────── بيانات الطالب ───────────────────

  الاسم:                  {student.get('اسم الطالب', '')}
  كود الطالب:             {student.get('كود الطالب', '')}
  الرقم القومي:           {student.get('الرقم القومى', '')}
  المستوى:                {student.get('المستوى', '')}
  القسم / الشعبة:          {student.get('القسم/ الشعبة', '')}
  اللائحة:                {student.get('اللائحه', '')}

  ─────────────────── البيانات الأكاديمية ───────────────────

  ⚠️ عدد الإنذارات:        {warnings_count}
  📚 ساعات الاجتياز:        {student.get('ساعات الاجتياز', '')}
  📊 تراكمى الفصل:          {student.get('تراكمى الفصل', '')}
  📈 تراكمى الطالب:         {student.get('تراكمى الطالب', '')}

  ─────────────────── حالة العلم بالإنذار ───────────────────

  {sign_status_plain}

================================================================
                       تعليمات هامة
================================================================

  📢 برجاء التوجه إلى الإرشاد الأكاديمي لفك الحظر،
     مع ضرورة إحضار:
        • نسخة من إثبات الشخصية (بطاقة الرقم القومي / جواز السفر)
        • هذا البيان مطبوعاً وموقعاً منك

  📌 هذا البيان صادر إلكترونياً من نظام متابعة الإنذارات
     كلية علوم الرياضة - بنين

================================================================
              جميع الحقوق محفوظة © كلية علوم الرياضة بنين
================================================================
"""
    return statement
