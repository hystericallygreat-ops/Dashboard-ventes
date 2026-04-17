import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard SaaS Ventes", layout="wide")

# ---------------- CONFIG FICHIER ----------------
SAVE_PATH = "last_uploaded.xlsx"

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file is not None:
    with open(SAVE_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())

if uploaded_file is None and os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH

if os.path.exists(SAVE_PATH):
    if st.sidebar.button("🗑 Supprimer le fichier chargé"):
        os.remove(SAVE_PATH)
        st.rerun()

# ---------------- STYLE ULTRA SAAS ----------------
st.markdown("""
<style>

/* GLOBAL */
body {
    background-color: #F7F9FB;
}

/* TITRES */
h1, h2, h3 {
    font-weight: 600;
    color: #0F172A;
}

/* KPI CARDS */
.card {
    background: white;
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.05);
}

.kpi-title {
    font-size: 13px;
    color: #64748B;
}

.kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #0F172A;
}

.kpi-sub {
    font-size: 14px;
    color: #22C55E;
}

/* PROGRESS BAR */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #3B82F6, #06B6D4);
    border-radius: 10px;
}

/* LIST CARDS */
.list-card {
    background: white;
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.04);
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E7EB;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Ventes")

# ---------------- SI FICHIER ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # CLEAN
    df["responder"] = df["responder"].astype(str).str.strip().str.upper()
    code.iloc[:, 0] = code.iloc[:, 0].astype(str).str.strip().str.upper()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # ---------------- FILTRES ----------------
    st.sidebar.header("🔎 Filtres")

    agents = st.sidebar.multiselect("Agent", df["agent"].unique(), default=df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseur", df["get_provider"].unique(), default=df["get_provider"].unique())

    df_filtered = df[
        (df["agent"].isin(agents)) &
        (df["get_provider"].isin(fournisseurs))
    ]

    # ---------------- KPI ----------------
    total_sales = len(df_filtered)
    objectif_total = objectifs["Objectifs Total"].sum()

    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    def kpi(col, title, value, taux):
        col.markdown(f"""
        <div class="card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{taux:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(col1, "Ventes Totales", total_sales, taux_global)
    kpi(col2, "Objectif Global", int(objectif_total), 1)
    kpi(col3, "Progression", "", taux_global)

    st.markdown("---")

    # ---------------- OBJECTIF FOURNISSEUR ----------------
    st.subheader("🏢 Performance Fournisseurs")

    objectif_global_185h = 185 * 0.75

    ventes_fournisseur = (
        df_filtered.groupby("get_provider")
        .size()
        .reset_index(name="ventes")
    )

    rows = []

    for _, row in ventes_fournisseur.iterrows():

        fournisseur = row["get_provider"]
        ventes = row["ventes"]

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        objectif_fournisseur = 0
        if not obj_row.empty and objectif_total:
            part = obj_row["Objectifs Total"].sum() / objectif_total
            objectif_fournisseur = objectif_global_185h * part

        taux = ventes / objectif_fournisseur if objectif_fournisseur else 0

        rows.append((fournisseur, ventes, objectif_fournisseur, taux))

    # TRI BEST → WORST
    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    for f, v, obj, t in rows:

        st.markdown(f"""
        <div class="list-card">
            <b>{f}</b><br>
            {emoji(t)} {v} / {int(obj)} ({t:.0%})
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(t, 1.0))

    st.markdown("---")

    # ---------------- OBJECTIF AGENTS ----------------
    st.subheader("👤 Performance Agents (base 185h)")

    ventes_agent = (
        df_filtered.groupby("agent")
        .size()
        .reset_index(name="ventes")
    )

    rows = []

    for _, row in ventes_agent.iterrows():

        agent = row["agent"]
        ventes = row["ventes"]

        objectif_agent = objectif_global_185h
        taux = ventes / objectif_agent if objectif_agent else 0

        rows.append((agent, ventes, objectif_agent, taux))

    rows = sorted(rows, key=lambda x: x[3], reverse=True)

    for a, v, obj, t in rows:

        st.markdown(f"""
        <div class="list-card">
            <b>{a}</b><br>
            {emoji(t)} {v} / {int(obj)} ({t:.0%})
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(t, 1.0))

    st.markdown("---")

    # ---------------- PERFORMANCE DETAIL ----------------
    st.subheader("🎯 Détail par Agent")

    heures = st.number_input("Heures travaillées", value=185.0)
    agent_select = st.selectbox("Choisir un agent", df_filtered["agent"].unique())

    df_agent = df_filtered[df_filtered["agent"] == agent_select]

    for fournisseur in objectifs["Fournisseur"].dropna().unique():

        df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
        ventes = len(df_f)

        obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

        objectif = 0
        if not obj_row.empty and objectif_total:
            part = obj_row["Objectifs Total"].sum() / objectif_total
            objectif = heures * 0.75 * part

        taux = ventes / objectif if objectif else 0

        st.markdown(f"**{fournisseur}**")
        st.caption(f"{emoji(taux)} {ventes} / {int(objectif)} ({taux:.0%})")
        st.progress(min(taux, 1.0))

else:
    st.info("Veuillez uploader un fichier Excel")
