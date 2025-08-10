import streamlit as st
import pandas as pd
from datetime import datetime

# כותרת הדף
st.title("📋 טופס מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו")
st.write("""
שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה.
אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.
""")

# יצירת טופס
with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    full_name = st.text_input("שם מלא של המדריך/ה")
    first_name = st.text_input("שם פרטי")
    last_name = st.text_input("שם משפחה")
    training_institution = st.text_input("מוסד / שירות ההכשרה")
    specialty = st.selectbox("תחום ההתמחות", ["Please Select", "תחום א", "תחום ב", "תחום ג", "אחר"])
    other_specialty = ""
    if specialty == "אחר":
        other_specialty = st.text_input("אם ציינת אחר, אנא כתוב את תחום ההתמחות")

    st.subheader("כתובת מקום ההכשרה")
    street = st.text_input("רחוב")
    city = st.text_input("עיר")
    postal_code = st.text_input("מיקוד")

    students_count = st.number_input("מספר סטודנטים שניתן לקלוט השנה", min_value=0, step=1)
    continue_training = st.radio("האם מעוניין/ת להמשיך להדריך השנה?", ["כן", "לא"])
    phone = st.text_input("טלפון")
    email = st.text_input("כתובת אימייל")
    
    notes = st.text_area("הערות")

    submit_btn = st.form_submit_button("שלח")

# שמירת הנתונים אם נשלח
if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם מלא": [full_name],
        "שם פרטי": [first_name],
        "שם משפחה": [last_name],
        "מוסד / שירות ההכשרה": [training_institution],
        "תחום התמחות": [specialty if specialty != "אחר" else other_specialty],
        "רחוב": [street],
        "עיר": [city],
        "מיקוד": [postal_code],
        "מספר סטודנטים": [students_count],
        "ממשיך הדרכה": [continue_training],
        "טלפון": [phone],
        "אימייל": [email],
        "הערות": [notes]
    }

    df = pd.DataFrame(data)

    try:
        existing_df = pd.read_csv("mapping_data.csv")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv("mapping_data.csv", index=False)
    except FileNotFoundError:
        df.to_csv("mapping_data.csv", index=False)

    st.success("✅ הנתונים נשמרו בהצלחה!")

# הצגת הנתונים — יוצג רק כשאת פותחת את האפליקציה דרך החשבון שלך
if st.sidebar.checkbox("הצג את כל התשובות (למנהל בלבד)"):
    try:
        all_data = pd.read_csv("mapping_data.csv")
        st.subheader("📄 כל התשובות שנשמרו:")
        st.dataframe(all_data)

        csv = all_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 הורד את כל התשובות כ-CSV",
            data=csv,
            file_name="mapping_data.csv",
            mime="text/csv"
        )
    except FileNotFoundError:
        st.warning("אין עדיין תשובות שמורות.")
