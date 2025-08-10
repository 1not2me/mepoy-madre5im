import streamlit as st
import pandas as pd
from github import Github
from datetime import datetime
import io

# ------------------------------
# הגדרות GitHub
# ------------------------------
GITHUB_TOKEN = "הכניסי_כאן_את_הטוקן_שלך"
REPO_NAME = "1not2me/mepoy-madre5im"
CSV_FILE = "mapping_data.csv"

# ------------------------------
# התחברות ל-GitHub
# ------------------------------
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# ------------------------------
# פונקציה לקריאת הנתונים הקיימים
# ------------------------------
def load_csv_from_github():
    try:
        file_content = repo.get_contents(CSV_FILE)
        df = pd.read_csv(io.BytesIO(file_content.decoded_content))
        return df
    except:
        return pd.DataFrame(columns=["שם מלא", "שם משפחה", "שם פרטי", "מוסד/שירות", "תחום התמחות", "רחוב", "עיר", "תאריך"])

# ------------------------------
# פונקציה לשמירת הנתונים
# ------------------------------
def save_csv_to_github(df):
    csv_bytes = df.to_csv(index=False).encode()
    try:
        file = repo.get_contents(CSV_FILE)
        repo.update_file(CSV_FILE, "עדכון נתונים", csv_bytes, file.sha)
    except:
        repo.create_file(CSV_FILE, "קובץ חדש עם נתונים", csv_bytes)

# ------------------------------
# טופס הקליטה
# ------------------------------
st.title("📝 מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה")

with st.form("form"):
    full_name = st.text_input("שם מלא של המדריך/ה")
    last_name = st.text_input("שם משפחה")
    first_name = st.text_input("שם פרטי")
    institution = st.text_input("מוסד / שירות ההכשרה")
    field = st.selectbox("תחום התמחות", ["חינוך", "בריאות", "חברתי", "אחר"])
    street = st.text_input("רחוב")
    city = st.text_input("עיר")

    submitted = st.form_submit_button("שלח")

if submitted:
    df = load_csv_from_github()
    new_row = {
        "שם מלא": full_name,
        "שם משפחה": last_name,
        "שם פרטי": first_name,
        "מוסד/שירות": institution,
        "תחום התמחות": field,
        "רחוב": street,
        "עיר": city,
        "תאריך": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv_to_github(df)
    st.success("✅ הנתונים נשמרו בהצלחה ב־GitHub שלך!")
