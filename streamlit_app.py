import streamlit as st
import pandas as pd
import os
import subprocess

# שם הקובץ שבו נשמור את התשובות
CSV_FILE = "mapping_data.csv"

st.title("מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")
st.write("שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה. אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.")

# שדות הטופס
full_name_last = st.text_input("שם משפחה")
full_name_first = st.text_input("שם פרטי")
institution = st.text_input("מוסד / שירות ההכשרה")
specialization = st.selectbox("תחום ההתמחות", ["Please Select", "פסיכולוגיה", "עבודה סוציאלית", "חינוך", "אחר"])
if specialization == "אחר":
    specialization_other = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות")
else:
    specialization_other = ""
address_street = st.text_input("רחוב")
address_city = st.text_input("עיר")
address_zip = st.text_input("מיקוד")
students_capacity = st.number_input("מספר סטודנטים שניתן לקלוט השנה", min_value=0, step=1)
continue_teaching = st.selectbox("האם מעוניין/ת להמשיך להדריך השנה", ["כן", "לא"])
phone = st.text_input("טלפון", placeholder="(000) 000-0000")
email = st.text_input("כתובת אימייל", placeholder="example@example.com")

# כפתור שליחה
if st.button("שלח/י"):
    # יצירת DataFrame משורה אחת
    new_data = pd.DataFrame([{
        "שם משפחה": full_name_last,
        "שם פרטי": full_name_first,
        "מוסד / שירות ההכשרה": institution,
        "תחום ההתמחות": specialization,
        "תחום התמחות אחר": specialization_other,
        "רחוב": address_street,
        "עיר": address_city,
        "מיקוד": address_zip,
        "מספר סטודנטים שניתן לקלוט": students_capacity,
        "האם ממשיך השנה": continue_teaching,
        "טלפון": phone,
        "אימייל": email
    }])

    # אם הקובץ כבר קיים – נטען אותו ונוסיף את השורה
    if os.path.exists(CSV_FILE):
        existing_data = pd.read_csv(CSV_FILE)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    else:
        updated_data = new_data

    # שמירה מקומית
    updated_data.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

    # העלאה ל־GitHub
    subprocess.run(["git", "add", CSV_FILE])
    subprocess.run(["git", "commit", "-m", "עדכון נתוני טופס"])
    subprocess.run(["git", "push"])

    st.success("הטופס נשלח בהצלחה! הנתונים נשמרו ב־GitHub שלך.")

# הצגת הנתונים (רק לך)
if st.checkbox("הצג את כל התשובות (רק למנהל)"):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        st.dataframe(df)
        st.download_button("הורד קובץ CSV", df.to_csv(index=False, encoding="utf-8-sig"), "mapping_data.csv")
    else:
        st.warning("אין נתונים להצגה כרגע.")
