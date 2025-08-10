import base64
import requests
from datetime import datetime

# ===== הגדרות GitHub =====
GITHUB_TOKEN = "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"
REPO_OWNER = "1not2me"
REPO_NAME = "mepoy-madre5im"
FILE_PATH = "mapping_data.csv"

def update_github_csv(new_row):
    """מעדכן את הקובץ mapping_data.csv ב-GitHub עם שורה חדשה"""
    # שלב 1: קבלת תוכן קיים
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    file_data = r.json()
    
    sha = file_data["sha"]
    content = base64.b64decode(file_data["content"]).decode("utf-8")

    # שלב 2: הוספת שורה חדשה
    content += "\n" + ",".join(new_row)

    # שלב 3: המרת התוכן ל-base64
    updated_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # שלב 4: עדכון הקובץ בגיטהאב
    data = {
        "message": f"Update {FILE_PATH} - {datetime.now().isoformat()}",
        "content": updated_content,
        "sha": sha
    }
    put_r = requests.put(url, headers=headers, json=data)
    put_r.raise_for_status()
    print("✅ הקובץ עודכן בהצלחה ב-GitHub")

# ===== דוגמה לשמירת נתונים מהטופס =====
# אחרי שהמשתמש ממלא טופס ב-Streamlit:
if st.button("שלח"):
    name = st.text_input("שם")
    email = st.text_input("אימייל")
    answer = st.text_area("תשובה")

    # אם המשתמש לחץ שלח – נוסיף את השורה ל-GitHub
    if name and email and answer:
        update_github_csv([name, email, answer])
        st.success("הנתונים נשמרו בהצלחה ב-GitHub!")
