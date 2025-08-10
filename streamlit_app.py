import streamlit as st
import pandas as pd
from github import Github
from io import StringIO

# ===== הגדרות GitHub =====
GITHUB_TOKEN = "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"
REPO_NAME = "1not2me/mepoy-madre5im"
FILE_PATH = "mapping_data.csv"

# ===== פונקציה לעדכון CSV ב-GitHub =====
def update_github_csv(new_row):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    try:
        file_content = repo.get_contents(FILE_PATH)
        data = file_content.decoded_content.decode()
        df = pd.read_csv(StringIO(data))
    except Exception:
        df = pd.DataFrame(columns=["Name", "Email", "Answer"])

    # הוספת השורה החדשה
    df.loc[len(df)] = new_row

    # המרה ל-CSV והעלאה לגיטהאב
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    repo.update_file(FILE_PATH, "Update mapping_data.csv", csv_buffer.getvalue(), file_content.sha if 'file_content' in locals() else None)

# ===== טופס בדיקה =====
st.title("טופס בדיקה לשמירה ב-GitHub")

name = st.text_input("שם")
email = st.text_input("אימייל")
answer = st.text_area("תשובה")

if st.button("שלח ל-GitHub"):
    if name and email and answer:
        update_github_csv([name, email, answer])
        st.success("✅ הנתונים נשמרו בהצלחה ל-GitHub!")
    else:
        st.error("❌ יש למלא את כל השדות")
