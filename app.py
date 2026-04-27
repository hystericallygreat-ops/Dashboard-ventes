# ================= OBJECTIFS =================
    elif page=="🎯 Objectifs":

        st.header("🎯 Performance détaillée")

        colA,colB = st.columns(2)
        heures = colA.number_input("Heures", value=185.0)
        agent = colB.selectbox("Agent", df_filtered["agent"].unique())

        df_agent = df_filtered[df_filtered["agent"] == agent]

        obj_agent = round_excel(heures*0.75)
        ventes_total = len(df_agent)
        taux = ventes_total/obj_agent if obj_agent else 0

        # ✅ CARTE
        st.markdown("<div class='block'>", unsafe_allow_html=True)
        st.subheader(agent)
        st.progress(min(taux,1.0))
        st.write(f"{emoji(taux)} {ventes_total}/{obj_agent} ({taux:.0%})")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### ⚡ Ventes Fournisseurs")

        special=["HOMESERVE","FREE"]

        for f in objectifs["Fournisseur"].dropna().unique():

            if f in special:
                continue

            df_f = df_agent[df_agent["get_provider"]==f]
            obj_row = objectifs[objectifs["Fournisseur"]==f]

            obj_total_f = round_excel(
                heures*0.75*(obj_row["Objectifs Total"].sum()/objectif_total)
            )

            obj_elec_f = round_excel(
                heures*0.75*(obj_row["Objectif Elec"].sum()/objectif_total)
            )

            obj_gaz_f = round_excel(
                heures*0.75*(obj_row["Objectif Gaz"].sum()/objectif_total)
            )

            v_total = len(df_f)
            v_elec = len(df_f[df_f["energie"]=="ELEC"])
            v_gaz = len(df_f[df_f["energie"]=="GAZ"]

)

            p = v_total/obj_total_f if obj_total_f else 0

            c1,c2,c3 = st.columns([2,5,5])
            c1.write(f)
            c2.progress(min(p,1.0))
            c3.markdown(
                f"⚡ {v_elec}/{obj_elec_f} &nbsp;&nbsp; "
                f"🔥 {v_gaz}/{obj_gaz_f} &nbsp;&nbsp; "
                f"🎯 {v_total}/{obj_total_f} &nbsp;&nbsp; "
                f"{emoji(p)} {p:.0%}",
                unsafe_allow_html=True
            )

