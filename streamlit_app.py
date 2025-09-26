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
from gspread_formatting import (
    CellFormat, Color, TextFormat,
    ConditionalFormatRule, BooleanRule, BooleanCondition,
    GridRange, format_cell_range, get_conditional_format_rules
)

# ===== קונפיגורציה כללית =====
st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו", layout="centered")
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&family=Noto+Sans+Hebrew:wght@400;600&display=swap" rel="stylesheet">

<style>
:root { --app-font: 'Assistant', 'Noto Sans Hebrew', 'Segoe UI', -apple-system, sans-serif; }

/* בסיס האפליקציה */
html, body, .stApp, [data-testid="stAppViewContainer"], .main {
  font-family: var(--app-font) !important;
}

/* ודא שכל הצאצאים יורשים את הפונט */
.stApp * {
  font-family: var(--app-font) !important;
}

/* רכיבי קלט/בחירה של Streamlit */
div[data-baseweb], /* select/radio/checkbox */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div,
.stMultiSelect div,
.stRadio,
.stCheckbox,
.stButton > button {
  font-family: var(--app-font) !important;
}

/* טבלאות DataFrame/Arrow */
div[data-testid="stDataFrame"] div {
  font-family: var(--app-font) !important;
}

/* כותרות */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--app-font) !important;
}
</style>
""", unsafe_allow_html=True)
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
SPECIALIZATIONS = ["רווחה","מוגבלות","זקנה","ילדים ונוער","בריאות הנפש",
                   "שיקום","משפחה","נשים","בריאות","קהילה"]

# ===== סדר עמודות =====
COLUMNS_ORDER = [
    "תאריך שליחה",
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
    "חוות דעת - נקודות",
    "חוות דעת - טקסט חופשי",
    "טלפון",
    "אימייל",
]

# ===== פונקציית עיצוב =====
def style_google_sheet(ws):
    header_fmt = CellFormat(
        backgroundColor=Color(0.4, 0.8, 0.6),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),
        horizontalAlignment='CENTER'
    )
    format_cell_range(ws, "1:1", header_fmt)

    rule = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range('A2:Z1000', ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('CUSTOM_FORMULA', ['=ISEVEN(ROW())']),
            format=CellFormat(backgroundColor=Color(0.95, 0.95, 0.95))
        )
    )
    rules = get_conditional_format_rules(ws)
    rules.clear()
    rules.append(rule)
    rules.save()

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
        if not existing or existing[0] != COLUMNS_ORDER:
            worksheet.clear()
            worksheet.append_row(COLUMNS_ORDER, value_input_option="USER_ENTERED")

        row_values = [record.get(col, "") for col in COLUMNS_ORDER]
        worksheet.append_row(row_values, value_input_option="USER_ENTERED")
        style_google_sheet(worksheet)
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
        help="מדריך חדש יישלח לקורס הכשרה מתאים"
    )

    st.subheader("מוסד ההכשרה")
    institute_select = st.text_input("שם המוסד *")
    spec_choice = st.selectbox("תחום התמחות *", ["בחר/י מהרשימה"] + SPECIALIZATIONS)

    st.subheader("כתובת המוסד")
    street = st.text_input("רחוב *")
    city = st.text_input("עיר *")
    postal_code = st.text_input("מיקוד *")

    st.subheader("קליטת סטודנטים")
    num_students = st.selectbox("מספר סטודנטים שניתן לקלוט (1 או 2) *", [1, 2])

    st.subheader("המשכיות הדרכה")
    continue_mentoring = st.radio("האם אתה מעוניין להמשיך להדריך? *", ["כן", "לא"])

    st.subheader("בקשות מיוחדות")
    special_requests = st.text_area(
        "בקשות מיוחדות (למשל: הדרכה בערב, שפות, נגישות, אילוצים)",
        placeholder="כתוב/י כאן כל בקשה שתרצה שניקח בחשבון בשיבוץ"
    )

    st.subheader("חוות דעת על המדריך")
    mentor_feedback_points = st.multiselect(
       "סמן/י נקודות רלוונטיות",
       ["סבלני", "מקצועי", "זמין", "קשוב", "מאפשר התנסות", "אחר"],
       placeholder="בחר/י מהרשימה"
   )

    mentor_feedback_text = st.text_area(
        "כתיבה חופשית (פירוט נוסף)",
        placeholder="כתוב/י כאן חוות דעת חופשית..."
    )


    st.subheader("פרטי התקשרות")
    phone = st.text_input("מספר טלפון *")
    email = st.text_input("כתובת דוא\"ל *")

    submit_btn = st.form_submit_button("שלח/י", use_container_width=True)

# ===== טיפול בטופס =====
if submit_btn:
    errors = []
    if not first_name.strip():
        errors.append("יש למלא שם פרטי")
    if not last_name.strip():
        errors.append("יש למלא שם משפחה")
    if spec_choice == "בחר מהרשימה":
        errors.append("יש לבחור תחום התמחות")
    if not institute_select.strip():
        errors.append("יש למלא שם מוסד")
    if not street.strip():
        errors.append("יש למלא רחוב")
    if not city.strip():
        errors.append("יש למלא עיר")
    if not postal_code.strip():
        errors.append("יש למלא מיקוד")

    phone_clean = phone.strip().replace("-", "").replace(" ", "")
    if not re.match(r"^(0?5\d{8})$", phone_clean):
        errors.append("מספר הטלפון אינו תקין (דוגמה: 0501234567)")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email.strip()):
        errors.append("כתובת הדוא\"ל אינה תקינה")

    if errors:
        for e in errors:
            st.error(e)
    else:
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
            "חוות דעת - נקודות": "; ".join(mentor_feedback_points),
            "חוות דעת - טקסט חופשי": mentor_feedback_text.strip(),
            "טלפון": phone_clean,
            "אימייל": email.strip()
        }
        save_to_google_sheets(record)
        st.success("✅ הנתונים נשמרו בהצלחה!")
