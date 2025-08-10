import streamlit as st
import pandas as pd
import base64
import requests

# פרטי ההתחברות ל-GitHub
GITHUB_TOKEN = "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"
REPO_OWNER = "1not2me"  # שם המשתמש שלך ב-GitHub
REPO_NAME = "mepoy-madre5im"  # שם הריפו
FILE_PATH = "mapping_data.csv"  # שם הקובץ בדיוק כמו שהוא בריפו
BRANCH = "main"

# טופס ב-Streamlit
st.title("📋 טופס שמירה ל-GitHub")
name = st.text_input("שם")
age = st.number_input("גיל", min_value=0, max_value=120, step=1)

if st.button("📤 שלח ושמור"):
    # שליפת תוכן קובץ קיים מ-GitHub
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_data = response.json()
        content = base64.b64decode(file_data["content"]).decode()
        df = pd.read_csv(pd.compat.StringIO(content))
    else:
        df = pd.DataFrame(columns=["שם", "גיל"])

    # הוספת שורה חדשה
    new_row = pd.DataFrame([[name, age]], columns=["שם", "גיל"])
    df = pd.concat([df, new_row], ignore_index=True)

    # המרה לבסיס64 לפני שמירה
    csv_content = df.to_csv(index=False)
    b64_content = base64.b64encode(csv_content.encode()).decode()

    # שמירה חזרה ל-GitHub
    data = {
        "message": "עדכון mapping_data.csv מהטופס",
        "content": b64_content,
        "branch": BRANCH
    }

    if response.status_code == 200:
        data["sha"] = file_data["sha"]  # כדי לעדכן קובץ קיים

    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        st.success("✅ הנתונים נשמרו בהצלחה ב-GitHub!")
    else:
        st.error(f"שגיאה בשמירה: {put_response.status_code}")
