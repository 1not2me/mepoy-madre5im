import streamlit as st
import pandas as pd
from github import Github
from io import StringIO

# פרטי גישה לגיטהאב
GITHUB_TOKEN = "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"
REPO_NAME = "1not2me/mepoy-madre5im"
FILE_PATH = "mapping_data.csv"

# פונקציה לשמירת הנתונים בגיטהאב
def save_to_github(new_data):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    try:
        contents = repo.get_contents(FILE_PATH)
        # אם קובץ כבר קיים – מוסיפים אליו
        existing_data = pd.read_csv(StringIO(contents.decoded_content.decode()))
        updated_data = pd.concat([existing_data, pd.DataFrame([new_data])], ignore_index=True)
        csv_content = updated_data.to_csv(index=False)
        repo.update_file(FILE_PATH, "עדכון נתונים", csv_content, contents.sha)
    except:
        # אם הקובץ לא קיים – יוצרים חדש
        df = pd.DataFrame([new_data])
        csv_content = df.to_csv(index=False)
        repo.create_file(FILE_PATH, "יצירת קובץ נתונים", csv_content)

# טופס
st.title("מיפוי מדריכים לשיבוץ סטודנטים - שנת הכשרה תשפ\"ו")
st.write("אנא מלא/י את כל השדות בצורה מדויקת.")

full_name = st.text_input("שם מלא של המדריך/ה")
institution = st.text_input("מוסד / שירות ההכשרה")
specialization = st.text_input("תחום ההתמחות")
address = st.text_input("כתובת מדויקת של מקום ההכשרה")
students_number = st.number_input("מספר סטודנטים שניתן לקלוט השנה", min_value=0, step=1)
continue_training = st.selectbox("האם מעוניין/ת להמשיך להדריך השנה?", ["כן", "לא"])
phone = st.text_input("טלפון")
email = st.text_input("כתובת אימייל")

if st.button("שלח"):
    data = {
        "שם מלא": full_name,
        "מוסד / שירות ההכשרה": institution,
        "תחום ההתמחות": specialization,
        "כתובת": address,
        "מספר סטודנטים": students_number,
        "ממשיך השנה": continue_training,
        "טלפון": phone,
        "אימייל": email
    }
    save_to_github(data)
    st.success("הטופס נשלח בהצלחה! הנתונים נשמרו ב-GitHub.")
