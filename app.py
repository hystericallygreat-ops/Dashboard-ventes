import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays

st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background-color: #E2E8F0;
}

[data-baseweb="tag"] {
    background-color: #BFDBFE !important;
    color: #1E3A8A !important;
}

.stProgress > div > div > div > div {
    background-color:#0F8BC6;
}

/* bloc différencié agent */
.block {
    padding: 10px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 8px;
}

h1, h2, h3 {
    margin-top: 8px !important;
    margin-bottom: 8px !important;
}

</style>
""", unsafe_allow_html=True)

SAVE_PATH = "last_uploaded.xlsx"

st.title("HelloWatt - Dashboard")

page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])

uploaded_file = SAVE_PATH if os.path.exists(SAVE_PATH) else None

# ---------------- UTILS ----------------
def clean_text(col):
    return col.astype(str).str.strip().str.replace('"','').str.replace("'","").str.upper()

def emoji(p):
    return "🟢" if p>=1 else "🟠" if p>=0.7 else "🔴"

def round_excel(x):
    return int(x+0.5+1e-9)

def get_working_days():
    today = datetime.today()
    start = today.replace(day=1)
    fr = holidays.FR()
    days = pd.date_range(start, today)
    return len([d for d in days if d.weekday()<5 and d.date() not in fr])

# ---------------- APP ----------------
if uploaded_file:

    xls = pd.ExcelFile(uploaded_file)
    df = pd.read_excel(xls,"Extraction")
    code = pd.read_excel(xls,"Code")
    objectifs = pd.read_excel(xls,"Objectifs")

    df["responder"] = clean_text(df["responder"])
    code.iloc[:,0] = clean_text(code.iloc[:,0])

    df = df.merge(
        code.rename(columns={code.columns[0]:"responder",code.columns[1]:"agent"}),
        on="responder",how="left"
    )

    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
    df["energie"] = clean_text(df["energie"])
    df["date"] = pd.to_datetime(df["date"],errors="coerce")

    USER_COL = "user id"

    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")

    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())

    min_d,max_d = df["date"].min(),df["date"].max()
    dates = st.sidebar.date_input("Période",[min_d,max_d])

    # admin en bas
    st.sidebar.markdown("---")
    password = st.sidebar.text_input("🔐 Admin", type="password")
    is_admin = password == "hello123"

    if is_admin:
        uploaded_file_admin = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
        if uploaded_file_admin:
            with open(SAVE_PATH, "wb") as f:
                f.write(uploaded_file_admin.getbuffer())

        if os.path.exists(SAVE_PATH):
            if st.sidebar.button("🗑 Supprimer"):
                os.remove(SAVE_PATH)
                st.rerun()

    df_filtered = df[
        df["agent"].isin(agents) &
        df["get_provider"].isin(fournisseurs) &
        df["energie"].isin(energie)
    ]

    if len(dates)==2:
        df_filtered = df_filtered[
            (df_filtered["date"]>=pd.to_datetime(dates[0])) &
            (df_filtered["date"]<=pd.to_datetime(dates[1]))
        ]

    objectif_total = objectifs["Objectifs Total"].sum()

    # ================= DASHBOARD =================
    if page=="📊 Dashboard":

        st.header("🏢 Objectifs Globaux")

        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")

        df_obj = objectifs.merge(
            ventes,left_on="Fournisseur",right_on="get_provider",how="left"
        ).fillna(0)

        for _,r in df_obj.iterrows():

            p = r["ventes"]/r["Objectifs Total"] if r["Objectifs Total"] else 0

            c1,c2,c3 = st.columns([3,6,2])
            c1.write(r["Fournisseur"])
            c2.progress(min(p,1))
            c3.write(f"{emoji(p)} {int(r['ventes'])}/{int(r['Objectifs Total'])}")

    # ================= AGENTS =================
    elif page=="👤 Agents":

        st.header("👤 Performance Agents")

        jours = get_working_days()
        obj_agent = math.ceil(185*0.75)

        ventes_agent = df_filtered.groupby(["agent","energie"]).size().unstack(fill_value=0)

        if "ELEC" not in ventes_agent.columns:
            ventes_agent["ELEC"] = 0
        if "GAZ" not in ventes_agent.columns:
            ventes_agent["GAZ"] = 0

        ventes_agent["TOTAL"] = ventes_agent.sum(axis=1)

        for agent, row in ventes_agent.iterrows():

            total = row["TOTAL"]
            elec = row["ELEC"]
            gaz = row["GAZ"]

            elec_obj = obj_agent * (elec/total) if total else 0
            gaz_obj = obj_agent * (gaz/total) if total else 0

            total_taux = total/obj_agent if obj_agent else 0

            with st.container():
                c1,c2 = st.columns([3,7])

                c1.write(agent)

                c2.progress(min(total_taux,1))

                st.markdown(
                    f"⚡ {elec}/{int(elec_obj)}   "
                    f"🔥 {gaz}/{int(gaz_obj)}   "
                    f"🎯 {total}/{obj_agent} {emoji(total_taux)}",
                    unsafe_allow_html=True
                )

    # ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA, colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        st.markdown("<br>", unsafe_allow_html=True)

        df_agent = df_filtered[df_filtered["agent"]==agent]

        obj_agent = round_excel(heures*0.75)

        elec = len(df_agent[df_agent["energie"]=="ELEC"])
        gaz = len(df_agent[df_agent["energie"]=="GAZ"])
        total = len(df_agent)

        elec_obj = obj_agent * (elec/total) if total else 0
        gaz_obj = obj_agent * (gaz/total) if total else 0

        taux = total/obj_agent if obj_agent else 0

        st.markdown(
            f"""
            <div class="block">
                👤 {agent}<br><br>
                ⚡ {elec}/{int(elec_obj)}<br>
                🔥 {gaz}/{int(gaz_obj)}<br>
                🎯 {total}/{obj_agent} {emoji(taux)}
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.info("🔒 Ajoute un fichier (admin)")
