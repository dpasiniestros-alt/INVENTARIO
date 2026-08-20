# -*- coding: utf-8 -*-
"""
Vista de Inventario y Stock en Tiempo Real.
"""

import streamlit as st
import pandas as pd
from modules.gsheets_db import get_db

def render_inventario_view():
    db = get_db()
    st.markdown("## 📦 Control de Inventario en Tiempo Real")
    st.caption("Consulta de stock disponible, alertas y estados de reposición")

    df_prod = db.get_productos()
    if df_prod.empty:
        st.warning("No hay productos cargados en el inventario.")
        return

    df_prod["Stock_Actual"] = pd.to_numeric(df_prod["Stock_Actual"], errors="coerce").fillna(0)
    df_prod["Stock_Minimo"] = pd.to_numeric(df_prod["Stock_Minimo"], errors="coerce").fillna(0)
    total_articulos = len(df_prod)
    total_stock_unidades = df_prod["Stock_Actual"].sum()
    criticos = df_prod[df_prod["Stock_Actual"] <= df_prod["Stock_Minimo"]]
    sin_stock = df_prod[df_prod["Stock_Actual"] == 0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Variedad de Productos", f"{total_articulos}")
    c2.metric("Unidades Totales en Stock", f"{int(total_stock_unidades)}")
    c3.metric("Stock Bajo / Reposición", f"{len(criticos)}", delta=f"-{len(criticos)}" if len(criticos)>0 else "0", delta_color="inverse")
    c4.metric("Sin Stock (Agotados)", f"{len(sin_stock)}", delta=f"-{len(sin_stock)}" if len(sin_stock)>0 else "0", delta_color="inverse")

    st.divider()

    col_f1, col_f2 = st.columns([1.5, 2.5])
    with col_f1:
        filtro_stock = st.selectbox("Mostrar:", ["TODOS", "CON STOCK", "SIN STOCK"])
        categorias = ["TODAS"] + sorted(df_prod["Categoria"].unique().tolist())
        cat_filtro = st.selectbox("Filtrar por Categoría:", categorias)
    with col_f2:
        query_busqueda = st.text_input("🔍 Buscar por Marca, Modelo, Medida o Código:", placeholder="Ej: Moura, 205/55, PH5949, 12V 75Ah...").strip().lower()

    df_mostrar = df_prod.copy()
    if filtro_stock == "CON STOCK":
        df_mostrar = df_mostrar[df_mostrar["Stock_Actual"] > 0]
    elif filtro_stock == "SIN STOCK":
        df_mostrar = df_mostrar[df_mostrar["Stock_Actual"] == 0]
    if cat_filtro != "TODAS":
        df_mostrar = df_mostrar[df_mostrar["Categoria"] == cat_filtro]

    if query_busqueda:
        df_mostrar = df_mostrar[
            df_mostrar["Marca"].str.lower().str.contains(query_busqueda, na=False) |
            df_mostrar["Modelo_Detalle"].str.lower().str.contains(query_busqueda, na=False) |
            df_mostrar["Codigo_Pieza"].str.lower().str.contains(query_busqueda, na=False) |
            df_mostrar["Categoria"].str.lower().str.contains(query_busqueda, na=False)
        ]

    def get_estado_badge(row):
        stock = int(row["Stock_Actual"])
        minimo = int(row.get("Stock_Minimo", 1))
        if stock == 0:
            return "🔴 AGOTADO"
        elif stock <= minimo:
            return "🟡 STOCK BAJO"
        else:
            return "🟢 NORMAL"

    df_mostrar["Estado"] = df_mostrar.apply(get_estado_badge, axis=1)

    cols_order = ["Estado", "Categoria", "Marca", "Modelo_Detalle", "Codigo_Pieza", "Stock_Actual", "Unidad", "Stock_Minimo"]
    cols_existentes = [c for c in cols_order if c in df_mostrar.columns]

    st.dataframe(
        df_mostrar[cols_existentes],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Stock_Actual": st.column_config.NumberColumn("Stock Actual", format="%d un."),
            "Stock_Minimo": st.column_config.NumberColumn("Stock Mín.", format="%d"),
            "Modelo_Detalle": st.column_config.TextColumn("Detalle / Modelo / Medida"),
            "Codigo_Pieza": st.column_config.TextColumn("Cód. Pieza"),
        }
    )

    csv_data = df_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Inventario en CSV (Excel)",
        data=csv_data,
        file_name="inventario_taller.csv",
        mime="text/csv",
        use_container_width=False
    )
