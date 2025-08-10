import streamlit as st
import pandas as pd
from datetime import datetime
import io

# סיסמה למנהל
ADMIN_PASSWORD = "1234"  # כאן תשני לסיסמה שלך

st.set_page_config(page_title="📋 מיפוי מדריכים", layout="centered")

st.title("📋 טופס מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו")
st.write("שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה. "
         "אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.")

# ----------- טופס מילוי -----------
with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    last_name = st.text_input("שם משפחה *")
    first_name = st.text_input("שם פרטי *")
    institution = st.text_input("מוסד / שירות ההכשרה *")
    specialization = st.selectbox("תחום ההתמחות *", ["Please Select", "חינוך", "רפואה", "טיפול", "אחר"])
    if specialization == "אחר":
        specialization_other = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות *")
    else:
        specialization_other = ""

    address_street = st.text_input("רחוב")
    address_city = st.text_input("עיר")
    address_zip = st.text_input("מיקוד")
    students_capacity = st.number_input("מספר סטודנטים שניתן לקלוט השנה *", min_value=0, step=1)
    continue_guiding = st.radio("האם מעוניין/ת להמשיך להדריך השנה *", ["כן", "לא"])
    phone = st.text_input("טלפון * (לדוגמה: 050-0000000)")
    email = st.text_input("כתובת אימייל *")

    submit_btn = st.form_submit_button("שלח/י")

# ----------- שמירת נתונים -----------
if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם משפחה": [last_name],
        "שם פרטי": [first_name],
        "מוסד/שירות ההכשרה": [institution],
        "תחום התמחות": [specialization_other if specialization == "אחר" else specialization],
        "רחוב": [address_street],
        "עיר": [address_city],
        "מיקוד": [address_zip],
        "מספר סטודנטים": [students_capacity],
        "המשך הדרכה": [continue_guiding],
        "טלפון": [phone],
        "אימייל": [email]
    }

    df = pd.DataFrame(data)

    try:
        existing_df = pd.read_csv("mapping_data.csv")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv("mapping_data.csv", index=False, encoding="utf-8-sig")
    except FileNotFoundError:
        df.to_csv("mapping_data.csv", index=False, encoding="utf-8-sig")

    st.success("✅ הנתונים נשמרו בהצלחה! תודה על מילוי הטופס.")

# ----------- כניסת מנהל -----------
st.markdown("---")
st.subheader("🔑 כניסת מנהל")

admin_input = st.text_input("הכנס סיסמה", type="password")

if admin_input == ADMIN_PASSWORD:
    st.success("ברוך הבא! כאן תוכל/י לראות את כל התשובות.")
    try:
        df_all = pd.read_csv("mapping_data.csv")
        st.dataframe(df_all)

        # כפתור להורדת CSV
        csv_buffer = io.BytesIO()
        df_all.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="⬇ הורד את כל הנתונים (CSV)",
            data=csv_buffer.getvalue(),
            file_name="mapping_data.csv",
            mime="text/csv"
        )

    except FileNotFoundError:
        st.warning("⚠ עדיין אין נתונים בטופס.")
elif admin_input:
    st.error("סיסמה שגויה.")
import pandas as pd
import os

# הצגת תשובות רק למנהל
st.markdown("---")
st.subheader("🔑 כניסת מנהל")

password = st.text_input("הכנסי סיסמה:", type="password")
if password == "1234":  # כאן את יכולה לשנות לסיסמה שלך
    if os.path.exists("mapping_data.csv"):
        df = pd.read_csv("mapping_data.csv")
        st.dataframe(df)

        # כפתור להורדה
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="⬇ הורד קובץ CSV",
            data=csv,
            file_name="mapping_data.csv",
            mime="text/csv"
        )
    else:
        st.info("אין עדיין תשובות במערכת.")
