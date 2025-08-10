import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")

# --- טופס מילוי ---
with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    full_name = st.text_input("שם מלא של המדריך/ה")
    last_name = st.text_input("שם משפחה")
    first_name = st.text_input("שם פרטי")
    institution = st.text_input("מוסד / שירות ההכשרה")
    specialty = st.selectbox("תחום ההתמחות", ["Please Select", "חינוך", "בריאות", "חברה", "אחר"])
    specialty_other = ""
    if specialty == "אחר":
        specialty_other = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות")
    street = st.text_input("רחוב")
    city = st.text_input("עיר")
    zip_code = st.text_input("מיקוד")
    students_num = st.number_input("מספר סטודנטים שניתן לקלוט השנה", min_value=0, step=1)
    continue_teaching = st.radio("האם מעוניין/ת להמשיך להדריך השנה", ["כן", "לא"])
    phone = st.text_input("טלפון (בפורמט 000-0000000)")
    email = st.text_input("כתובת אימייל")

    submit_btn = st.form_submit_button("שלח/י")

# --- שמירת נתונים ---
if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם מלא": [full_name],
        "שם משפחה": [last_name],
        "שם פרטי": [first_name],
        "מוסד / שירות ההכשרה": [institution],
        "תחום ההתמחות": [specialty if specialty != "אחר" else specialty_other],
        "רחוב": [street],
        "עיר": [city],
        "מיקוד": [zip_code],
        "מס' סטודנטים": [students_num],
        "המשך הדרכה": [continue_teaching],
        "טלפון": [phone],
        "אימייל": [email]
    }

    df = pd.DataFrame(data)

    file_path = "mapping_data.csv"
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, index=False)

    st.success("✅ הנתונים נשמרו בהצלחה!")


