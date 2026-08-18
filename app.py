# -*- coding: utf-8 -*-
"""
Sistema de Gestion de Inventario y Remitos Digitales - Taller Automotor.
"""

import streamlit as st

st.set_page_config(
    page_title="Taller Automotor - Remitos e Inventario",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1050px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        min-height: 44px;
    }
    h1, h2, h3 {
        color: #0F172A;
    }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    iframe {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
    }
</style>
""", unsafe_allow_html=True)

from views.remito_view import render_remito_view
from views.inventario_view import render_inventario_view
from views.trazabilidad_view import render_trazabilidad_view
from views.historial_view import render_historial_view
from views.ordenes_view import render_ordenes_view
from views.admin_view import render_admin_view

def main():
    st.title("🚗 Taller Automotor")
    
    menu_options = [
        "📋 Nuevo Remito",
        "🔍 Trazabilidad (Baterías/Neumáticos)",
        "📦 Stock e Inventario",
        "📜 Historial de Remitos",
        "🔧 Órdenes de Taller",
        "⚙️ Panel de Control"
    ]

    selected_view = st.radio(
        "Menú de Navegación",
        menu_options,
        horizontal=True,
        label_visibility="collapsed"
    )
    st.divider()

    if selected_view == "📋 Nuevo Remito":
        render_remito_view()
    elif selected_view == "🔍 Trazabilidad (Baterías/Neumáticos)":
        render_trazabilidad_view()
    elif selected_view == "📦 Stock e Inventario":
        render_inventario_view()
    elif selected_view == "📜 Historial de Remitos":
        render_historial_view()
    elif selected_view == "🔧 Órdenes de Taller":
        render_ordenes_view()
    elif selected_view == "⚙️ Panel de Control":
        render_admin_view()

if __name__ == "__main__":
    main()