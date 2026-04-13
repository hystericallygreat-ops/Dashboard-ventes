import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Ventes", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.metric-card {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: white;
}
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
    code_dict = dict(zip(code.iloc[:,0], code.iloc[:,1]))
    df["agent"] = df["responder"].map(code_dict)

    # Nettoyage
    df["energie"] = df["energie"].str.lower()

    # KPI
    total_sales = len(df)
    objectif_total = objectifs["Objectifs Total"].sum()
    taux_global = total_sales / objectif_total if objectif_total else 0

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"""<div class='metric-card'><h2>{total_sales}</h2><p>Ventes</p></div>""", unsafe_allow_html=True)
    col2.markdown(f"""<div class='metric-card'><h2>{objectif_total}</h2><p>Objectif</p></div>""", unsafe_allow_html=True)
    col3.markdown(f"""<div class='metric-card'><h2>{taux_global:.1%}</h2><p>Taux</p></div>""", unsafe_allow_html=True)

    st.divider()

    # Ventes par fournisseur
    ventes_fournisseur = df.groupby("get_provider").size().reset_index(name="ventes")
    fig_fournisseur = px.bar(ventes_fournisseur, x="get_provider", y="ventes", title="Ventes par fournisseur")
    st.plotly_chart(fig_fournisseur, use_container_width=True)

    # Ventes par agent
    ventes_agent = df.groupby("agent").size().reset_index(name="ventes")
    ventes_agent = ventes_agent.sort_values(by="ventes", ascending=False)

    fig_agent = px.bar(ventes_agent, x="agent", y="ventes", title="Classement des agents")
    st.plotly_chart(fig_agent, use_container_width=True)

    # Podium
    st.subheader("🏆 Top 3 agents")
    top3 = ventes_agent.head(3)

    cols = st.columns(3)
    for i, row in enumerate(top3.itertuples()):
        cols[i].markdown(f"""<div class='metric-card'><h3>#{i+1}</h3><h2>{row.agent}</h2><p>{row.ventes} ventes</p></div>""", unsafe_allow_html=True)

    st.divider()

    # Tableau détaillé
    st.subheader("📋 Détail par agent")

    df_detail = ventes_agent.copy()
    df_detail["taux"] = df_detail["ventes"] / objectif_total

    st.dataframe(df_detail, use_container_width=True)

else:
    st.info("Veuillez uploader un fichier Excel pour commencer.")
