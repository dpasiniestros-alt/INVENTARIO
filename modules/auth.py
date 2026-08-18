# -*- coding: utf-8 -*-
"""
Modulo de Autenticacion y Seguridad por PIN.
"""

import streamlit as st

def get_secret(key, default=""):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

def check_admin_auth() -> bool:
    if st.session_state.get("is_admin_authenticated", False):
        return True
    return False

def render_admin_login() -> bool:
    st.markdown("### 🔒 Acceso al Panel de Control")
    st.info("Esta sección está reservada para administradores y supervisores del taller.")
    
    admin_pin_secret = get_secret("ADMIN_PIN", "1234")
    
    with st.form("form_admin_auth"):
        pin_ingresado = st.text_input("Ingrese PIN de Administrador:", type="password", placeholder="****")
        submitted = st.form_submit_button("Ingresar", use_container_width=True)
        if submitted:
            if str(pin_ingresado).strip() == str(admin_pin_secret).strip():
                st.session_state["is_admin_authenticated"] = True
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("PIN incorrecto. Intente nuevamente.")
    return False

def logout_admin():
    st.session_state["is_admin_authenticated"] = False
    st.rerun()
