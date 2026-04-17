import streamlit as st
import pandas as pd
import os
import math

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

SAVE_PATH = "last_uploaded.xlsx"

# ---------------- STYLE ----------------
st.markdown("""
<style>
html, body {
    background-color: #F7F9FB;
}

.block-container {
    padding-top: 2rem;
}

h1 {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
}

h2 {
    font-size: 20px;
    font-weight: 600;
    color: #374151;
}

.metric-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E5E7EB;
}

.metric-value {
    font-size: 26px;
    font-weight: 700;
}

.metric-label {
    color: #6B7280;
    font-size: 13px;
}

.stProgress > div > div > div > div {
    background-color: #3B82F6;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col_logo, col_title = st.columns([1,5])

with col_logo:
    st.image("https://logo.clearbit.com/hellowatt.fr", width=80)

with col_title:
    st.markdown("# Dashboard Ventes")
    st.caption("Suivi des performances commerciales")

st.markdown("---")

# ---------------- AUTH ----------------
password = st.sidebar.text_input("🔐 Admin", type="password")
is_admin = password == "hello123"

# ---------------- UPLOAD ----------------
uploaded_file = None

if is_admin:
    uploaded_file = st.sidebar.file_uploader("Uploader Excel", type=["xlsx"])

    if uploaded_file is not None:
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
page = st.sidebar.radio("", [
    "Dashboard",
    "Agents",
    "Objectifs"
])

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    df["responder"] = df["responder"].astype(str).str.upper().str.strip()
    code.iloc[:,0] = code.iloc[:,0].astype(str).str.upper().str.strip()

    df = df.merge(
        code.rename(columns={code.columns[0]: "responder", code.columns[1]: "agent"}),
        on="responder",
        how="left"
    )

    df["agent"] = df["agent"].fillna("Inconnu")

    df_filtered = df

    objectif_total = objectifs["Objectifs Total"].sum()

    def emoji(p):
        return "🟢" if p >= 1 else "🟠" if p >= 0.7 else "🔴"

    # ---------------- DASHBOARD ----------------
    if page == "Dashboard":

        total = len(df_filtered)
        taux = total / objectif_total if objectif_total else 0

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Ventes</div>
                <div class="metric-value">{total}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Progression</div>
                <div class="metric-value">{taux:.0%}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("## 🎯 Performance détaillée")

        heures = st.number_input("Heures", value=185.0)
        agent = st.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        for fournisseur in objectifs["Fournisseur"].dropna().unique():

            df_f = df_agent[df_agent["get_provider"].str.lower() == fournisseur.lower()]
            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == fournisseur.lower()]

            ventes = len(df_f)

            obj = math.ceil(obj_row["Objectifs Total"].sum() * (heures / 185))

            p = ventes / obj if obj else 0

            st.markdown(f"**{fournisseur}**")
            st.caption(f"{emoji(p)} {ventes}/{obj} ({p:.0%})")
            st.progress(min(p,1.0))

    # ---------------- AGENTS ----------------
    elif page == "Agents":

        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")

        objectif_agent = math.ceil(185 * 0.75)

        ventes_agent["taux"] = ventes_agent["ventes"] / objectif_agent
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)

        for _, r in ventes_agent.iterrows():
            st.markdown(f"**{r['agent']}**")
            st.caption(f"{emoji(r['taux'])} {r['ventes']}/{objectif_agent}")
            st.progress(min(r["taux"],1.0))

    # ---------------- OBJECTIFS ----------------
    elif page == "Objectifs":

        ventes_fournisseur = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        for _, r in ventes_fournisseur.iterrows():

            obj_row = objectifs[objectifs["Fournisseur"].str.lower() == r["get_provider"].lower()]
            obj = obj_row["Objectifs Total"].sum()

            p = r["ventes"] / obj if obj else 0

            st.markdown(f"**{r['get_provider']}**")
            st.caption(f"{emoji(p)} {r['ventes']}/{int(obj)}")
            st.progress(min(p,1.0))

else:
    st.info("Ajoute un fichier (admin uniquement)")
