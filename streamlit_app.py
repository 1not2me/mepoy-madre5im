import streamlit as st
import pandas as pd
import os

CSV_FILE = "mapping_data.csv"

st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים", page_icon="📝")

st.title("📝 - מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")

# פונקציה לשמירת נתונים
def save_data(data):
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

# בחירת מצב - משתמש רגיל או מנהל
mode = st.sidebar.radio("בחר מצב", ["מילוי טופס", "כניסת מנהל"])

if mode == "מילוי טופס":
    with st.form("mapping_form"):
        full_name = st.text_input("שם מלא של המדריך/ה")
        last_name = st.text_input("שם משפחה")
        first_name = st.text_input("שם פרטי")
        institution = st.text_input("מוסד / שירות ההכשרה")
        field = st.selectbox("תחום ההתמחות", ["Please Select", "חינוך", "בריאות", "טכנולוגיה", "אחר"])
        street = st.text_input("רחוב")
        city = st.text_input("עיר")

        submitted = st.form_submit_button("שלח")

        if submitted:
            data = {
                "שם מלא": full_name,
                "שם משפחה": last_name,
                "שם פרטי": first_name,
                "מוסד/שירות הכשרה": institution,
                "תחום התמחות": field,
                "רחוב": street,
                "עיר": city
            }
            save_data(data)
            st.success("✅ הטופס נשלח בהצלחה!")

elif mode == "כניסת מנהל":
    password = st.text_input("הכנס סיסמה", type="password")
    if password == "rawan_0304":
        st.success("ברוכה הבאה, מנהלת!")
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            st.dataframe(df)
            csv_data = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 הורד את כל התשובות כ-CSV",
                data=csv_data,
                file_name="mapping_data.csv",
                mime="text/csv"
            )
        else:
            st.info("אין עדיין נתונים להצגה.")
    elif password != "":
        st.error("סיסמה שגויה ❌")
