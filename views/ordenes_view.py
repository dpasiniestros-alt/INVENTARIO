# -*- coding: utf-8 -*-
"""
Vista de Consulta de Ordenes de Taller (OT) - Modo Lectura de Google Sheets.
"""

import streamlit as st
import pandas as pd
from modules.gsheets_db import get_db

def render_ordenes_view():
    db = get_db()
    st.markdown("## 🔧 Solicitudes y Órdenes de Trabajo (OT)")
    st.caption("Consulta de órdenes de trabajo generadas por el sistema central (Hoja 'COORDINACION DE ENVIO A TALLER')")

    df_ots = db.get_ordenes_taller()

    if df_ots.empty:
        st.info("No hay órdenes de taller registradas o sincronizadas en este momento.")
        return

    # Filtros de busqueda
    col_e1, col_e2 = st.columns([1.5, 2.5])
    with col_e1:
        estados_disp = ["TODAS"]
        if "Estado" in df_ots.columns:
            estados_disp += [e for e in df_ots["Estado"].dropna().unique().tolist() if e]
        filtro_estado = st.selectbox("Filtrar por Estado:", estados_disp)
    with col_e2:
        q_ot = st.text_input("🔍 Buscar por N° OT, Patente o Reporte de Falla:", placeholder="Ej: OT-1001, AF395XD, Frenos, Service...").strip().lower()

    df_view = df_ots.copy()
    if filtro_estado != "TODAS" and "Estado" in df_view.columns:
        df_view = df_view[df_view["Estado"].astype(str).str.lower() == filtro_estado.lower()]
    if q_ot:
        df_view = df_view[
            df_view.get("Nro_OT", pd.Series()).astype(str).str.lower().str.contains(q_ot, na=False) |
            df_view.get("Patente", pd.Series()).astype(str).str.lower().str.contains(q_ot, na=False) |
            df_view.get("Descripcion_Trabajo", pd.Series()).astype(str).str.lower().str.contains(q_ot, na=False) |
            df_view.get("Gerencia", pd.Series()).astype(str).str.lower().str.contains(q_ot, na=False)
        ]

    st.write(f"**Órdenes encontradas ({len(df_view)}):**")

    for _, row in df_view.iterrows():
        nro = str(row.get("Nro_OT", "-"))
        est = str(row.get("Estado", "Pendiente"))
        pat = str(row.get("Patente", "-"))
        ger = str(row.get("Gerencia", "-"))
        desc = str(row.get("Descripcion_Trabajo", "-"))
        fecha = str(row.get("Fecha", "-"))

        badge_color = "🟡" if "PEND" in est.upper() else ("🔵" if "PROC" in est.upper() else "🟢")
        
        with st.container():
            st.markdown(f"### {badge_color} {nro} | Patente: {pat} ({ger})")
            if fecha and fecha != "-":
                st.markdown(f"**Fecha:** {fecha} | **Estado:** {est}")
            else:
                st.markdown(f"**Estado:** {est}")
            st.markdown(f"**Reporte de Falla / Motivo:** {desc}")
            st.divider()
