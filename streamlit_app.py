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

# ===== עיצוב =====
st.markdown("""
<style>
:root{
  --ink:#0f172a; 
  --muted:#475569; 
  --ring:rgba(99,102,241,.25); 
  --card:rgba(255,255,255,.85);
}

/* RTL + פונטים */
html, body, [class*="css"] { font-family: system-ui, "Segoe UI", Arial; }
.stApp, .main, [data-testid="stSidebar"]{ direction:rtl; text-align:right; }

/* רקע */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(1200px 600px at 8% 8%, #e0f7fa 0%, transparent 65%),
    radial-gradient(1000px 500px at 92% 12%, #ede7f6 0%, transparent 60%),
    radial-gradient(900px 500px at 20% 90%, #fff3e0 0%, transparent 55%);
}
.block-container{ padding-top:1.1rem; }

/* מסגרת לטופס */
[data-testid="stForm"]{
  background:var(--card);
  border:1px solid #e2e8f0;
  border-radius:16px;
  padding:18px 20px;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
}

/* תוויות + נקודתיים מימין */
[data-testid="stWidgetLabel"] p{
  text-align:right; 
  margin-bottom:.25rem; 
  color:var(--muted); 
}
[data-testid="stWidgetLabel"] p::after{
  content: " :";
}

/* שדות */
input, textarea, select{ direction:rtl; text-align:right; }
</style>
""", unsafe_allow_html=True)

# ===== פונקציות עזר לקבצים =====
def load_csv_safely(path: Path) -> pd.DataFrame:
    """קריאה בטוחה של CSV אם קיים, אחרת מחזיר DataFrame ריק עם עמודות סטנדרטיות (אם ידועות)."""
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            # אם יש בעיה בקריאה, ננסה עם encoding חלופי
            return pd.read_csv(path, encoding="utf-8-sig")
    else:
        return pd.DataFrame()

def save_master_dataframe(df: pd.DataFrame) -> None:
    """
    שומר את המסד הראשי (mapping_data.csv) בצורה אטומית.
    לא מוחק רשומות קיימות – רק מעדכן את הקובץ עם כל הנתונים.
    שומר גם גיבוי מתוארך בתיקיית backups.
    """
    # שמירה אטומית: כתיבה לקובץ זמני ואז החלפה
    temp_path = CSV_FILE.with_suffix(".tmp.csv")
    df.to_csv(temp_path, index=False, encoding="utf-8-sig")
    temp_path.replace(CSV_FILE)

    # שמירת גיבוי מתוארך
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"mapping_data_{ts}.csv"
    df.to_csv(backup_path, index=False, encoding="utf-8-sig")

def append_to_log(row_df: pd.DataFrame) -> None:
    """
    רישום Append-Only של כל הרשומות שנוספו, כדי שלעולם לא ילכו לאיבוד.
    כותב כותרת רק אם הקובץ עדיין לא קיים.
    """
    file_exists = CSV_LOG_FILE.exists()
    row_df.to_csv(
        CSV_LOG_FILE,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig"
    )

def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """ממיר DataFrame לקובץ Excel בזיכרון (BytesIO)."""
    bio = BytesIO()
    try:
        with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        bio.seek(0)
        return bio.read()
    except Exception:
        # אם xlsxwriter לא זמין, נחזיר None ונמנע מכפתור אקסל
        return b""

# ===== בדיקת מצב מנהל =====
# תמיכה ב-Streamlit חדשים: st.query_params הוא מילון של מחרוזות
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

        # מידע כללי
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📦 קובץ ראשי (מצטבר)")
            st.write(f"סה\"כ רשומות: **{len(df_master)}**")
        with col2:
            st.subheader("🧾 קובץ יומן (Append-Only)")
            st.write(f"סה\"כ רשומות (יומן): **{len(df_log)}**")

        # תצוגה והורדות
        st.markdown("### הצגת הקובץ הראשי")
        if not df_master.empty:
            st.dataframe(df_master, use_container_width=True)
            st.download_button(
                "📥 הורד CSV (ראשי)",
                data=df_master.to_csv(index=False, encoding="utf-8-sig"),
                file_name="mapping_data.csv",
                mime="text/csv",
                key="dl_master_csv"
            )
            excel_bytes = dataframe_to_excel_bytes(df_master)
            if excel_bytes:
                st.download_button(
                    "📊 הורד Excel (ראשי)",
                    data=excel_bytes,
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
                "📥 הורד CSV (יומן)",
                data=df_log.to_csv(index=False, encoding="utf-8-sig"),
                file_name="mapping_data_log.csv",
                mime="text/csv",
                key="dl_log_csv"
            )
            excel_bytes_log = dataframe_to_excel_bytes(df_log, sheet_name="Log")
            if excel_bytes_log:
                st.download_button(
                    "📊 הורד Excel (יומן)",
                    data=excel_bytes_log,
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
    institution = st.text_input("מוסד / שירות ההכשרה *", key="institution")
    specialization = st.selectbox(
        "תחום ההתמחות *",
        ["בחר מהרשימה", "חינוך", "בריאות", "רווחה", "אחר"],
        key="specialization"
    )
    specialization_other = ""
    if specialization == "אחר":
        specialization_other = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות *", key="specialization_other")

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
    # תיקון Regex: אין צורך ב-\\ בתוך r-string
    if not re.match(r"^0\d{1,2}-\d{6,7}$", phone.strip()):
        errors.append("מספר הטלפון אינו תקין (דוגמה תקינה: 050-1234567)")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email.strip()):
        errors.append("כתובת האימייל אינה תקינה")

    if errors:
        for e in errors:
            st.error(e)
    else:
        # בניית הרשומה לשמירה
        record = {
            "תאריך": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "שם משפחה": last_name.strip(),
            "שם פרטי": first_name.strip(),
            "מוסד/שירות ההכשרה": institution.strip(),
            "תחום התמחות": (specialization_other.strip() if specialization == "אחר" else specialization),
            "רחוב": street.strip(),
            "עיר": city.strip(),
            "מיקוד": postal_code.strip(),
            "מספר סטודנטים": int(num_students),
            "המשך הדרכה": continue_mentoring,
            "טלפון": phone.strip(),
            "אימייל": email.strip()
        }
        new_row_df = pd.DataFrame([record])

        # 1) טען את המסד הראשי הקיים (אם יש), הוסף, ושמור (ללא מחיקה)
        master_df = load_csv_safely(CSV_FILE)
        master_df = pd.concat([master_df, new_row_df], ignore_index=True)
        save_master_dataframe(master_df)  # שמירה אטומית + גיבוי מתוארך

        # 2) כתיבה Append-Only ליומן
        append_to_log(new_row_df)

        st.success("✅ הנתונים נשמרו בהצלחה!")
