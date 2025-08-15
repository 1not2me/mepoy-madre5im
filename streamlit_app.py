import streamlit as st
import pandas as pd
from datetime import datetime
import re

# ===== הגדרות =====
st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו", layout="centered")
ADMIN_PASSWORD = "rawan_0304"
CSV_FILE = "mapping_data.csv"

# בדיקה אם המשתמש במצב מנהל
is_admin_mode = st.query_params.get("admin", ["0"])[0] == "1"

# ===== מצב מנהל =====
if is_admin_mode:
    st.title("🔑 גישת מנהל - צפייה בנתונים")
    password = st.text_input("הכנס סיסמת מנהל:", type="password")
    if password == ADMIN_PASSWORD:
        try:
            df = pd.read_csv(CSV_FILE)
            st.success("התחברת בהצלחה ✅")
            st.dataframe(df)
            st.download_button("📥 הורד CSV", data=df.to_csv(index=False).encode('utf-8-sig'),
                               file_name="mapping_data.csv", mime="text/csv")
        except FileNotFoundError:
            st.warning("⚠ עדיין אין נתונים שנשמרו.")
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
    last_name = st.text_input(":שם משפחה *")
    first_name = st.text_input(":שם פרטי *")

    st.subheader("מוסד והכשרה")
    institution = st.text_input(":מוסד / שירות ההכשרה *")
    specialization = st.selectbox(":תחום ההתמחות *", ["Please Select", "חינוך", "בריאות", "רווחה", "אחר"])
    specialization_other = ""
    if specialization == "אחר":
        specialization_other = st.text_input(":אם ציינת אחר, אנא כתוב את תחום ההתמחות *")

    st.subheader("כתובת מקום ההכשרה")
    street = st.text_input(":רחוב *")
    city = st.text_input("עיר *")
    postal_code = st.text_input(":מיקוד *")

    st.subheader("קליטת סטודנטים")
    num_students = st.number_input(":מספר סטודנטים שניתן לקלוט השנה *", min_value=0, step=1)
    continue_mentoring = st.radio("?האם מעוניין/ת להמשיך להדריך השנה *", ["כן", "לא"])

    st.subheader("פרטי התקשרות")
    phone = st.text_input(":טלפון * (לדוגמה: 050-1234567)")
    email = st.text_input(":כתובת אימייל *")

    submit_btn = st.form_submit_button("שלח/י")

# ===== טיפול בטופס =====
if submit_btn:
    errors = []

    if not last_name.strip():
        errors.append("יש למלא שם משפחה")
    if not first_name.strip():
        errors.append("יש למלא שם פרטי")
    if not institution.strip():
        errors.append("יש למלא מוסד/שירות ההכשרה")
    if specialization == "Please Select":
        errors.append("יש לבחור תחום התמחות")
    if specialization == "אחר" and not specialization_other.strip():
        errors.append("יש למלא את תחום ההתמחות")
    if not street.strip():
        errors.append("יש למלא רחוב")
    if not city.strip():
        errors.append("יש למלא עיר")
    if not postal_code.strip():
        errors.append("יש למלא מיקוד")
    if num_students <= 0:
        errors.append("יש להזין מספר סטודנטים גדול מ-0")
    if not re.match(r"^0\d{1,2}-\d{6,7}$", phone.strip()):
        errors.append("מספר הטלפון אינו תקין")
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email.strip()):
        errors.append("כתובת האימייל אינה תקינה")

    if errors:
        for e in errors:
            st.error(e)
    else:
        data = {
            "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "שם משפחה": [last_name],
            "שם פרטי": [first_name],
            "מוסד/שירות ההכשרה": [institution],
            "תחום התמחות": [specialization_other if specialization == "אחר" else specialization],
            "רחוב": [street],
            "עיר": [city],
            "מיקוד": [postal_code],
            "מספר סטודנטים": [num_students],
            "המשך הדרכה": [continue_mentoring],
            "טלפון": [phone],
            "אימייל": [email]
        }

        df = pd.DataFrame(data)

        try:
            existing_df = pd.read_csv(CSV_FILE)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_csv(CSV_FILE, index=False)
        except FileNotFoundError:
            df.to_csv(CSV_FILE, index=False)

        st.success("✅ הנתונים נשמרו בהצלחה!")

