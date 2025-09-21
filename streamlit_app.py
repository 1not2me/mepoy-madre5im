# streamlit_app.py
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from io import BytesIO
from datetime import datetime
import re

import streamlit as st
import pandas as pd

# ===== הגדרות קבועות =====
st.set_page_config(page_title="מיפוי מדריכים לשיבוץ סטודנטים - תשפ\"ו", layout="centered")
ADMIN_PASSWORD = "rawan_0304"

DATA_DIR   = Path("data")
BACKUP_DIR = DATA_DIR / "backups"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE      = DATA_DIR / "שאלון_שיבוץ.csv"         # קובץ ראשי (מצטבר, לעולם לא מתאפס)
CSV_LOG_FILE  = DATA_DIR / "שאלון_שיבוץ_log.csv"     # יומן הוספות (Append-Only)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "rawan_0304")  # מומלץ לשים ב-secrets

# ספריית נתונים + קבצים
DATA_DIR = Path("data")
BACKUP_DIR = DATA_DIR / "backups"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILE = DATA_DIR / "mapping_data.csv"          # קובץ ראשי (נשמר ומעודכן)
CSV_LOG_FILE = DATA_DIR / "mapping_data_log.csv"  # קובץ יומן הוספות (Append-Only)
SITES_FILE = DATA_DIR / "sites_catalog.csv"       # אופציונלי: קטלוג מוסדות/תחומים

# ===== רשימת תחומי התמחות (ניתן לעדכן בהתאם לשאלון הסטודנטים) =====
SPECIALIZATIONS = [
    "מערכות מידע רפואיות", "בריאות דיגיטלית", "רווחה", "חינוך", "קהילה",
    "סיעוד", "פסיכולוגיה קהילתית", "מנהל מערכות מידע", "ניתוח נתונים", "סיוע טכנולוגי",
    "אחר"
]

# ===== סדר עמודות רצוי (כולל תאריך) =====
COLUMNS_ORDER = [
    "תאריך",
    "שם פרטי",
    "שם משפחה",
    "סטטוס מדריך",
    "מוסד",
    "תחום התמחות",
    "רחוב",
    "עיר",
    "מיקוד",
    "מספר סטודנטים שניתן לקלוט (1 או 2)",
    "מעוניין להמשיך",
    "בקשות מיוחדות",
    "טלפון",
    "אימייל",
]

def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    known = [c for c in COLUMNS_ORDER if c in df.columns]
    extra = [c for c in df.columns if c not in known]
    return df[known + extra]

# ===== עיצוב =====
st.markdown("""
<style>
:root{
  --ink:#0f172a; 
  --muted:#475569; 
  --ring:rgba(99,102,241,.25); 
  --card:rgba(255,255,255,.85);
}
html, body, [class*="css"] { font-family: system-ui, "Segoe UI", Arial; }
.stApp, .main, [data-testid="stSidebar"]{ direction:rtl; text-align:right; }
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(1200px 600px at 8% 8%, #e0f7fa 0%, transparent 65%),
    radial-gradient(1000px 500px at 92% 12%, #ede7f6 0%, transparent 60%),
    radial-gradient(900px 500px at 20% 90%, #fff3e0 0%, transparent 55%);
}
.block-container{ padding-top:1.1rem; }
[data-testid="stForm"]{
  background:var(--card);
  border:1px solid #e2e8f0;
  border-radius:16px;
  padding:18px 20px;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
}
[data-testid="stWidgetLabel"] p{ text-align:right; margin-bottom:.25rem; color:var(--muted); }
[data-testid="stWidgetLabel"] p::after{ content: " :"; }
input, textarea, select{ direction:rtl; text-align:right; }
</style>
""", unsafe_allow_html=True)

# ===== פונקציות עזר לקבצים =====
def load_csv_safely(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            try:
                return pd.read_csv(path, encoding="utf-8-sig")
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()

def save_master_dataframe(df: pd.DataFrame) -> None:
    df = reorder_columns(df.copy())
    temp_path = CSV_FILE.with_suffix(".tmp.csv")
    df.to_csv(temp_path, index=False, encoding="utf-8-sig")
    temp_path.replace(CSV_FILE)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"mapping_data_{ts}.csv"
    df.to_csv(backup_path, index=False, encoding="utf-8-sig")

def append_to_log(row_df: pd.DataFrame) -> None:
    row_df = reorder_columns(row_df.copy())
    file_exists = CSV_LOG_FILE.exists()
    row_df.to_csv(
        CSV_LOG_FILE,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig"
    )

def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    df = reorder_columns(df.copy())
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]
        for i, col in enumerate(df.columns):
            width = min(60, max(12, int(df[col].astype(str).map(len).max() if not df.empty else 12) + 4))
            ws.set_column(i, i, width)
    bio.seek(0)
    return bio.read()

# ===== קריאת קטלוג מוסדות/תחומים (אופציונלי) =====
def load_sites_catalog() -> pd.DataFrame:
    if not SITES_FILE.exists():
        return pd.DataFrame()
    df = load_csv_safely(SITES_FILE)
    if df.empty:
        st.warning("⚠ קובץ הקטלוג קיים אך ריק.")
        return pd.DataFrame()

    cols = {c.strip(): c for c in df.columns}
    def pick(*options):
        for opt in options:
            if opt in cols:
                return cols[opt]
        return None

    col_institute = pick('מוסד', 'שם מוסד', 'שם מוסד/שירות ההכשרה', 'Institution')
    col_spec      = pick('תחום התמחות', 'תחום', 'התמחות', 'Specialization')

    if not col_institute or not col_spec:
        st.warning("⚠ בקטלוג חסרות עמודות חובה: 'מוסד' ו'תחום התמחות'. הטופס יעבוד במצב קלט חופשי.")
        return pd.DataFrame()

    clean = (
        df[[col_institute, col_spec]]
        .rename(columns={col_institute: 'מוסד', col_spec: 'תחום התמחות'})
        .dropna().drop_duplicates().reset_index(drop=True)
    )
    for c in ['מוסד', 'תחום התמחות']:
        clean[c] = clean[c].astype(str).str.strip()
    return clean

sites_df = load_sites_catalog()
sites_available = not sites_df.empty
known_specs = sorted(sites_df['תחום התמחות'].dropna().unique().tolist()) if sites_available else SPECIALIZATIONS[:]
known_institutions = sorted(sites_df['מוסד'].dropna().unique().tolist()) if sites_available else []

# ===== בדיקת מצב מנהל =====
try:
    params = st.query_params
    admin_flag = params.get("admin", ["0"])[0]
except Exception:
    admin_flag = "0"
is_admin_mode = (admin_flag == "1")
