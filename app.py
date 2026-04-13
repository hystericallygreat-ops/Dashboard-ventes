import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 20px;
    border-radius: 14px;
    color: white;
}
.metric-title {font-size: 14px; opacity: 0.7;}
.metric-value {font-size: 28px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard des ventes")

uploaded_file = st.file_uploader("Uploader votre fichier Excel", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")

    # Mapping agents
    code_dict = dict(zip(code.iloc[:, 0], code.iloc[:, 1]))
    df["agent"] = df["responder"].map(code_dict)

    # ---------------- KPI GLOBAL ----------------
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""<div class='metric-card'><div class='metric-title'>Ventes</div><div class='metric-value'>{total_sales}</div></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class='metric-card'><div class='metric-title'>Objectif</div><div class='metric-value'>{objectif_total}</div></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class='metric-card'><div class='metric-title'>Taux</div><div class='metric-value'>{taux_global:.1%}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------------- OBJECTIF INDIVIDUEL ----------------
    st.subheader("🎯 Objectif individuel")

    heures = st.number_input("Heures planifiées du mois", min_value=0.0, step=1.0)

    total_objectifs = objectifs["Objectifs Total"].sum()

    # Calcul proportion fournisseur
    objectifs["poids"] = objectifs["Objectifs Total"] / total_objectifs

    objectifs["objectif_individuel"] = heures * 0.75 * objectifs["poids"]

    st.dataframe(objectifs[["Fournisseur", "Objectifs Total", "objectif_individuel"]], use_container_width=True)

    st.markdown("---")

    # ---------------- VENTES PAR AGENT ----------------
    ventes_agent = df.groupby("agent").size().reset_index(name="ventes")

    # Calcul objectif individuel par agent (total)
    objectif_indiv_total = heures * 0.75

    ventes_agent["taux"] = ventes_agent["ventes"] / objectif_indiv_total if objectif_indiv_total else 0

    ventes_agent = ventes_agent.sort_values(by="ventes", ascending=False)

    # ---------------- GRAPHIQUE ----------------
    fig = px.bar(ventes_agent, x="agent", y="ventes", title="Classement agents", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- TABLE ----------------
    st.subheader("📋 Performance agents")
    st.dataframe(ventes_agent, use_container_width=True)

    # ---------------- PODIUM ----------------
    st.subheader("🏆 Top 3")
    top3 = ventes_agent.head(3)
    cols = st.columns(3)

    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"""<div class='metric-card'><div class='metric-value'>{row.agent}</div><div>{row.ventes} ventes</div></div>""", unsafe_allow_html=True)

else:
    st.info("Veuillez uploader un fichier Excel")
