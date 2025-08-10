import streamlit as st
import pandas as pd
from datetime import datetime
import os
from urllib.parse import urlparse, parse_qs

st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים", layout="centered")

# קריאת פרמטרים מה-URL
query_params = st.query_params
is_admin = query_params.get("admin", ["0"])[0] == "1"

# ------------------ מצב מילוי טופס ------------------
if not is_admin:
    st.title("📋 מיפוי מדריכים לשיבוץ סטודנטים")
    with st.form("mapping_form"):
        last_name = st.text_input(":שם משפחה *")
        first_name = st.text_input(":שם פרטי *")
        field = st.text_input(":תחום התמחות *")
        city = st.text_input(":עיר *")
        submit_btn = st.form_submit_button("שלח/י")

    if submit_btn:
        if not last_name or not first_name or not field or not city:
            st.error("❌ יש למלא את כל השדות החיוניים")
        else:
            data = {
                "תאריך": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "שם משפחה": [last_name],
                "שם פרטי": [first_name],
                "תחום התמחות": [field],
                "עיר": [city]
            }
            df = pd.DataFrame(data)
            if os.path.exists("mapping_data.csv") and os.path.getsize("mapping_data.csv") > 0:
                existing_df = pd.read_csv("mapping_data.csv")
                pd.concat([existing_df, df], ignore_index=True).to_csv("mapping_data.csv", index=False)
            else:
                df.to_csv("mapping_data.csv", index=False)
            st.success("✅ הנתונים נשמרו בהצלחה!")

# ------------------ מצב ניהול ------------------
else:
    st.subheader("📄 נתוני הטופס (ניהול)")
    password = st.text_input("הכנס סיסמת מנהל", type="password")
    if password == "rawan_0304":
        if os.path.exists("mapping_data.csv") and os.path.getsize("mapping_data.csv") > 0:
            all_data = pd.read_csv("mapping_data.csv")
            st.dataframe(all_data)
            csv = all_data.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ הורד קובץ CSV", csv, "mapping_data.csv", "text/csv")
        else:
            st.info("אין נתונים להצגה.")
    elif password:
        st.error("סיסמה שגויה.")
