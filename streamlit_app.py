import streamlit as st
import pandas as pd
from datetime import datetime

# כותרת הדף
st.title("📋 טופס מיפוי מדריכים")

# יצירת טופס
with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    full_name = st.text_input("שם מלא")
    id_number = st.text_input("תעודת זהות")
    city = st.text_input("יישוב מגורים")
    distance = st.number_input("מרחק ממקום ההכשרה (בק\"מ)", min_value=0.0, step=10)

    st.subheader("ניסיון והעדפות")
    worked_before = st.radio("האם עבדת כבר במקום זה בעבר?", ["כן", "לא"])
    partner_preference = st.text_input("שם בן/בת זוג מועדף לשיבוץ (אם יש)")
    preferred_area = st.selectbox("אזור מועדף", ["צפון", "מרכז", "דרום", "אין העדפה"])

    st.subheader("הערות נוספות")
    notes = st.text_area("הערות")

    # כפתור שליחה
    submit_btn = st.form_submit_button("שלח")

# שמירת הנתונים אם נשלח
if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם מלא": [full_name],
        "תעודת זהות": [id_number],
        "יישוב": [city],
        "מרחק": [distance],
        "עבד בעבר": [worked_before],
        "בן/בת זוג לשיבוץ": [partner_preference],
        "אזור מועדף": [preferred_area],
        "הערות": [notes]
    }

    df = pd.DataFrame(data)

    try:
        # אם הקובץ קיים - הוספה אליו
        existing_df = pd.read_csv("mapping_data.csv")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_csv("mapping_data.csv", index=False)
    except FileNotFoundError:
        # אם הקובץ לא קיים - יצירה חדשה
        df.to_csv("mapping_data.csv", index=False)

    st.success("✅ הנתונים נשמרו בהצלחה!")

    # הצגת טבלה למילוי האחרון
    st.write("**הנתונים שהוזנו:**")
    st.dataframe(df)
