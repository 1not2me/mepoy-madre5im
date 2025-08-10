import streamlit as st
import pandas as pd
from datetime import datetime
from github import Github
import io

# הגדרות GitHub
GITHUB_TOKEN = "הכניסי_כאן_את_הטוקן_שלך"
GITHUB_REPO = "המשתמש_שלך/mapping-data"  # למשל: rawansaab/mapping-data
CSV_FILE_PATH = "mapping_data.csv"

st.title("📋 טופס מיפוי מדריכים")

with st.form("mapping_form"):
    st.subheader("פרטים אישיים")
    full_name = st.text_input("שם מלא")
    institute = st.text_input("מוסד/שירות ההכשרה")
    specialization = st.text_input("תחום ההתמחות")
    address = st.text_input("כתובת מדויקת של מקום ההכשרה")
    city = st.text_input("עיר")
    zip_code = st.text_input("מיקוד")
    num_students = st.number_input("מספר סטודנטים שניתן לקלוט השנה", min_value=0, step=1)
    continue_teaching = st.radio("האם מעוניין/ת להמשיך להדריך השנה", ["כן", "לא"])
    phone = st.text_input("טלפון")
    email = st.text_input("כתובת אימייל")

    submit_btn = st.form_submit_button("שלח")

if submit_btn:
    data = {
        "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "שם מלא": [full_name],
        "מוסד/שירות": [institute],
        "תחום התמחות": [specialization],
        "כתובת": [address],
        "עיר": [city],
        "מיקוד": [zip_code],
        "מספר סטודנטים": [num_students],
        "ממשיך להדריך": [continue_teaching],
        "טלפון": [phone],
        "אימייל": [email]
    }

    df = pd.DataFrame(data)

    # התחברות ל-GitHub
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    try:
        # קריאת הקובץ הקיים מה-Repo
        contents = repo.get_contents(CSV_FILE_PATH)
        existing_df = pd.read_csv(io.BytesIO(contents.decoded_content))
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        csv_bytes = updated_df.to_csv(index=False).encode()
        repo.update_file(CSV_FILE_PATH, "עדכון טופס", csv_bytes, contents.sha)
    except:
        # אם אין קובץ קיים, יוצרים חדש
        csv_bytes = df.to_csv(index=False).encode()
        repo.create_file(CSV_FILE_PATH, "יצירת קובץ ראשון", csv_bytes)

    st.success("✅ הנתונים נשמרו ב-GitHub בהצלחה!")
