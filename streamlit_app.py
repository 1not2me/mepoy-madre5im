# streamlit_app.py
# ---------------------------------------------------------
# שיבוץ סטודנטים לפי "מי-מתאים-ל" עם מרחק:
# 1) student_form_example_5.csv     (סטודנטים)
# 2) example_assignment_result_5.csv (אתרים/מדריכים)
# ניקוד: תחום (חפיפה/הכלה) + עיר (נירמול) + מרחק (קירבה) + קיבולת
# כולל מדריך שימוש באתר ועיצוב RTL בסגנון המבוקש
# ---------------------------------------------------------

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from io import BytesIO
import re, time, math

# ========= Geopy (לגיאוקוד) =========
try:
    from geopy.geocoders import Nominatim
    GEOPY_OK = True
except Exception:
    GEOPY_OK = False

# =========================
# הגדרות כלליות + עיצוב
# =========================
st.set_page_config(page_title="שיבוץ סטודנטים – מי-מתאים-ל", layout="wide")

st.markdown("""
<style>
:root{
  --ink:#0f172a; 
  --muted:#475569; 
  --ring:rgba(99,102,241,.25); 
  --card:rgba(255,255,255,.85);
  --border:#e2e8f0;
}

/* RTL + פונטים */
html, body, [class*="css"] { font-family: system-ui, "Segoe UI", Arial; }
.stApp, .main, [data-testid="stSidebar"]{ direction:rtl; text-align:right; }

/* רקע */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(1200px 600px at 8% 8%, #e0f7fa 0%, transparent 65%),
    radial-gradient(1000px 500px at 92% 12%, #ede7f6 0%, transparent 60%),
    radial-gradient(900px 500px at 20% 90%, #fff3e0 0%, transparent 55%);
}
.block-container{ padding-top:1.1rem; }

/* כרטיסים */
.card{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:18px 20px; box-shadow:0 8px 24px rgba(2,6,23,.06); }
.hero{
  background:linear-gradient(180deg, rgba(255,255,255,.96), rgba(255,255,255,.9));
  border:1px solid var(--border); border-radius:18px; padding:22px 20px; box-shadow:0 8px 28px rgba(2,6,23,.06);
}
.hero h1{ margin:0 0 6px 0; color:var(--ink); font-size:28px; }
.hero p{ margin:0; color:var(--muted); }

/* מסגרת לטופס */
[data-testid="stForm"], .boxed{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:16px;
  padding:18px 20px;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
}

/* תוויות + נקודתיים מימין */
[data-testid="stWidgetLabel"] p{ text-align:right; margin-bottom:.25rem; color:var(--muted); }
[data-testid="stWidgetLabel"] p::after{ content: " :"; }

/* שדות */
input, textarea, select{ direction:rtl; text-align:right; }

/* KPIs */
.metric{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 12px; border:1px solid var(--border); border-radius:14px; background:#fff;
}
.metric .label{ color:var(--muted); font-size:.9rem; }
.metric .value{ color:var(--ink); font-weight:700; }

hr{ border-color:var(--border); }
.small{ color:#64748b; font-size:.92rem; }
</style>
""", unsafe_allow_html=True)

# =========================
# קבועים ושמות קבצים
# =========================
DEFAULT_STUDENTS = Path("./student_form_example_5.csv")
DEFAULT_SITES    = Path("./example_assignment_result_5.csv")
DEFAULT_ASSIGN   = Path("./assignments.csv")
GEOCODE_CACHE    = Path("./geocode_cache.csv")   # קאש כתובת/עיר -> קואורדינטות

# =========================
# פונקציות עזר – קריאה/נירמול/פיצול/מרחק
# =========================
def read_csv_flex(path_or_upload):
    if path_or_upload is None: return None
    try:
        return pd.read_csv(path_or_upload)
    except Exception:
        try:
            if hasattr(path_or_upload, "seek"): path_or_upload.seek(0)
            return pd.read_csv(path_or_upload, encoding="utf-8-sig")
        except Exception:
            return None

def _strip(x): 
    return "" if pd.isna(x) else str(x).strip()

def _lc(x): 
    return _strip(x).lower()

_PUNCT_RE = re.compile(r"[\"'`”“׳״\.\!\?\:\;\|\·•\u2022\(\)\[\]\{\}]+")
_WS_RE    = re.compile(r"\s+")
def normalize_text(s: str) -> str:
    s = _strip(s)
    s = _PUNCT_RE.sub(" ", s)
    s = s.replace("-", " ").replace("–", " ").replace("—", " ").replace("/", " ")
    s = _WS_RE.sub(" ", s).strip()
    return s.lower()

def split_multi(raw) -> set:
    if pd.isna(raw): return set()
    s = str(raw).replace("\n", ",")
    s = re.sub(r"[;/|•·•]", ",", s)
    s = s.replace("–", ",").replace("—", ",").replace("/", ",")
    if "," not in s: s = re.sub(r"\s{2,}", ",", s)
    items = [normalize_text(p) for p in s.split(",") if normalize_text(p)]
    return set(items)

def overlap_count(set_a: set, set_b: set) -> int:
    cnt = 0
    for a in set_a:
        for b in set_b:
            if not a or not b: 
                continue
            if a == b: cnt += 1
            else:
                if (len(a) >= 3 and a in b) or (len(b) >= 3 and b in a): cnt += 1
    return cnt

def bytes_for_download(df, filename):
    bio = BytesIO(); df.to_csv(bio, index=False, encoding="utf-8-sig"); bio.seek(0); return bio, filename

def haversine_km(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]: return None
    try:
        R = 6371.0
        p1 = math.radians(lat1); p2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except Exception:
        return None

# ---- קאש גיאוקוד ----
def load_geocode_cache():
    if GEOCODE_CACHE.exists():
        try:
            df = pd.read_csv(GEOCODE_CACHE)
            return {row["query"]: (row["lat"], row["lon"]) for _, row in df.iterrows()}
        except Exception:
            return {}
    return {}

def save_geocode_cache(cache_dict):
    try:
        df = pd.DataFrame([{"query": k, "lat": v[0], "lon": v[1]} for k, v in cache_dict.items()])
        df.to_csv(GEOCODE_CACHE, index=False, encoding="utf-8-sig")
    except Exception:
        pass

@st.cache_data(show_spinner=False)
def geocode_query(query):
    if not GEOPY_OK: return None
    geolocator = Nominatim(user_agent="student-placement-app")
    time.sleep(1.0)  # נימוס ל-OSM
    try:
        loc = geolocator.geocode(query)
        if loc: return (loc.latitude, loc.longitude)
    except Exception:
        return None
    return None

def geocode_many(queries, country_hint="ישראל"):
    cache = load_geocode_cache()
    out = {}
    for q in queries:
        if not q: out[q] = (None, None); continue
        q_norm = f"{q}, {country_hint}" if country_hint and country_hint not in q else q
        if q_norm in cache: out[q] = cache[q_norm]; continue
        res = geocode_query(q_norm)
        if res is None: out[q] = (None, None)
        else:
            out[q] = (float(res[0]), float(res[1]))
            cache[q_norm] = out[q]
    save_geocode_cache(cache)
    return out

# =========================
# משקולות ניקוד
# =========================
W_DOMAIN_MAIN  = 2.0   # תחום מועדף ↔ תחום ההתמחות
W_DOMAIN_MULTI = 1.0   # חפיפה/הכלה לכל ערך נוסף
W_CITY         = 1.2   # עיר (נירמול)
DEFAULT_W_DISTANCE = 1.8   # משקל קירבה
DEFAULT_MAX_KM     = 60    # טווח קירבה אפקטיבי

# =========================
# Sidebar – העלאות + מרחק
# =========================
with st.sidebar:
    st.header("העלאת נתונים")
    st.caption("אם לא תעלי קובץ – נטען מהתיקייה בשמות הדיפולטיים.")
    up_students = st.file_uploader("סטודנטים – student_form_example_5.csv", type=["csv"])
    up_sites    = st.file_uploader("אתרים/מדריכים – example_assignment_result_5.csv", type=["csv"])

    st.divider()
    st.subheader("מרחק (קירבה)")
    use_distance   = st.checkbox("שקלול מרחק בציון", value=True)
    hard_limit_on  = st.checkbox("אל תשבץ מעבר לטווח מקסימלי", value=True)
    max_km         = st.slider("טווח מקסימלי (ק\"מ)", 10, 200, DEFAULT_MAX_KM, 5)
    w_distance     = st.slider("משקל המרחק (ככל שקרוב יותר = ציון גבוה יותר)", 0.0, 5.0, DEFAULT_W_DISTANCE, 0.1)
    st.caption("אם אין Lat/Lon – נבצע גיאוקוד לפי עיר/כתובת (OSM) עם קאש מקומי.")

# קריאה
students_raw = read_csv_flex(up_students) if up_students else (read_csv_flex(DEFAULT_STUDENTS) if DEFAULT_STUDENTS.exists() else None)
sites_raw    = read_csv_flex(up_sites)    if up_sites    else (read_csv_flex(DEFAULT_SITES)    if DEFAULT_SITES.exists()    else None)

# =========================
# Hero + סטטוס
# =========================
st.markdown(
    """
<div class="hero">
  <h1>📅 שיבוץ סטודנטים – מי-מתאים-ל</h1>
  <p>הציון מחושב לפי <b>תחום</b> + <b>עיר</b> + <b>מרחק</b> (אם הופעל), ואז מתבצע שיבוץ לפי <b>קיבולת</b> לכל מוסד.</p>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([1.25, 1])
with c1:
    st.markdown("### שלבים בקצרה")
    st.markdown("- העלאת שני הקבצים (או טעינה אוטומטית).")
    st.markdown("- בדיקה מהירה בטאב **📥 נתונים**.")
    st.markdown("- **הרצת שיבוץ** בטאב **🧩 שיבוץ**.")
    st.markdown("- **הורדה/שמירה** בטאב **📤 ייצוא**.")
with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric"><span class="label">סטודנטים</span><span class="value">{0 if students_raw is None else len(students_raw)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric"><span class="label">אתרים</span><span class="value">{0 if sites_raw is None else len(sites_raw)}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# =========================
# Tabs
# =========================
tab_guide, tab_data, tab_match, tab_export = st.tabs(["📖 מדריך", "📥 נתונים", "🧩 שיבוץ", "📤 ייצוא"])

# =========================
# מדריך
# =========================
with tab_guide:
    st.subheader("מדריך מלא")
    st.markdown(f"""
**מטרה**  
שיבוץ אוטומטי של סטודנטים/ות למוסדות הכשרה לפי **תחום**, **עיר**, ו**מרחק בפועל** בין עיר הסטודנט/ית לכתובת/עיר המוסד.  
דוגמה: *\"רואן סעב – אבו סנאן\"* לעומת *\"תל אביב\"* – המרחק גדול ולכן האתר יקבל ציון נמוך/ייפסל אם הופעל כלל המרחק.

### קבצים נדרשים
- `student_form_example_5.csv` → עמודות: `שם פרטי`, `שם משפחה`, `עיר מגורים`, `תחומים מבוקשים`, `תחום מועדף`.
- `example_assignment_result_5.csv` → עמודות: `מוסד / שירות הכשרה`, `תחום ההתמחות`, `עיר`, `מספר סטודנטים שניתן לקלוט השנה`.

### איך מחשבים?
1. **תחום מועדף ↔ תחום ההתמחות**: בסיס {W_DOMAIN_MAIN} + {W_DOMAIN_MULTI} לכל חפיפה/הכלה נוספת.  
2. **תחומים מבוקשים ↔ תחום ההתמחות**: {W_DOMAIN_MULTI} לכל חפיפה.  
3. **עיר ↔ עיר**: {W_CITY} (עם נירמול/הכלה).  
4. **מרחק** (אם הופעל):  
   `distance_score = w_distance * (1 - min(distance_km / max_km, 1))`  
   ואם מסומן **אל תשבץ מעבר לטווח** – זוגות שמעל {DEFAULT_MAX_KM} ק״מ *נפסלים מראש*.

### תוצאה
`student_id, student_name, assigned_site, assigned_city, assigned_distance_km, match_score, status`  
ניתן להוריד CSV או לשמור בשם הקבוע `assignments.csv`.
""")

# =========================
# נתונים
# =========================
with tab_data:
    st.info("המערכת משתמשת בעמודות: סטודנטים → `שם פרטי`, `שם משפחה`, `עיר מגורים`, `תחומים מבוקשים`, `תחום מועדף` • אתרים → `מוסד / שירות הכשרה`, `תחום ההתמחות`, `עיר`, `מספר סטודנטים שניתן לקלוט השנה`", icon="ℹ️")
    if students_raw is None or sites_raw is None:
        st.warning("יש להעלות/לספק את שני הקבצים.", icon="⚠️")
    else:
        cA, cB = st.columns(2)
        with cA: st.dataframe(students_raw, use_container_width=True, height=320)
        with cB: st.dataframe(sites_raw,    use_container_width=True, height=320)

# =========================
# שיבוץ (כולל מרחק)
# =========================
with tab_match:
    if students_raw is None or sites_raw is None:
        st.warning("חסרים נתונים. העלי את שני הקבצים.", icon="⚠️")
    else:
        # שמות עמודות
        STU_FIRST, STU_LAST, STU_CITY, STU_DOMS, STU_PREFDOM = "שם פרטי", "שם משפחה", "עיר מגורים", "תחומים מבוקשים", "תחום מועדף"
        SITE_NAME, SITE_CITY, SITE_DOMAIN, SITE_CAP = "מוסד / שירות הכשרה", "עיר", "תחום ההתמחות", "מספר סטודנטים שניתן לקלוט השנה"

        # בדיקות
        missing = []
        for req in [STU_FIRST, STU_LAST, STU_CITY, STU_DOMS, STU_PREFDOM]:
            if req not in students_raw.columns: missing.append(f"סטודנטים: {req}")
        for req in [SITE_NAME, SITE_CITY, SITE_DOMAIN, SITE_CAP]:
            if req not in sites_raw.columns: missing.append(f"אתרים: {req}")
        if missing: st.error("עמודות חסרות: " + " | ".join(missing)); st.stop()

        # --- סטודנטים
        stu = students_raw.copy()
        stu["student_id"] = [f"S{i+1:03d}" for i in range(len(stu))]
        stu["student_name"] = (stu[STU_FIRST].astype(str).fillna("") + " " + stu[STU_LAST].astype(str).fillna("")).str.strip()

        # זיהוי עמודות Lat/Lon אם קיימות
        def detect_latlon_cols(df):
            lat = next((c for c in df.columns if c.lower() in ["lat","latitude","קו רוחב","רוחב"]), None)
            lon = next((c for c in df.columns if c.lower() in ["lon","lng","longitude","קו אורך","אורך"]), None)
            return lat, lon
        stu_lat_col, stu_lon_col = detect_latlon_cols(stu)

        # --- אתרים
        site = sites_raw.copy()
        site["capacity"] = pd.to_numeric(site[SITE_CAP], errors="coerce").fillna(1).astype(int).clip(lower=0)
        site = site[site["capacity"] > 0]
        site_lat_col, site_lon_col = detect_latlon_cols(site)

        # איחוד תחומים וכבישת עיר לא ריקה
        def union_domains(series) -> str:
            acc = set()
            for v in series.dropna(): acc |= split_multi(v)
            return ", ".join(sorted(acc)) if acc else ""
        def first_non_empty(series) -> str:
            for v in series:
                if _strip(v): return v
            return ""
        sites_agg = site.groupby(SITE_NAME, as_index=False).agg({SITE_CITY: first_non_empty, SITE_DOMAIN: union_domains})
        site_capacity = site.groupby(SITE_NAME)["capacity"].sum().to_dict()
        site_city_map = pd.Series(sites_agg[SITE_CITY].values, index=sites_agg[SITE_NAME].astype(str)).to_dict()

        # --- קואורדינטות סטודנטים
        stu_coords = {}
        if stu_lat_col and stu_lon_col:
            for _, r in stu.iterrows():
                lat = pd.to_numeric(r[stu_lat_col], errors="coerce")
                lon = pd.to_numeric(r[stu_lon_col], errors="coerce")
                stu_coords[r["student_id"]] = (lat if pd.notna(lat) else None, lon if pd.notna(lon) else None)
        elif use_distance and GEOPY_OK:
            unique_cities = sorted(set(_strip(c) for c in stu[STU_CITY].fillna("").astype(str)))
            city_to_xy = geocode_many(unique_cities, country_hint="ישראל")
            for _, r in stu.iterrows():
                city = _strip(r[STU_CITY]); stu_coords[r["student_id"]] = city_to_xy.get(city, (None, None))
        else:
            for _, r in stu.iterrows(): stu_coords[r["student_id"]] = (None, None)

        # --- קואורדינטות אתרים
        site_coords = {}
        if site_lat_col and site_lon_col:
            for _, r in site.iterrows():
                sname = _strip(r[SITE_NAME])
                lat = pd.to_numeric(r[site_lat_col], errors="coerce")
                lon = pd.to_numeric(r[site_lon_col], errors="coerce")
                site_coords[sname] = (lat if pd.notna(lat) else None, lon if pd.notna(lon) else None)
        elif use_distance and GEOPY_OK:
            queries = []
            for _, r in sites_agg.iterrows():
                q = _strip(r[SITE_NAME]); city = _strip(r[SITE_CITY])
                queries.append(f"{q}, {city}" if city else q)
            q_to_xy = geocode_many(sorted(set(queries)), country_hint="ישראל")
            for _, r in sites_agg.iterrows():
                q = _strip(r[SITE_NAME]); city = _strip(r[SITE_CITY])
                site_coords[q] = q_to_xy.get(f"{q}, {city}" if city else q, (None, None))
        else:
            for _, r in sites_agg.iterrows():
                site_coords[_strip(r[SITE_NAME])] = (None, None)

        # --- ניקוד בסיס + בונוס מרחק
        def base_match_score(stu_row, site_row):
            score = 0.0
            pref_set = split_multi(stu_row.get(STU_PREFDOM, ""))
            dom_site = split_multi(site_row.get(SITE_DOMAIN, "")) or {normalize_text(site_row.get(SITE_DOMAIN, ""))}
            if pref_set and dom_site:
                c1 = overlap_count(pref_set, dom_site)
                if c1 > 0: score += W_DOMAIN_MAIN + W_DOMAIN_MULTI * max(0, c1-1)
            all_set = split_multi(stu_row.get(STU_DOMS, ""))
            if all_set and dom_site:
                c2 = overlap_count(all_set, dom_site)
                if c2 > 0: score += W_DOMAIN_MULTI * c2
            stu_city  = normalize_text(stu_row.get(STU_CITY, ""))
            site_city = normalize_text(site_row.get(SITE_CITY, ""))
            if stu_city and site_city and (stu_city == site_city or stu_city in site_city or site_city in stu_city):
                score += W_CITY
            return score

        def distance_info(stu_id, site_name):
            lat1, lon1 = stu_coords.get(stu_id, (None, None))
            lat2, lon2 = site_coords.get(site_name, (None, None))
            d = haversine_km(lat1, lon1, lat2, lon2)
            return None if d is None else float(d)

        def distance_bonus(dist_km):
            if (not use_distance) or dist_km is None: return 0.0
            proximity = max(0.0, 1.0 - min(dist_km / max_km, 1.0))
            return w_distance * proximity

        # --- ציונים לכל צמד (כולל מרחק) ---
        rows = []
        for _, srow in stu.iterrows():
            sid = srow["student_id"]; sname = srow["student_name"]
            for _, trow in sites_agg.iterrows():
                site_name = _strip(trow[SITE_NAME])
                base = base_match_score(srow, trow)
                dkm = distance_info(sid, site_name)
                if hard_limit_on and use_distance and (dkm is None or dkm > max_km):
                    # פוסל צמד רחוק מדי
                    total = -1e9
                else:
                    total = base + distance_bonus(dkm)
                rows.append((sid, sname, site_name, total, _strip(trow[SITE_CITY]), None if dkm is None else round(dkm,1)))
        scores = pd.DataFrame(rows, columns=["student_id","student_name","site_name","score","site_city","distance_km"])

        # דיאגנוסטיקה (כולל מרחק)
        st.markdown("##### Top-3 התאמות (כולל עיר ומרחק בק\"מ)")
        top3 = scores.sort_values(["student_id","score"], ascending=[True, False]).groupby("student_id").head(3)
        st.dataframe(top3, use_container_width=True, height=320)

        # --- שיבוץ Greedy עם קיבולת ---
        assignments, cap_left = [], site_capacity.copy()
        for sid, grp in scores.groupby("student_id"):
            grp = grp.sort_values("score", ascending=False)
            chosen, chosen_score, sname = "ללא שיבוץ", 0.0, grp.iloc[0]["student_name"]
            chosen_city, chosen_dist = "", None
            for _, r in grp.iterrows():
                if r["score"] < -1e8:  # נפסל בגלל מרחק
                    continue
                site_nm = r["site_name"]
                if cap_left.get(site_nm, 0) > 0:
                    chosen, chosen_score = site_nm, float(r["score"])
                    chosen_city = site_city_map.get(site_nm, _strip(r.get("site_city","")))
                    chosen_dist = r.get("distance_km", None)
                    cap_left[site_nm] -= 1
                    break
            assignments.append({
                "student_id": sid,
                "student_name": sname,
                "assigned_site": chosen,
                "assigned_city": chosen_city,
                "assigned_distance_km": (None if pd.isna(chosen_dist) or chosen_dist is None else float(chosen_dist)),
                "match_score": round(chosen_score, 3),
                "status": "שובץ" if chosen != "ללא שיבוץ" else "ממתין"
            })

        asg = pd.DataFrame(assignments).sort_values("student_id")
        st.success(f"שובצו {(asg['status']=='שובץ').sum()} • ממתינים {(asg['status']=='ממתין').sum()}")
        st.dataframe(asg, use_container_width=True, height=420)

        cA, cB, cC = st.columns(3)
        with cA: st.metric("סה\"כ סטודנטים", len(asg))
        with cB: st.metric("שובצו", int((asg["status"]=="שובץ").sum()))
        with cC: st.metric("ממתינים", int((asg["status"]=="ממתין").sum()))

        st.session_state["assignments_df"] = asg

# =========================
# ייצוא
# =========================
with tab_export:
    st.subheader("הורדה/שמירה")
    if isinstance(st.session_state.get("assignments_df"), pd.DataFrame):
        out = st.session_state["assignments_df"].copy()
        st.dataframe(out, use_container_width=True, height=340)
        fname = f"assignments_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        bio = BytesIO(); out.to_csv(bio, index=False, encoding="utf-8-sig"); bio.seek(0)
        st.download_button("⬇️ הורדת CSV", bio, file_name=fname, mime="text/csv", use_container_width=True)
        if st.checkbox("שמור גם בשם הקבוע assignments.csv"):
            try:
                out.to_csv(DEFAULT_ASSIGN, index=False, encoding="utf-8-sig")
                st.success("נשמר assignments.csv בתיקיית האפליקציה.")
            except Exception as e:
                st.error(f"שגיאת שמירה: {e}")
    else:
        st.info("אין עדיין תוצאות – הריצי שיבוץ בטאב \"🧩 שיבוץ\".")
