# -*- coding: utf-8 -*-
"""
Modulo de Autenticacion y Seguridad por PIN.
"""

import streamlit as st
from modules.gsheets_db import get_db

def get_secret(key, default=""):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

def check_admin_auth() -> bool:
    usuario = str(st.session_state.get("current_user", "")).strip()
    if not st.session_state.get("user_authenticated", False) or not usuario:
        return False
    return get_db().es_administrador(usuario)

def render_admin_login() -> bool:
    st.markdown("### 🔒 Acceso al Panel de Control")
    st.info("Esta sección está reservada a los responsables habilitados como administradores.")
    st.warning(f"El usuario {st.session_state.get('current_user', 'actual')} no tiene permisos de administración.")
    return False

def logout_admin():
    st.session_state["is_admin_authenticated"] = False
    st.rerun()

def is_user_authenticated() -> bool:
    return bool(st.session_state.get("user_authenticated", False))

def logout_user():
    st.session_state["user_authenticated"] = False
    st.session_state.pop("current_user", None)
    st.session_state.pop("is_admin_authenticated", None)
    st.session_state.pop("cart_items", None)
    st.rerun()

def render_login() -> bool:
    """Pantalla inicial de acceso para responsables del taller."""
    st.markdown("## Acceso al Taller Automotor")
    st.caption("Seleccione su nombre e ingrese su clave para continuar.")

    with st.spinner("Cargando responsables autorizados..."):
        responsables = get_db().get_responsables()

    if responsables.empty or "nombre" not in responsables.columns:
        st.error("No hay responsables disponibles. Verifique la hoja RESPONSABLES en Google Sheets.")
        return False

    nombres = [str(nombre).strip() for nombre in responsables["nombre"].tolist() if str(nombre).strip()]
    if not nombres:
        st.error("No hay responsables autorizados cargados.")
        return False

    with st.form("form_login_usuario"):
        nombre = st.selectbox("Responsable:", nombres)
        pin = st.text_input("Clave:", type="password", placeholder="Ingrese su clave")
        ingresar = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

    if ingresar:
        filas = responsables[responsables["nombre"].astype(str).str.strip() == nombre]
        pin_guardado = str(filas.iloc[0].get("pin", "")).strip() if not filas.empty else ""
        if pin_guardado and pin.strip() == pin_guardado:
            st.session_state["user_authenticated"] = True
            st.session_state["current_user"] = nombre
            st.rerun()
        else:
            st.error("Clave incorrecta.")
    return False
