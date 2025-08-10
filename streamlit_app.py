import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ----- הגדרות -----
ADMIN_PASSWORD = "1234"  # כאן תחליפי לסיסמה שלך

# כותרת הדף
st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")
st.write("שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה. "
         "אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.")

# ----- טופס מילוי -----
with st.form("mapping_form"):
    last_name = st.text_input("שם משפחה*")
    first_name = st.text_input("שם פרטי*")
    institution = st.text_input("מוסד / שירות ההכשרה*")
    specialty = st.selectbox("תחום ההתמחות*", ["Please Select", "חינוך", "בריאות", "רווחה", "אחר"])
    other_specialty = ""
    if specialty == "אחר":
        other_specialty = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות*")
    street = st.text_input("רחוב")
    city = st.text_input("עיר")
    postal_code = st.text_input("מיקוד")
    num_students = st.number_input("מספר סטודנטים שניתן לקלוט השנה*", min_value=0, step=1)
    continue_guiding = st.radio("האם מעוניין/ת להמשיך להדריך השנה*", ["כן", "לא"])
    phone = st.text_input("טלפון*")
    email = st.text_input("כתובת אימייל*")
    
    submit_btn = st.form_submit_button("שלח/י")

if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם משפחה": [last_name],
        "שם פרטי": [first_name],
        "מוסד/שירות הכשרה": [institution],
        "תחום התמחות": [specialty],
        "תחום התמחות אחר": [other_specialty],
        "רחוב": [street],
        "עיר": [city],
        "מיקוד": [postal_code],
        "מספר סטודנטים": [num_students],
        "המשך הדרכה": [continue_guiding],
        "טלפון": [phone],
        "אימייל": [email]
    }
    df = pd.DataFrame(data)
    try:
        existing_df = pd.read_csv("mapping_data.csv")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv("mapping_data.csv", index=False)
    except FileNotFoundError:
        df.to_csv("mapping_data.csv", index=False)
    st.success("✅ הנתונים נשמרו בהצלחה!")

# ----- מצב מנהל -----
st.subheader("🔑 כניסת מנהל")
admin_password_input = st.text_input("הכנס/י סיסמת מנהל", type="password")
if admin_password_input == ADMIN_PASSWORD:
    st.session_state["admin_view"] = True
    st.success("ברוך הבא, מנהל!")
elif admin_password_input != "":
    st.error("סיסמה שגויה")

# ----- הצגת והורדת נתונים -----
if st.session_state.get("admin_view", False):
    if os.path.exists("mapping_data.csv"):
        st.subheader("📊 כל התשובות שנאספו")
        df = pd.read_csv("mapping_data.csv")
        st.dataframe(df)

        with open("mapping_data.csv", "rb") as file:
            st.download_button(
                label="📥 הורד את קובץ התשובות",
                data=file,
                file_name="mapping_data.csv",
                mime="text/csv"
            )
