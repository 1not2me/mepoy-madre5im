# streamlit_app.py
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from io import BytesIO
from datetime import datetime
import re

import streamlit as st
import pandas as pd

# ===== הגדרות קבועות =====
st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו", layout="centered")
ADMIN_PASSWORD = "rawan_0304"

# ספריית נתונים + קבצים
DATA_DIR = Path("data")
BACKUP_DIR = DATA_DIR / "backups"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = DATA_DIR / "mapping_data.csv"          # קובץ ראשי (נשמר ומעודכן לאורך זמן)
CSV_LOG_FILE = DATA_DIR / "mapping_data_log.csv"  # קובץ יומן הוספות (Append-Only)
SITES_FILE = DATA_DIR / "sites_catalog.csv"       # אופציונלי: קטלוג מוסדות/תחומים

# ===== עיצוב =====
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

# ===== פונקציות עזר לקבצים =====
def load_csv_safely(path: Path) -> pd.DataFrame:
    """קריאה בטוחה של CSV אם קיים, אחרת מחזיר DataFrame ריק."""
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.read_csv(path, encoding="utf-8-sig")
    return pd.DataFrame()

def save_master_dataframe(df: pd.DataFrame) -> None:
    """
    שומר את המסד הראשי בצורה אטומית + יוצר גיבוי מתוארך.
    """
    temp_path = CSV_FILE.with_suffix(".tmp.csv")
    df.to_csv(temp_path, index=False, encoding="utf-8-sig")
    temp_path.replace(CSV_FILE)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"mapping_data_{ts}.csv"
    df.to_csv(backup_path, index=False, encoding="utf-8-sig")

def append_to_log(row_df: pd.DataFrame) -> None:
    """Append-Only: לעולם לא מוחקים, רק מוסיפים שורה חדשה."""
    file_exists = CSV_LOG_FILE.exists()
    row_df.to_csv(
        CSV_LOG_FILE,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig"
    )

def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """ממיר DataFrame ל-XLSX בזיכרון (BytesIO)."""
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        # התאמת רוחב עמודות בסיסית
        ws = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            width = min(60, max(12, int(df[col].astype(str).map(len).max() if not df.empty else 12) + 4))
            ws.set_column(i, i, width)
    bio.seek(0)
    return bio.read()

# ===== קריאת קטלוג מוסדות (אופציונלי) =====
def load_sites_catalog() -> pd.DataFrame:
    """
    מנסה לקרוא קטלוג מוסדות. מצפה לעמודות:
    - 'שם מוסד' (או חלופות: 'מוסד', 'שם מוסד/שירות ההכשרה')
    - 'תחום התמחות' (או חלופות: 'תחום', 'התמחות')
    אם חסר או לא קיים – מחזיר DF ריק ומציג אזהרה עדינה (ללא חריגה).
    """
    if not SITES_FILE.exists():
        return pd.DataFrame()

    df = load_csv_safely(SITES_FILE)
    if df.empty:
        st.warning("⚠ קובץ המוסדות קיים אך ריק.")
        return pd.DataFrame()

    # נרמול שמות עמודות אפשריים
    cols = {c.strip(): c for c in df.columns}

    def pick(*options):
        for opt in options:
            if opt in cols:
                return cols[opt]
        return None

    # נסיונות זיהוי גמישים
    col_institution = pick('שם מוסד', 'מוסד', 'שם מוסד/שירות ההכשרה')
    col_spec        = pick('תחום התמחות', 'תחום', 'התמחות')

    if not col_institution or not col_spec:
        st.warning("⚠ בקובץ האתרים חסרות עמודות חובה: 'שם מוסד' / 'תחום התמחות'. הטופס יעבוד במצב קלט חופשי.")
        return pd.DataFrame()

    clean = (
        df[[col_institution, col_spec]]
        .rename(columns={col_institution: 'שם מוסד', col_spec: 'תחום התמחות'})
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # ניקוי טקסט בסיסי
    for c in ['שם מוסד', 'תחום התמחות']:
        clean[c] = clean[c].astype(str).str.strip()

    return clean

sites_df = load_sites_catalog()
sites_available = not sites_df.empty
known_specs = sorted(sites_df['תחום התמחות'].dropna().unique().tolist()) if sites_available else []
known_institutions = sorted(sites_df['שם מוסד'].dropna().unique().tolist()) if sites_available else []

# ===== בדיקת מצב מנהל =====
params = st.query_params if hasattr(st, "query_params") else {}
admin_flag = params.get("admin", "0")
is_admin_mode = (admin_flag == "1")

# ===== מצב מנהל =====
if is_admin_mode:
    st.title("🔑 גישת מנהל - צפייה בנתונים (נשמר לאורך זמן)")

    password = st.text_input("הכנס סיסמת מנהל", type="password", key="admin_pwd_input")
    if password == ADMIN_PASSWORD:
        st.success("התחברת בהצלחה ✅")

        # טען נתונים
        df_master = load_csv_safely(CSV_FILE)
        df_log = load_csv_safely(CSV_LOG_FILE)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 קובץ ראשי (מצטבר)")
            st.write(f"סה\"כ רשומות: **{len(df_master)}**")
        with col2:
            st.subheader("🧾 קובץ יומן (Append-Only)")
            st.write(f"סה\"כ רשומות (יומן): **{len(df_log)}**")

        # תצוגה והורדות – XLSX בלבד לפי בקשה
        st.markdown("### הצגת הקובץ הראשי")
        if not df_master.empty:
            st.dataframe(df_master, use_container_width=True)
            st.download_button(
                "📊 הורד Excel (ראשי)",
                data=dataframe_to_excel_bytes(df_master, sheet_name="Master"),
                file_name="mapping_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_master_xlsx"
            )
        else:
            st.info("⚠ עדיין אין נתונים בקובץ הראשי.")

        st.markdown("---")
        st.markdown("### הצגת קובץ היומן (Append-Only)")
        if not df_log.empty:
            st.dataframe(df_log, use_container_width=True)
            st.download_button(
                "📊 הורד Excel (יומן)",
                data=dataframe_to_excel_bytes(df_log, sheet_name="Log"),
                file_name="mapping_data_log.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_log_xlsx"
            )
        else:
            st.info("⚠ עדיין אין נתונים ביומן.")
    else:
        if password:
            st.error("סיסמה שגויה")
    st.stop()

# ===== טופס למילוי =====
st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")
st.write("""
שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה.  
אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.
""")

with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    last_name = st.text_input("שם משפחה *", key="last_name")
    first_name = st.text_input("שם פרטי *", key="first_name")

    st.subheader("מוסד והכשרה")
    # אם יש קטלוג – נשתמש ב-Selectbox; אחרת שדה חופשי
    if sites_available:
        specialization = st.selectbox("תחום ההתמחות *", ["בחר מהרשימה"] + known_specs, key="specialization")
        # מוסדות מסוננים לפי תחום שבחרו (אם נבחר)
        filtered_institutions = (
            sorted(sites_df[sites_df['תחום התמחות'] == specialization]['שם מוסד'].unique().tolist())
            if specialization in known_specs else known_institutions
        )
        institution = st.selectbox("מוסד / שירות ההכשרה *", ["בחר מהרשימה"] + filtered_institutions, key="institution_select")
        specialization_other = ""  # לא נדרש כשיש קטלוג
    else:
        specialization = st.selectbox("תחום ההתמחות *", ["בחר מהרשימה", "חינוך", "בריאות", "רווחה", "אחר"], key="specialization")
        institution = st.text_input("מוסד / שירות ההכשרה *", key="institution")
        specialization_other = st.text_input("אם ציינת 'אחר', אנא כתוב/י את תחום ההתמחות *", key="specialization_other") if specialization == "אחר" else ""

    st.subheader("כתובת מקום ההכשרה")
    street = st.text_input("רחוב *", key="street")
    city = st.text_input("עיר *", key="city")
    postal_code = st.text_input("מיקוד *", key="postal_code")

    st.subheader("קליטת סטודנטים")
    num_students = st.number_input("מספר סטודנטים שניתן לקלוט השנה *", min_value=1, step=1, key="num_students")
    continue_mentoring = st.radio("האם מעוניין/ת להמשיך להדריך השנה *", ["כן", "לא"], key="continue_mentoring")

    st.subheader("פרטי התקשרות")
    phone = st.text_input("טלפון * (לדוגמה: 050-1234567)", key="phone")
    email = st.text_input("כתובת אימייל *", key="email")

    submit_btn = st.form_submit_button("שלח/י", use_container_width=True)

# ===== טיפול בטופס =====
if submit_btn:
    errors = []

    if not last_name.strip():
        errors.append("יש למלא שם משפחה")
    if not first_name.strip():
        errors.append("יש למלא שם פרטי")

    # אימות מוסד/התמחות בהתאם לזמינות קטלוג
    if sites_available:
        if specialization == "בחר מהרשימה":
            errors.append("יש לבחור תחום התמחות")
        if institution == "בחר מהרשימה":
            errors.append("יש לבחור מוסד/שירות הכשרה")
        # ולידציה שהמוסד תואם לתחום שנבחר
        if specialization in known_specs and institution in known_institutions:
            ok = not sites_df[(sites_df['תחום התמחות'] == specialization) & (sites_df['שם מוסד'] == institution)].empty
            if not ok:
                errors.append("המוסד שנבחר אינו תואם לתחום ההתמחות שבחרת.")
    else:
        if not institution.strip():
            errors.append("יש למלא מוסד/שירות ההכשרה")
        if specialization == "בחר מהרשימה":
            errors.append("יש לבחור תחום התמחות")
        if specialization == "אחר" and not specialization_other.strip():
            errors.append("יש למלא את תחום ההתמחות")

    if not street.strip():
        errors.append("יש למלא רחוב")
    if not city.strip():
        errors.append("יש למלא עיר")
    if not postal_code.strip():
        errors.append("יש למלא מיקוד")
    # טלפון ואימייל
    if not re.match(r"^0\d{1,2}-\d{6,7}$", phone.strip()):
        errors.append("מספר הטלפון אינו תקין (דוגמה תקינה: 050-1234567)")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email.strip()):
        errors.append("כתובת האימייל אינה תקינה")

    if errors:
        for e in errors:
            st.error(e)
    else:
        # בניית הרשומה לשמירה
        final_spec = specialization if (sites_available and specialization in known_specs and specialization != "בחר מהרשימה") else \
                     (specialization_other.strip() if specialization == "אחר" else specialization)
        final_institution = institution if (sites_available and institution != "בחר מהרשימה") else institution.strip()

        record = {
            "תאריך": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "שם משפחה": last_name.strip(),
            "שם פרטי": first_name.strip(),
            "מוסד/שירות ההכשרה": final_institution,
            "תחום התמחות": final_spec,
            "רחוב": street.strip(),
            "עיר": city.strip(),
            "מיקוד": postal_code.strip(),
            "מספר סטודנטים": int(num_students),
            "המשך הדרכה": continue_mentoring,
            "טלפון": phone.strip(),
            "אימייל": email.strip()
        }
        new_row_df = pd.DataFrame([record])

        # 1) עדכון הקובץ הראשי (ללא מחיקה) + גיבוי מתוארך
        master_df = load_csv_safely(CSV_FILE)
        master_df = pd.concat([master_df, new_row_df], ignore_index=True)
        save_master_dataframe(master_df)

        # 2) רישום ליומן (Append-Only)
        append_to_log(new_row_df)

        # ✅ הודעת הצלחה תקינה
        st.success("✅ הנתונים נשמרו בהצלחה!")
