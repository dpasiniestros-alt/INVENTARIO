# -*- coding: utf-8 -*-
"""
Panel de Control y Administracion del Taller.
"""

import streamlit as st
import pandas as pd
from modules.gsheets_db import get_db
from modules.catalog_seed import GERENCIAS
from modules.auth import check_admin_auth, render_admin_login, logout_admin

def render_admin_view():
    st.markdown("## ⚙️ Panel de Control y Administración")
    st.caption("Configuraciones del sistema, edición de receptores, flota de vehículos y catálogo")

    if not check_admin_auth():
        render_admin_login()
        return

    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.success("🔓 Sesión de Administrador activa")
    with c_head2:
        if st.button("Cerrar Sesión Admin", use_container_width=True):
            logout_admin()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Receptores / Clientes",
        "🚗 Flota y Patentes",
        "👨‍🔧 Responsables Taller",
        "📦 Ajustes de Stock",
        "☁️ Conexión Google Sheets & Email"
    ])

    db = get_db()

    with tab1:
        st.markdown("### 👥 Agenda de Receptores")
        st.info("Aquí puede corregir correos mal escritos o actualizar la gerencia de las personas que reciben materiales.")

        df_rec = db.get_receptores()
        
        if not df_rec.empty:
            for idx, r in df_rec.iterrows():
                with st.expander(f"👤 {r.get('nombre', '')} ({r.get('email', 'Sin email')})"):
                    with st.form(f"form_rec_{idx}"):
                        e_nombre = st.text_input("Nombre:", value=str(r.get("nombre", "")), key=f"rec_nom_{idx}")
                        e_email = st.text_input("Email:", value=str(r.get("email", "")), key=f"rec_mail_{idx}")
                        
                        idx_g = GERENCIAS.index(r.get("gerencia")) if r.get("gerencia") in GERENCIAS else 0
                        e_ger = st.selectbox("Gerencia:", GERENCIAS, index=idx_g, key=f"rec_ger_{idx}")
                        
                        c_sav, c_del = st.columns([2, 1])
                        with c_sav:
                            sub_rec = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                            if sub_rec:
                                df_rec.at[idx, "nombre"] = e_nombre
                                df_rec.at[idx, "email"] = e_email
                                df_rec.at[idx, "gerencia"] = e_ger
                                db.save_receptores(df_rec)
                                st.success("Datos actualizados correctamente.")
                                st.rerun()
        else:
            st.write("No hay receptores registrados aún.")

        st.divider()
        st.markdown("#### ➕ Agregar Nuevo Receptor:")
        with st.form("form_new_rec"):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_nom = st.text_input("Apellido y Nombre:")
            with c2:
                n_mail = st.text_input("Correo Electrónico:")
            with c3:
                n_ger = st.selectbox("Gerencia:", GERENCIAS)
            if st.form_submit_button("Agregar Receptor", use_container_width=True):
                if n_nom:
                    db.add_or_update_receptor(n_nom, n_mail, n_ger)
                    st.success(f"Receptor {n_nom} agregado.")
                    st.rerun()

    with tab2:
        st.markdown("### 🚗 Gestión de Flota y Patentes")
        st.caption("Estado de vehículos (ACTIVO, BAJA, ACTIVO (OTROS)) y registro de Fecha de Baja para trazabilidad histórica.")

        df_veh = db.get_vehiculos(solo_activos=False)

        q_pat = st.text_input("🔍 Buscar Patente:", placeholder="Ej: AF395...").strip().upper()
        if q_pat and not df_veh.empty:
            df_veh = df_veh[df_veh["PATENTE"].str.contains(q_pat, na=False)]

        df_veh_display = df_veh.loc[:, ~df_veh.columns.duplicated(keep="first")].copy()
        if df_veh_display.empty:
            st.warning("No se pudo leer la hoja VEHICULOS del libro DPA en este momento.")
        else:
            st.dataframe(
                df_veh_display,
                use_container_width=True,
                hide_index=True
            )

        st.info("La flota se lee exclusivamente desde el libro DPA PARQUE Automotor Grupo Sima, hoja VEHICULOS. Esta aplicación no modifica ese libro.")

    with tab3:
        st.markdown("### 👨‍🔧 Personal Autorizado de Taller")
        df_resp = db.get_responsables()
        st.dataframe(df_resp, use_container_width=True, hide_index=True)

        with st.form("form_new_resp"):
            st.markdown("#### ➕ Registrar Nuevo Responsable:")
            n_resp_nom = st.text_input("Apellido y Nombre:")
            n_resp_pin = st.text_input("PIN de Acceso (4 dígitos):", value="1234", type="password")
            if st.form_submit_button("Guardar Responsable", use_container_width=True):
                if n_resp_nom:
                    db.add_responsable(n_resp_nom, n_resp_pin)
                    st.success(f"Responsable {n_resp_nom} habilitado.")
                    st.rerun()

    with tab4:
        st.markdown("### 📦 Ajuste Manual de Inventario")
        st.caption("Permite corregir desvíos o realizar inventario inicial físico.")

        df_prod = db.get_productos()
        if not df_prod.empty:
            prod_labels = [f"{p['ID']} | [{p['Categoria']}] {p['Marca']} - {p['Modelo_Detalle']} (Stock actual: {p['Stock_Actual']})" for _, p in df_prod.iterrows()]
            sel_p_adj = st.selectbox("Seleccione el Producto a ajustar:", prod_labels)
            
            p_id = sel_p_adj.split("|")[0].strip()
            row_p = df_prod[df_prod["ID"] == p_id].iloc[0]

            with st.form("form_adj_stock"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    nuevo_stock = st.number_input("Nuevo Stock Real:", min_value=0, value=int(row_p["Stock_Actual"]), step=1)
                with col_a2:
                    nuevo_min = st.number_input("Stock Mínimo de Alerta:", min_value=0, value=int(row_p.get("Stock_Minimo", 1)), step=1)

                motivo = st.text_input("Motivo del Ajuste (para auditoría):", placeholder="Ej: Conteo físico mensual, rotura, etc.")

                if st.form_submit_button("Confirmar Ajuste de Stock", use_container_width=True):
                    idx_p = df_prod.index[df_prod["ID"] == p_id][0]
                    df_prod.at[idx_p, "Stock_Actual"] = int(nuevo_stock)
                    df_prod.at[idx_p, "Stock_Minimo"] = int(nuevo_min)
                    db.save_productos(df_prod)
                    db.registrar_auditoria(
                        str(st.session_state.get("current_user", "")),
                        "AJUSTE_STOCK",
                        "producto",
                        p_id,
                        {"stock": int(nuevo_stock), "stock_minimo": int(nuevo_min), "motivo": motivo},
                    )
                    st.success(f"Stock de {row_p['Modelo_Detalle']} actualizado a {nuevo_stock} unidades.")
                    st.rerun()

    with tab5:
        st.markdown("### ☁️ Estado de Conexión en la Nube")
        
        if db.is_connected_gsheets:
            inv_id = getattr(db.spreadsheet_inventario, "id", "desconocido")
            veh_id = getattr(db.spreadsheet_vehiculos, "id", "desconocido")
            st.success(f"🟢 Conectado a Google Sheets. Inventario: {inv_id} | Flota (solo lectura): {veh_id}")
        else:
            st.warning("🟡 Funcionando en modo de almacenamiento local seguro. Para conectar directamente con tu Google Sheets en la nube, configura las credenciales en secrets.toml.")

        email_cfg = {}
        if hasattr(st, "secrets") and "email" in st.secrets:
            email_cfg = st.secrets["email"]

        if email_cfg and email_cfg.get("sender_email"):
            st.success(f"🟢 Envío de Emails SMTP Configurado (Remitente: {email_cfg.get('sender_email')})")
        else:
            st.info("⚪ Para habilitar el envío automático de PDFs por correo, configura la sección [email] en secrets.toml.")

        with st.expander("📖 Ver Guía Rápida de Configuración de Secrets"):
            st.code("""
# En Streamlit Cloud > Settings > Secrets:
ADMIN_PIN = "1234"
GSHEET_SPREADSHEET_ID = "1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU"

[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "tu-servicio@tu-proyecto.iam.gserviceaccount.com"

[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "taller.empresa@gmail.com"
sender_password = "tu-contraseña-de-aplicacion"
sender_name = "Taller Automotor"
copy_to_taller = "taller.empresa@gmail.com"
            """, language="toml")
