import streamlit as st
import pandas as pd
from github import Github
import io

# ===== הגדרות GitHub =====
GITHUB_TOKEN = "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"
REPO_NAME = "1not2me/mepoy-madre5im"  # שם המשתמש/שם הריפו
FILE_PATH = "mapping_data.csv"        # הנתיב לקובץ בריפו

# התחברות ל־GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# פונקציה לקריאת הקובץ הקיים
def load_data():
    try:
        file_content = repo.get_contents(FILE_PATH)
        data = file_content.decoded_content.decode()
        return pd.read_csv(io.StringIO(data))
    except:
        return pd.DataFrame(columns=["שם משפחה", "שם פרטי", "מוסד / שירות ההכשרה", "תחום ההתמחות", "כתובת", "מספר סטודנטים", "טלפון", "אימייל"])

# פונקציה לשמירת נתונים ל־GitHub
def save_data(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    try:
        file = repo.get_contents(FILE_PATH)
        repo.update_file(FILE_PATH, "עדכון טופס", csv_buffer.getvalue(), file.sha)
    except:
        repo.create_file(FILE_PATH, "יצירת טופס", csv_buffer.getvalue())

# ===== עיצוב הטופס =====
st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו")
st.write("אנא מלא/י את כל השדות. המידע ישמש לתכנון השיבוץ בלבד.")

with st.form("form"):
    last_name = st.text_input("שם משפחה*")
    first_name = st.text_input("שם פרטי*")
    institution = st.text_input("מוסד / שירות ההכשרה*")
    specialty = st.text_input("תחום ההתמחות*")
    address = st.text_input("כתובת מלאה*")
    students_num = st.number_input("מספר סטודנטים שניתן לקלוט השנה*", min_value=0)
    phone = st.text_input("טלפון*")
    email = st.text_input("אימייל*")
    submitted = st.form_submit_button("שלח")

if submitted:
    df = load_data()
    df.loc[len(df)] = [last_name, first_name, institution, specialty, address, students_num, phone, email]
    save_data(df)
    st.success("✅ הטופס נשלח בהצלחה ונשמר ב־GitHub!")

# ===== למנהל בלבד - הצגת הנתונים =====
password = st.sidebar.text_input("סיסמת מנהל", type="password")
if password == "rawan_0304":
    st.sidebar.success("ברוכה הבאה מנהלת!")
    data = load_data()
    st.write("📊 כל הנתונים שנשמרו:")
    st.dataframe(data)
    st.download_button("⬇ הורד CSV", data.to_csv(index=False), file_name="mapping_data.csv", mime="text/csv")
