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

    remitos = db.get_remitos()
    patentes_con_remito = set()
    ots_con_remito = set()
    if not remitos.empty:
        patentes_con_remito = set(remitos.get("Patente", pd.Series(dtype=str)).astype(str).str.upper())
        ots_con_remito = set(remitos.get("Nro_Orden_Taller", pd.Series(dtype=str)).astype(str).str.upper())

    df_ots["_ot_num"] = df_ots["Nro_OT"].astype(str).str.extract(r"(\d+)", expand=False).fillna("0").astype(int)
    df_ots = df_ots.sort_values("_ot_num", ascending=False, kind="stable")

    # Filtros de búsqueda
    col_e1, col_e2, col_e3 = st.columns([1.2, 1.3, 2.5])
    with col_e1:
        estados_disp = ["TODAS"]
        if "Estado" in df_ots.columns:
            estados_disp += [e for e in df_ots["Estado"].dropna().unique().tolist() if e]
        filtro_estado = st.selectbox("Filtrar por Estado:", estados_disp)
    with col_e2:
        filtro_vinculo = st.selectbox("Mostrar:", ["TODAS", "ASOCIADAS A REMITOS", "SIN REMITO"])
    with col_e3:
        q_ot = st.text_input("🔍 Buscar por N° OT, Patente o Reporte de Falla:", placeholder="Ej: OT-1001, AF395XD, Frenos, Service...").strip().lower()

    df_view = df_ots.copy()
    if filtro_estado != "TODAS" and "Estado" in df_view.columns:
        df_view = df_view[df_view["Estado"].astype(str).str.lower() == filtro_estado.lower()]
    if filtro_vinculo != "TODAS":
        def tiene_remito(row):
            ot = str(row.get("Nro_OT", "")).strip().upper()
            pat = str(row.get("Patente", "")).strip().upper()
            return ot in ots_con_remito or pat in patentes_con_remito
        vinculadas = df_view.apply(tiene_remito, axis=1)
        df_view = df_view[vinculadas if filtro_vinculo == "ASOCIADAS A REMITOS" else ~vinculadas]
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
            remitos_ot = remitos[remitos.get("Nro_Orden_Taller", pd.Series(dtype=str)).astype(str).str.upper() == nro.upper()] if not remitos.empty else pd.DataFrame()
            if not remitos_ot.empty:
                st.caption("Remitos asociados: " + ", ".join(remitos_ot["Nro_Remito"].astype(str).tolist()))
            st.caption(f"Identificación: {row.get('#ID', row.get('Nro_OT', '-'))} | Responsable: {row.get('RESPONSABLE DE TALLER ', '-')}")
            st.divider()
