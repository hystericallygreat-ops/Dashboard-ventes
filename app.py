import streamlit as st
import pandas as pd
import os
import math
from datetime import datetime
import holidays
 
st.set_page_config(page_title="HelloWatt Dashboard", layout="wide")
 
# ---------------- CSS ÉTENDU ----------------
# ÉTAPE 1 : Remplace l'ancien bloc CSS par celui-ci
# Nouveautés : .metric-card, .agent-row, .top-badge, .period-banner, .section-title
# Les classes existantes (.block, .stProgress, etc.) sont conservées intactes
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
.block {
    padding: 12px;
    border-radius: 10px;
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    margin-bottom: 12px;
}
h1, h2, h3 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
 
/* --- NOUVEAUX STYLES --- */
 
/* Carte métrique synthétique en haut de page */
.metric-card {
    background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
    border: 1px solid #BAE6FD;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    margin-bottom: 8px;
}
.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0369A1;
    line-height: 1.2;
}
.metric-card .metric-label {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
 
/* Ligne agent avec fond alterné */
.agent-row {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
}
.agent-row-alt {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
}
 
/* Badge top 3 */
.top-badge {
    font-size: 1.1rem;
    font-weight: 700;
    display: inline-block;
    margin-right: 6px;
}
 
/* Bannière période active */
.period-banner {
    background-color: #EFF6FF;
    border-left: 4px solid #3B82F6;
    border-radius: 0 8px 8px 0;
    padding: 8px 16px;
    margin-bottom: 16px;
    color: #1E40AF;
    font-size: 0.9rem;
}
 
/* Titre de section secondaire */
.section-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
    margin-top: 16px;
}
 
/* Séparateur discret entre lignes fournisseurs */
.fournisseur-row {
    border-bottom: 1px solid #F1F5F9;
    padding: 6px 0;
}
.fournisseur-row:last-child {
    border-bottom: none;
}
 
/* Résumé filtres actifs sidebar */
.filter-summary {
    background-color: #DBEAFE;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.8rem;
    color: #1E3A8A;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)
 
SAVE_PATH = "last_uploaded.xlsx"
 
# ---------------- HEADER ----------------
st.title("HelloWatt - Dashboard")
st.markdown("<br>", unsafe_allow_html=True)
 
# ---------------- NAV ----------------
page = st.sidebar.radio("Navigation", ["📊 Dashboard","👤 Agents","🎯 Objectifs"])
 
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 Admin")
password = st.sidebar.text_input("Mot de passe", type="password")
is_admin = password == "hello123"
 
if is_admin:
    uploaded_file_admin = st.sidebar.file_uploader("Uploader fichier Excel", type=["xlsx"])
    if uploaded_file_admin:
        with open(SAVE_PATH, "wb") as f:
            f.write(uploaded_file_admin.getbuffer())
        st.rerun()
    if os.path.exists(SAVE_PATH):
        if st.sidebar.button("🗑 Supprimer"):
            os.remove(SAVE_PATH)
            st.rerun()
 
uploaded_file = None
 
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
 
# ÉTAPE 2 : Nouvelle fonction utilitaire mutualisée pour sécuriser les colonnes énergie
# Ajoute-la juste après get_working_days(), avant le bloc if os.path.exists(SAVE_PATH)
def ensure_energie_cols(df_pivot):
    """Garantit que les colonnes ELEC et GAZ existent toujours après un unstack."""
    for col in ["ELEC", "GAZ"]:
        if col not in df_pivot.columns:
            df_pivot[col] = 0
    return df_pivot
 
# ÉTAPE 3 : Cache data — lecture Excel encapsulée pour éviter les rechargements inutiles
# Cette fonction remplace les 3 pd.read_excel() directs du bloc principal
@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, "Extraction")
    code = pd.read_excel(xls, "Code")
    objectifs = pd.read_excel(xls, "Objectifs")
    return df, code, objectifs
 
# ---------------- APP ----------------
if os.path.exists(SAVE_PATH):
    uploaded_file = SAVE_PATH
 
if uploaded_file:
 
    # Appel de la fonction cachée (remplace les 3 pd.read_excel directs)
    df, code, objectifs = load_data(uploaded_file)
 
    df["responder"] = clean_text(df["responder"])
    code.iloc[:,0] = clean_text(code.iloc[:,0])
 
    df = df.merge(
        code.rename(columns={code.columns[0]:"responder", code.columns[1]:"agent"}),
        on="responder", how="left"
    )
 
    df["agent"] = clean_text(df["agent"]).fillna("INCONNU")
    df["get_provider"] = clean_text(df["get_provider"])
 
    df["energie"] = (
        df["energie"]
        .astype(str)
        .str.strip()
        .str.lower()
        .replace({"gas":"GAZ","elec":"ELEC"})
        .str.upper()
    )
 
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    objectifs["Fournisseur"] = clean_text(objectifs["Fournisseur"])
 
    USER_COL = "user id"
 
    # ---------------- FILTRES ----------------
    st.sidebar.markdown("### 🔎 Filtres")
 
    agents = st.sidebar.multiselect("Agents", df["agent"].unique(), df["agent"].unique())
    fournisseurs = st.sidebar.multiselect("Fournisseurs", df["get_provider"].unique(), df["get_provider"].unique())
    energie = st.sidebar.multiselect("Énergie", df["energie"].unique(), df["energie"].unique())
 
    min_d, max_d = df["date"].min(), df["date"].max()
    dates = st.sidebar.date_input("Période", [min_d, max_d])
 
    df_filtered = df[
        df["agent"].isin(agents) &
        df["get_provider"].isin(fournisseurs) &
        df["energie"].isin(energie)
    ]
 
    if len(dates) == 2:
        df_filtered = df_filtered[
            (df_filtered["date"] >= pd.to_datetime(dates[0])) &
            (df_filtered["date"] <= pd.to_datetime(dates[1]))
        ]
 
    objectif_total = objectifs["Objectifs Total"].sum()
 
    # ÉTAPE 4 : Résumé filtres actifs en sidebar
    # Ajoute ce bloc juste après le filtre dates, avant le if page==
    n_agents_actifs = len(agents)
    n_fournisseurs_actifs = len(fournisseurs)
    energie_label = " + ".join(energie) if energie else "—"
    st.sidebar.markdown(
        f"<div class='filter-summary'>"
        f"👤 {n_agents_actifs} agent(s)<br>"
        f"🏢 {n_fournisseurs_actifs} fournisseur(s)<br>"
        f"⚡ {energie_label}"
        f"</div>",
        unsafe_allow_html=True
    )
 
    # ÉTAPE 4 (suite) : Bannière période active — affichée en haut de chaque page
    if len(dates) == 2:
        d_start = dates[0].strftime("%d/%m/%Y")
        d_end = dates[1].strftime("%d/%m/%Y")
        period_html = f"<div class='period-banner'>📅 Période active : <strong>{d_start}</strong> → <strong>{d_end}</strong></div>"
    else:
        period_html = ""
 
    # ================= DASHBOARD =================
    # ÉTAPE 5 : Remplace le bloc if page=="📊 Dashboard": par celui-ci
    if page == "📊 Dashboard":
 
        st.header("🏢 Objectifs Globaux")
        st.markdown(period_html, unsafe_allow_html=True)
 
        # --- Métriques synthétiques en haut ---
        # 3 cartes : total ventes, total objectif, taux global
        total_ventes = len(df_filtered)
        total_objectif = int(objectifs["Objectifs Total"].sum())
        taux_global = total_ventes / total_objectif if total_objectif else 0
 
        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{total_ventes}</div>"
            f"<div class='metric-label'>Ventes réalisées</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m2.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{total_objectif}</div>"
            f"<div class='metric-label'>Objectif total</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m3.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{emoji(taux_global)} {taux_global:.0%}</div>"
            f"<div class='metric-label'>Taux global</div>"
            f"</div>",
            unsafe_allow_html=True
        )
 
        st.markdown("<div class='section-title'>Détail par fournisseur</div>", unsafe_allow_html=True)
 
        # Logique inchangée — uniquement le rendu visuel est amélioré
        ventes = df_filtered.groupby("get_provider").size().reset_index(name="ventes")
 
        df_obj = objectifs.merge(
            ventes, left_on="Fournisseur", right_on="get_provider", how="left"
        ).fillna(0)
 
        df_obj = df_obj.sort_values("Objectifs Total", ascending=False)
 
        for i, (_, r) in enumerate(df_obj.iterrows()):
 
            p = r["ventes"] / r["Objectifs Total"] if r["Objectifs Total"] else 0
 
            df_f = df_filtered[df_filtered["get_provider"] == r["Fournisseur"]]
 
            v_elec = len(df_f[df_f["energie"] == "ELEC"])
            v_gaz = len(df_f[df_f["energie"] == "GAZ"])
 
            obj_elec = objectifs[objectifs["Fournisseur"] == r["Fournisseur"]]["Objectif Elec"].sum()
            obj_gaz = objectifs[objectifs["Fournisseur"] == r["Fournisseur"]]["Objectif Gaz"].sum()
 
            # Fond alterné pour lisibilité
            row_class = "fournisseur-row"
            with st.container():
                st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([3, 6, 4])
                c1.write(r["Fournisseur"])
                c2.progress(min(p, 1.0))
                c3.markdown(
                    f"⚡ {v_elec}/{int(obj_elec)} &nbsp;&nbsp; "
                    f"🔥 {v_gaz}/{int(obj_gaz)} &nbsp;&nbsp; "
                    f"🎯 {int(r['ventes'])}/{int(r['Objectifs Total'])} &nbsp;&nbsp; "
                    f"{emoji(p)} {p:.0%}",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
 
    # ================= AGENTS =================
    # ÉTAPE 6 : Remplace le bloc elif page=="👤 Agents": par celui-ci
    elif page == "👤 Agents":
 
        st.header("👤 Performance Agents")
        st.markdown(period_html, unsafe_allow_html=True)
 
        # Logique inchangée
        jours = get_working_days()
        obj_agent = math.ceil(185 * 0.75)
 
        ventes_agent = df_filtered.groupby("agent").size().reset_index(name="ventes")
 
        ventes_energie = (
            df_filtered
            .groupby(["agent", "energie"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
 
        # Utilisation de la fonction mutualisée (remplace les 2 if "ELEC"/"GAZ" not in)
        ventes_energie = ensure_energie_cols(ventes_energie)
 
        ventes_agent = ventes_agent.merge(ventes_energie, on="agent", how="left").fillna(0)
        ventes_agent["taux"] = ventes_agent["ventes"] / obj_agent
        ventes_agent["kpi"] = ventes_agent["ventes"] / jours if jours else 0
        ventes_agent = ventes_agent.sort_values("taux", ascending=False)
 
        # --- Métriques synthétiques en haut ---
        total_ventes_agents = int(ventes_agent["ventes"].sum())
        meilleur = ventes_agent.iloc[0]["agent"] if not ventes_agent.empty else "—"
        meilleur_taux = ventes_agent.iloc[0]["taux"] if not ventes_agent.empty else 0
 
        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{total_ventes_agents}</div>"
            f"<div class='metric-label'>Ventes totales</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m2.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{meilleur}</div>"
            f"<div class='metric-label'>Meilleur agent</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m3.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{jours}</div>"
            f"<div class='metric-label'>Jours ouvrés (mois)</div>"
            f"</div>",
            unsafe_allow_html=True
        )
 
        st.markdown("<div class='section-title'>Classement agents</div>", unsafe_allow_html=True)
 
        # Badges top 3
        BADGES = {0: "🥇", 1: "🥈", 2: "🥉"}
 
        for i, (_, r) in enumerate(ventes_agent.iterrows()):
 
            v_total = int(r["ventes"])
            v_elec = int(r["ELEC"])
            v_gaz = int(r["GAZ"])
            taux = r["taux"]
 
            # Fond alterné
            row_class = "agent-row" if i % 2 == 0 else "agent-row-alt"
 
            with st.container():
                st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)
 
                c1, c2, c3, c4 = st.columns([3, 5, 4, 2])
 
                # Badge top 3 + nom agent
                badge = BADGES.get(i, "")
                c1.markdown(
                    f"<span class='top-badge'>{badge}</span> {r['agent']}",
                    unsafe_allow_html=True
                )
 
                c2.progress(min(taux, 1.0))
 
                c3.markdown(
                    f"⚡ {v_elec} &nbsp;&nbsp; "
                    f"🔥 {v_gaz} &nbsp;&nbsp; "
                    f"🎯 {v_total}/{obj_agent} &nbsp;&nbsp; "
                    f"{emoji(taux)} {taux:.0%}",
                    unsafe_allow_html=True
                )
 
                c4.write(f"📅 {round(r['kpi'], 1)}/J")
 
                st.markdown("</div>", unsafe_allow_html=True)
 
    # ================= OBJECTIFS =================
    # ÉTAPE 7 : Remplace le bloc elif page=="🎯 Objectifs": par celui-ci
    elif page == "🎯 Objectifs":
 
        st.header("🎯 Performance détaillée")
        st.markdown(period_html, unsafe_allow_html=True)
 
        colA, colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())
 
        df_agent = df_filtered[df_filtered["agent"] == agent]
 
        # Logique inchangée
        obj_agent = round_excel(heures * 0.75)
        ventes_total = len(df_agent)
        taux = ventes_total / obj_agent if obj_agent else 0
 
        # --- Métriques synthétiques agent ---
        v_elec_agent = len(df_agent[df_agent["energie"] == "ELEC"])
        v_gaz_agent = len(df_agent[df_agent["energie"] == "GAZ"])
 
        m1, m2, m3 = st.columns(3)
        m1.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{ventes_total}</div>"
            f"<div class='metric-label'>Ventes totales</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m2.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>⚡ {v_elec_agent} &nbsp; 🔥 {v_gaz_agent}</div>"
            f"<div class='metric-label'>Elec / Gaz</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        m3.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-value'>{emoji(taux)} {taux:.0%}</div>"
            f"<div class='metric-label'>Taux objectif</div>"
            f"</div>",
            unsafe_allow_html=True
        )
 
        # Bloc récap agent (inchangé dans la logique, légèrement retouché visuellement)
        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.subheader(agent)
        st.progress(min(taux, 1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")
        st.markdown("</div>", unsafe_allow_html=True)
 
        st.markdown("<div class='section-title'>⚡ Ventes par fournisseur</div>", unsafe_allow_html=True)
 
        special = ["HOMESERVE", "FREE"]
 
        for i, f in enumerate(objectifs["Fournisseur"].dropna().unique()):
 
            if f in special:
                continue
 
            df_f = df_agent[df_agent["get_provider"] == f]
            obj_row = objectifs[objectifs["Fournisseur"] == f]
 
            # Logique de calcul inchangée
            obj_total_f = round_excel(
                heures * 0.75 * (obj_row["Objectifs Total"].sum() / objectif_total)
            )
            obj_elec_f = round_excel(
                heures * 0.75 * (obj_row["Objectif Elec"].sum() / objectif_total)
            )
            obj_gaz_f = round_excel(
                heures * 0.75 * (obj_row["Objectif Gaz"].sum() / objectif_total)
            )
 
            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"] == "ELEC"])
            v_gaz = len(df_f[df_f["energie"] == "GAZ"])
 
            p = v_total / obj_total_f if obj_total_f else 0
 
            # Séparateur alterné entre fournisseurs
            row_class = "fournisseur-row"
            with st.container():
                st.markdown(f"<div class='{row_class}'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 5, 5])
                c1.write(f)
                c2.progress(min(p, 1.0))
                c3.markdown(
                    f"⚡ {v_elec}/{obj_elec_f} &nbsp;&nbsp; "
                    f"🔥 {v_gaz}/{obj_gaz_f} &nbsp;&nbsp; "
                    f"🎯 {v_total}/{obj_total_f} &nbsp;&nbsp; "
                    f"{emoji(p)} {p:.0%}",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
 
else:
    st.info("🔒 Ajoute un fichier (admin)")
