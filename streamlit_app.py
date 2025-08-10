import streamlit as st
import pandas as pd
import base64
import requests
import os

# ה־token מאוחסן ב־secret
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = "1not2me"
REPO_NAME = "mepoy-madre5im"
FILE_PATH = "mapping_data.csv"

def update_github_csv(new_data):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    # קריאת הקובץ הקיים
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        df = pd.read_csv(pd.compat.StringIO(content))
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data

    # שמירת הקובץ חזרה ל־GitHub
    content_bytes = df.to_csv(index=False).encode()
    content_b64 = base64.b64encode(content_bytes).decode()

    data = {
        "message": "עדכון נתונים מהטופס",
        "content": content_b64,
        "sha": r.json().get("sha") if r.status_code == 200 else None
    }
    requests.put(url, headers=headers, json=data)

# טופס פשוט לדוגמה
st.title("📋 טופס לדוגמה")
name = st.text_input("שם")
email = st.text_input("אימייל")
if st.button("שמור"):
    if name and email:
        df_new = pd.DataFrame([{"שם": name, "אימייל": email}])
        update_github_csv(df_new)
        st.success("✅ הנתונים נשמרו ב־GitHub!")
    else:
        st.error("❌ יש למלא את כל השדות")
