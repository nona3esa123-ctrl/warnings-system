import streamlit as st
import pandas as pd
import html
from datetime import datetime
from utils.sheets import read_tab, append_row, log_action
from utils.drive import list_converted_sheets, read_sheet_by_id


# خريطة أعمدة ملف الطالب (بالفهارس)
COL = {
    "عدد الإنذارات": 2,
    "ساعات الاجتياز": 4,
    "تراكمى الفصل": 5,
    "تراكمى الطالب": 6,
    "اللائحة": 7,
    "القسم/ الشعبة": 11,
    "المستوى": 14,
    "الرقم القومي": 15,
    "كود الطالب": 16,
    "اسم الطالب": 17,
}


def _safe(value):
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() == "nan":
        return ""
    return s


def _extract_row(raw_row, file_name):
    """استخراج بيانات طالب من صف خام"""
    student = {}
    for key, idx in COL.items():
        try:
            student[key] = _safe(raw_row[idx]) if idx < len(raw_row) else ""
        except Exception:
            student[key] = ""
    student["_file"] = file_name
    return student


@st.cache_data(ttl=600, show_spinner=False)
def load_all_students():
    """تحميل جميع الطلاب من ملفات Google Sheets"""
    files = list_converted_sheets()
    all_rows = []
    for f in files:
        raw_values = read_sheet_by_id(f['id'])
        if not raw_values:
            continue
        for raw_row in raw_values[8:]:  # الصف 9 فما فوق
            if not raw_row:
                continue
            try:
                nid = _safe(raw_row[15]) if len(raw_row) > 15 else ""
            except Exception:
                nid = ""
            if not nid:
                continue
            student = _extract_row(raw_row, f['name'])
            if student["الرقم القومي"]:
                all_rows.append(student)
    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()


def find_all_student_rows(national_id):
    """البحث عن جميع صفوف الطالب (قد تكون 9-10 صفوف عبر ملفات مختلفة)"""
    if not national_id:
        return pd.DataFrame()
    df = load_all_students()
    if df.empty:
        return pd.DataFrame()
    match = df[df["الرقم القومي"].astype(str).str.strip() == str(national_id).strip()]
    return match


def get_signature(national_id):
    sig_df = read_tab("signatures")
    if sig_df.empty:
        return None
    sig_df["الرقم القومي"] = sig_df["الرقم القومي"].astype(str).str.strip()
    match = sig_df[sig_df["الرقم القومي"] == str(national_id).strip()]
    if match.empty:
        return None
    return match.iloc[0]


def sign_warning(national_id):
    student = find_all_student_rows(national_id)
    if student.empty:
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
    student_name = student.iloc[0]["اسم الطالب"]
    log_action("تسجيل توقيع", target=student_name, details=f"الرقم: {national_id}")
    return {"success": True, "message": f"✅ تم تسجيل التوقيع بتاريخ {now}", "timestamp": now}


def generate_student_html(rows_df, signature=None):
    """توليد HTML كامل لبيان الطالب (جاهز للطباعة كـ PDF)"""
    if rows_df.empty:
        return ""

    first = rows_df.iloc[0]
    student_name = html.escape(str(first.get("اسم الطالب", "")))
    student_code = html.escape(str(first.get("كود الطالب", "")))
    national_id = html.escape(str(first.get("الرقم القومي", "")))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    total_warnings = 0
    for _, r in rows_df.iterrows():
        try:
            total_warnings += int(float(r.get("عدد الإنذارات", 0) or 0))
        except (ValueError, TypeError):
            pass
    has_warnings = total_warnings > 0

    if signature is not None:
        sign_html = f"""
        <div class="info-box" style="background:#d1fae5; color:#065f46;">
            <b>حالة العلم بالإنذار:</b> ✅ تم بتاريخ {html.escape(str(signature['التاريخ']))}
            <br><b>الموظف:</b> {html.escape(str(signature.get('الموظف', '')))}
        </div>
        """
    else:
        sign_html = '<div class="info-box" style="background:#fef3c7; color:#92400e;"><b>حالة العلم بالإنذار:</b> ⏳ لم يتم التوقيع بعد</div>'

    table_rows = ""
    for _, r in rows_df.iterrows():
        table_rows += f"""
        <tr>
            <td>{html.escape(str(r.get('المستوى', '')))}</td>
            <td>{html.escape(str(r.get('القسم/ الشعبة', '')))}</td>
            <td>{html.escape(str(r.get('ساعات الاجتياز', '')))}</td>
            <td>{html.escape(str(r.get('تراكمى الفصل', '')))}</td>
            <td>{html.escape(str(r.get('تراكمى الطالب', '')))}</td>
            <td style="background:#fee2e2; font-weight:bold;">{html.escape(str(r.get('عدد الإنذارات', '')))}</td>
            <td>{html.escape(str(r.get('_file', '')))}</td>
        </tr>
        """

    alert_html = ""
    if has_warnings:
        alert_html = """
        <div class="alert">
            📢 تنبيه هام<br>
            برجاء التوجه للإرشاد الأكاديمي لفك الحظر،<br>
            مع ضرورة إحضار نسخة من إثبات الشخصية وبيان الإنذار مطبوعاً.
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>بيان إنذار - {student_name}</title>
<style>
    * {{ font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif; box-sizing: border-box; }}
    body {{ padding: 20px; max-width: 1100px; margin: auto; color: #1a3a5c; background: white; }}
    h1 {{ text-align: center; color: #2b7a62; border-bottom: 3px double #2b7a62; padding-bottom: 10px; margin-bottom: 5px; font-size: 22px; }}
    h2 {{ text-align: center; color: #1a3a5c; margin-top: 5px; font-size: 18px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }}
    th {{ background: #2b7a62; color: white; padding: 10px 8px; border: 1px solid #1a3a5c; }}
    td {{ padding: 8px; border: 1px solid #cbd5e1; text-align: center; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    .info-box {{ background: #f0f4f8; padding: 15px; border-radius: 10px; margin: 15px 0; line-height: 1.8; }}
    .alert {{ background: #fff5f5; border: 2px solid #e53e3e; border-radius: 10px; padding: 20px; text-align: center; color: #9b2c2c; margin-top: 20px; font-weight: bold; font-size: 16px; line-height: 1.8; }}
    .footer {{ text-align: center; color: #64748b; margin-top: 30px; padding-top: 15px; border-top: 1px solid #cbd5e1; font-size: 12px; }}
    .print-btn {{ display: block; margin: 20px auto; padding: 14px 40px; background: #2b7a62; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }}
    .print-btn:hover {{ background: #1e5c4a; }}
    @media print {{
        body {{ padding: 0; }}
        .no-print {{ display: none !important; }}
    }}
</style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">🖨️ طباعة / حفظ كـ PDF</button>

    <h1>كلية علوم الرياضة - بنين</h1>
    <h2>بيان إنذارات أكاديمية</h2>

    <div class="info-box">
        <b>الاسم:</b> {student_name} &nbsp;|&nbsp; <b>كود الطالب:</b> {student_code} &nbsp;|&nbsp; <b>الرقم القومي:</b> {national_id}
        <br><b>تاريخ الطباعة:</b> {now}
        <br><b>عدد الصفوف:</b> {len(rows_df)}
    </div>

    <table>
        <thead>
            <tr>
                <th>المستوى</th>
                <th>القسم/ الشعبة</th>
                <th>ساعات الاجتياز</th>
                <th>تراكمى الفصل</th>
                <th>تراكمى الطالب</th>
                <th>عدد الإنذارات</th>
                <th>المصدر</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    {sign_html}
    {alert_html}

    <div class="footer">
        جميع الحقوق محفوظة © كلية علوم الرياضة بنين<br>
        هذا البيان صادر إلكترونياً من نظام متابعة الإنذارات
    </div>

    <button class="print-btn no-print" onclick="window.print()">🖨️ طباعة / حفظ كـ PDF</button>
</body>
</html>"""
