import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="📋 מיפוי מדריכים לשיבוץ סטודנטים", layout="centered")

# בחירת מצב
mode = st.radio("בחר מצב", ["מילוי טופס", "כניסת מנהל"])

if mode == "מילוי טופס":
    st.title("📋 טופס מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו")
    st.write("שלום רב, מטרת טופס זה היא לאסוף מידע עדכני על מדריכים ומוסדות הכשרה לקראת שיבוץ הסטודנטים לשנת ההכשרה הקרובה. אנא מלא/י את כל השדות בצורה מדויקת. המידע ישמש לצורך תכנון השיבוץ בלבד.")

    with st.form("mapping_form"):
        full_name = st.text_input(":שם מלא של המדריך/ה*")
        last_name = st.text_input("שם משפחה")
        first_name = st.text_input("שם פרטי")
        institution = st.text_input(":מוסד / שירות ההכשרה*")
        specialty = st.selectbox(":תחום ההתמחות*", ["Please Select", "חינוך", "בריאות", "רווחה", "אחר"])
        other_specialty = ""
        if specialty == "אחר":
            other_specialty = st.text_input(":אם ציינת אחר, אנא כתוב את תחום ההתמחות*")
        street = st.text_input(":רחוב")
        city = st.text_input("עיר")
        zip_code = st.text_input(":מיקוד")
        num_students = st.number_input(":מספר סטודנטים שניתן לקלוט השנה*", min_value=0, step=1)
        continue_teaching = st.radio("?האם מעוניין/ת להמשיך להדריך השנה*", ["כן", "לא"])
        phone = st.text_input(":טלפון*")
        email = st.text_input(":כתובת אימייל*")

        submit_btn = st.form_submit_button("שלח/י")

    if submit_btn:
        data = {
            "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "שם מלא": [full_name],
            "שם משפחה": [last_name],
            "שם פרטי": [first_name],
            "מוסד / שירות ההכשרה": [institution],
            "תחום ההתמחות": [specialty if specialty != "אחר" else other_specialty],
            "רחוב": [street],
            "עיר": [city],
            "מיקוד": [zip_code],
            "מספר סטודנטים": [num_students],
            "ממשיך להדריך": [continue_teaching],
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

elif mode == "כניסת מנהל":
    st.subheader("🔑 כניסת מנהל")
    password = st.text_input("הכנס סיסמה", type="password")
    
    if password == "rawan_0304":
        st.success("ברוך הבא! כאן ניתן לראות ולהוריד את הנתונים.")
        
        try:
            df = pd.read_csv("mapping_data.csv")
            st.dataframe(df)

            # הורדת הקובץ כ-CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="⬇️ הורד קובץ CSV",
                data=csv_buffer.getvalue(),
                file_name="mapping_data.csv",
                mime="text/csv"
            )
        except FileNotFoundError:
            st.warning("⚠️ עדיין לא נשמרו נתונים.")
    elif password != "":
        st.error("סיסמה שגויה ❌")
