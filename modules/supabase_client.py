"""Conexion segura y utilidades minimas para Supabase."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value or "").strip()


def supabase_configured() -> bool:
    return bool(_secret("SUPABASE_URL") and _secret("SUPABASE_SERVICE_ROLE_KEY"))


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Any:
    """Crea un cliente cacheado; las credenciales nunca se guardan en el repo."""
    if not supabase_configured():
        return None

    from supabase import create_client

    return create_client(
        _secret("SUPABASE_URL"),
        _secret("SUPABASE_SERVICE_ROLE_KEY"),
    )


def check_supabase_connection() -> tuple[bool, str]:
    """Comprueba red, credenciales y que exista el esquema inicial."""
    client = get_supabase_client()
    if client is None:
        return False, "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Secrets."

    try:
        response = client.table("productos").select("id", count="exact").limit(1).execute()
        if response.count is None:
            return False, "Supabase responde, pero no se pudo validar la tabla productos."
        return True, "Supabase conectado y esquema disponible."
    except Exception as exc:
        return False, f"Supabase no esta listo: {exc}"
