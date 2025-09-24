# streamlit_app.py
# -*- coding: utf-8 -*-
import re
from datetime import datetime
import pytz

import streamlit as st
import pandas as pd

# ===== Google Sheets =====
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    CellFormat, Color, TextFormat,
    ConditionalFormatRule, BooleanRule, BooleanCondition,
    GridRange, format_cell_range, get_conditional_format_rules
)
# ===== קונפיגורציה כללית =====
st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו", layout="centered")

# ===== חיבור ל-Google Sheets דרך secrets =====
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

SHEET_ID = st.secrets["sheets"]["spreadsheet_id"]
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.sheet1

# ===== רשימת תחומי התמחות =====
SPECIALIZATIONS = [
    "מערכות מידע רפואיות", "בריאות דיגיטלית", "רווחה", "חינוך", "קהילה",
    "סיעוד", "פסיכולוגיה קהילתית", "מנהל מערכות מידע", "ניתוח נתונים", "סיוע טכנולוגי",
    "אחר"
]

# ===== סדר עמודות =====
COLUMNS_ORDER = [
    "תאריך",
    "שם פרטי",
    "שם משפחה",
    "סטטוס מדריך",
    "מוסד",
    "תחום התמחות",
    "רחוב",
    "עיר",
    "מיקוד",
    "מספר סטודנטים שניתן לקלוט (1 או 2)",
    "מעוניין להמשיך",
    "בקשות מיוחדות",
    "טלפון",
    "אימייל",
]
def style_google_sheet(ws):
    """Apply styling to the Google Sheet."""
    
    # --- עיצוב כותרות (שורה 1) ---
    header_fmt = CellFormat(
        backgroundColor=Color(0.4, 0.8, 0.6),   # ירוק בהיר
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),  # טקסט לבן מודגש
        horizontalAlignment='CENTER'
    )
    format_cell_range(ws, "1:1", header_fmt)

    # --- צבעי רקע מתחלפים (פסי זברה) ---
    rule = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('A2:Z1000', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('CUSTOM_FORMULA', ['=ISEVEN(ROW())']),
            format=CellFormat(backgroundColor=Color(0.95, 0.95, 0.95))  # אפור בהיר
        )
    )
    rules = get_conditional_format_rules(ws)
    rules.clear()
    rules.append(rule)
    rules.save()

    # --- עיצוב עמודת ת"ז (C) ---
    id_fmt = CellFormat(
        horizontalAlignment='CENTER',
        backgroundColor=Color(0.9, 0.9, 0.9)  # אפור עדין
    )
    format_cell_range(ws, "C2:C1000", id_fmt)

# ===== עיצוב CSS =====
st.markdown("""
<style>
:root{
  --ink:#0f172a; 
  --muted:#475569; 
  --ring:rgba(99,102,241,.25); 
  --card:rgba(255,255,255,.85);
}
html, body, [class*="css"] { font-family: system-ui, "Segoe UI", Arial; }
.stApp, .main, [data-testid="stSidebar"]{ direction:rtl; text-align:right; }
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(1200px 600px at 8% 8%, #e0f7fa 0%, transparent 65%),
    radial-gradient(1000px 500px at 92% 12%, #ede7f6 0%, transparent 60%),
    radial-gradient(900px 500px at 20% 90%, #fff3e0 0%, transparent 55%);
}
.block-container{ padding-top:1.1rem; }
[data-testid="stForm"]{
  background:var(--card);
  border:1px solid #e2e8f0;
  border-radius:16px;
  padding:18px 20px;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
}
[data-testid="stWidgetLabel"] p{ text-align:right; margin-bottom:.25rem; color:var(--muted); }
[data-testid="stWidgetLabel"] p::after{ content: " :"; }
input, textarea, select{ direction:rtl; text-align:right; }
</style>
""", unsafe_allow_html=True)

# ===== פונקציה לשמירה ב-Google Sheets =====
def save_to_google_sheets(record: dict):
    try:
        existing = worksheet.get_all_values()

        # אם אין כותרות או שהן לא תואמות – נכניס אותן מחדש
        if not existing or existing[0] != COLUMNS_ORDER:
            worksheet.clear()
            worksheet.append_row(COLUMNS_ORDER, value_input_option="USER_ENTERED")

        # מוסיפים את הרשומה בסוף
        row_values = [record.get(col, "") for col in COLUMNS_ORDER]
        worksheet.append_row(row_values, value_input_option="USER_ENTERED")

    except Exception as e:
        st.error(f"שגיאה בשמירה ל-Google Sheets: {e}")

# ===== טופס =====
st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")
st.write("""
שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות לקראת שיבוץ הסטודנטים לשנה הקרובה.  
אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.
""")

with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    first_name = st.text_input("שם פרטי *")
    last_name  = st.text_input("שם משפחה *")

    mentor_status = st.selectbox(
        "סטטוס מדריך *",
        ["מדריך חדש (נדרש קורס)", "מדריך ממשיך"],
        help=".מדריך חדש יישלח לקורס הכשרה מתאים"
    )

    st.subheader("מוסד")
    spec_choice = st.selectbox("תחום התמחות *", ["בחר מהרשימה"] + SPECIALIZATIONS)
    institute_select = st.text_input("מוסד *")

    st.subheader("כתובת המוסד")
    street = st.text_input("רחוב *")
    city = st.text_input("עיר *")
    postal_code = st.text_input("מיקוד *")

    st.subheader("קליטת סטודנטים")
    num_students = st.selectbox("מספר סטודנטים שניתן לקלוט (1 או 2) *", [1, 2])

    st.subheader("זמינות להמשך הדרכה")
    continue_mentoring = st.radio("מעוניין להמשיך *", ["כן", "לא"])

    st.subheader("בקשות מיוחדות")
    special_requests = st.text_area(
        "בקשות מיוחדות (למשל: הדרכה בערב, שפות, נגישות, אילוצים)",
        placeholder="כתבו כאן כל בקשה שתרצו שניקח בחשבון בשיבוץ",
        key="special_requests"
    )

    st.subheader("פרטי התקשרות")
    phone = st.text_input("טלפון *")
    email = st.text_input("אימייל *")

    submit_btn = st.form_submit_button("שלח/י", use_container_width=True)

# ===== טיפול בטופס =====
if submit_btn:
    errors = []
    if not first_name.strip():
        errors.append("יש למלא 'שם פרטי'")
    if not last_name.strip():
        errors.append("יש למלא 'שם משפחה'")
    if spec_choice == "בחר מהרשימה":
        errors.append("יש לבחור 'תחום התמחות'")
    if not institute_select.strip():
        errors.append("יש למלא 'מוסד'")
    if not street.strip():
        errors.append("יש למלא 'רחוב'")
    if not city.strip():
        errors.append("יש למלא 'עיר'")
    if not postal_code.strip():
        errors.append("יש למלא 'מיקוד'")

    phone_clean = phone.strip().replace("-", "").replace(" ", "")
    if not re.match(r"^(0?5\d{8})$", phone_clean):
        errors.append("מספר הטלפון אינו תקין (דוגמה: 0501234567)")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email.strip()):
        errors.append("כתובת האימייל אינה תקינה")

    if errors:
        for e in errors:
            st.error(e)
    else:
        # שעון ישראל
        tz_il = pytz.timezone("Asia/Jerusalem")

        record = {
            "תאריך": datetime.now(tz_il).strftime("%Y-%m-%d %H:%M:%S"),
            "שם פרטי": first_name.strip(),
            "שם משפחה": last_name.strip(),
            "סטטוס מדריך": mentor_status,
            "מוסד": institute_select.strip(),
            "תחום התמחות": spec_choice,
            "רחוב": street.strip(),
            "עיר": city.strip(),
            "מיקוד": postal_code.strip(),
            "מספר סטודנטים שניתן לקלוט (1 או 2)": int(num_students),
            "מעוניין להמשיך": continue_mentoring,
            "בקשות מיוחדות": special_requests.strip(),
            "טלפון": phone_clean,
            "אימייל": email.strip()
        }

        save_to_google_sheets(record)

        st.success("✅ הנתונים נשמרו בהצלחה !")
