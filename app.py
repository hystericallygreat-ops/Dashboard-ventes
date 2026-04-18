import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE ----------------
st.markdown("""
<style>

.block-container {
    max-width: 100% !important;
    padding-top: 3rem;
}

/* HERO */
.hero {
    background: linear-gradient(135deg, #E0F2FE 0%, #EDF7FA 100%);
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 15px;
}

/* CARD */
.card {
    background: white;
    padding: 14px;
    border-radius: 10px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

/* AGENT CARD (PLUS VISIBLE) */
.agent-card {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 2px solid #0F8BC6;
    box-shadow: 0 6px 16px rgba(15,139,198,0.2);
    margin-bottom: 15px;
}

/* SPECIAL KPI CARD */
.special-card {
    background: #F0F9FF;
    padding: 14px;
    border-radius: 10px;
    border: 2px solid #0F8BC6;
    margin-bottom: 10px;
}

/* PROGRESS */
.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* TAG */
[data-baseweb="tag"] {
    background-color:#E0F2FE !important;
    color:#0369A1 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <h2 style="color:#0F8BC6;margin:0;">HelloWatt</h2>
    <span style="color:#64748B;">Dashboard de performance commerciale</span>
</div>
""", unsafe_allow_html=True)

# ---------------- AUTH ----------------
password = st.sidebar.text_input("🔐 Admin", type="password")
is_admin = password == "hello123"

uploaded_file = None

if is_admin:
    uploaded_file = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
    if uploaded_file:
        with open(SAVE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())

    if os.path.exists(SAVE_PATH):
        if st.sidebar.button("🗑 Supprimer"):
            os.remove(SAVE_PATH)
            st.rerun()
else:
    if os.path.exists(SAVE_PATH):
        uploaded_file = SAVE_PATH

# ---------------- NAV ----------------
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "👤 Agents",
    "🎯 Objectifs"
])

# ---------------- UTILS ----------------
def clean_text(col):
    return (
        col.astype(str)
        .str.strip()
        .str.replace('"', '', regex=False)
        .str.replace("'", "", regex=False)
        .str.replace("\xa0", "", regex=False)
        .str.upper()
    )

def emoji(p):
    return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

def round_excel(x):
    return int(x + 0.5 + 1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr_holidays = holidays.FR()

    days = pd.date_range(start, today)
    working_days = [
        d for d in days
        if d.weekday() < 5 and d.date() not in fr_holidays
    ]
    return len(working_days)

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    df["responder"] = clean_text(df["responder"])
    code.iloc[:, 0] = clean_text(code.iloc[:, 0])

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
    df["energie"] = clean_text(df["energie"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    objectifs["Fournisseur"] = clean_text(objectifs["Fournisseur"])

    USER_COL = "user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), default=df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), default=df["energie"].unique())

    min_date = df["date"].min()
    max_date = df["date"].max()
    date_range = st.sidebar.date_input("Période", [min_date, max_date])

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs)) &
        (df["energie"].isin(energie))
    ]

    if len(date_range) == 2:
        df_filtered = df_filtered[
            (df_filtered["date"] >= pd.to_datetime(date_range[0])) &
            (df_filtered["date"] <= pd.to_datetime(date_range[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()

    # ---------------- OBJECTIFS ----------------
    if page == "🎯 Objectifs":

        st.title("🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        # -------- KPI GLOBAL AGENT --------
        objectif_agent = round_excel(heures * 0.75)
        ventes_total_agent = len(df_agent)
        taux_agent = ventes_total_agent / objectif_agent if objectif_agent else 0

        st.markdown('<div class="agent-card">', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3,6,2])
        col1.markdown(f"**{agent}**")
        col2.progress(min(taux_agent,1.0))
        col3.markdown(f"{emoji(taux_agent)} {ventes_total_agent}/{objectif_agent} ({taux_agent:.0%})")

        st.markdown('</div>', unsafe_allow_html=True)

        # -------- FOURNISSEURS CLASSIQUES (SANS HOMESERVE / FREE) --------
        special_providers = ["HOMESERVE", "FREE"]

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            if fournisseur in special_providers:
                continue

            df_f = df_agent[df_agent["get_provider"] == fournisseur]
            obj_row = objectifs[objectifs["Fournisseur"] == fournisseur]

            ventes = len(df_f)

            obj = round_excel(
                heures * 0.75 *
                (obj_row["Objectifs Total"].sum() / objectif_total)
            )

            p = ventes / obj if obj else 0

            col1, col2, col3 = st.columns([3,6,2])

            col1.markdown(f"**{fournisseur}**")
            col2.progress(min(p,1.0))
            col3.markdown(f"{emoji(p)} {ventes}/{obj} ({p:.0%})")

        # -------- FOURNISSEURS SPÉCIAUX --------
        st.markdown("### ⭐ Fournisseurs spécifiques")

        total_unique = df_agent[USER_COL].nunique()

        cols = st.columns(2)

        for i, sp in enumerate(special_providers):

            df_sp = df_agent[df_agent["get_provider"] == sp]
            ventes_sp = df_sp[USER_COL].nunique()

            obj_sp = max(1, round_excel(total_unique * 0.05))
            p_sp = ventes_sp / obj_sp if obj_sp else 0

            with cols[i]:
                st.markdown('<div class="special-card">', unsafe_allow_html=True)

                st.markdown(f"**{sp}**")
                st.progress(min(p_sp,1.0))
                st.markdown(f"{emoji(p_sp)} {ventes_sp}/{obj_sp} ({p_sp:.0%})")

                st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("🔒 Ajoute un fichier (admin uniquement)")
