"""Conexion segura y utilidades minimas para Supabase."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st


def _coalesce(*values):
    for value in values:
        if value is not None and str(value).strip() not in ("", "None"):
            return value
    return ""


def _secret(name: str, default: str = "") -> str:
    value = default
    try:
        if hasattr(st, "secrets"):
            value = _coalesce(st.secrets.get(name), st.secrets.get(name.lower()), st.secrets.get(name.upper()))
            if value == "":
                supabase_secrets = st.secrets.get("supabase", {})
                if isinstance(supabase_secrets, dict):
                    value = _coalesce(supabase_secrets.get(name), supabase_secrets.get(name.lower()), supabase_secrets.get(name.upper()))
    except Exception:
        value = default

    if value == "":
        value = _coalesce(
            os.getenv(name),
            os.getenv(name.upper()),
            os.getenv(name.lower()),
            os.getenv(f"STREAMLIT_SECRET_{name.upper()}"),
            os.getenv(f"STREAMLIT_SECRET_{name.lower()}"),
        )

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


def refresh_supabase_client() -> Any:
    """Descarta el cliente cacheado después de una suspensión o fallo de red."""
    get_supabase_client.clear()
    return get_supabase_client()


def check_supabase_connection() -> tuple[bool, str]:
    """Comprueba red, credenciales y que exista el esquema inicial."""
    client = get_supabase_client()
    if client is None:
        return False, "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Secrets."

    try:
        client.table("productos").select("id", count="exact").limit(1).execute()
        client.table("remitos").select("nro_remito,nro_orden_taller,vehiculo_origen,link_pdf").limit(1).execute()
        return True, "Supabase conectado y esquema disponible."
    except Exception as exc:
        return False, f"Supabase no esta listo o falta actualizar el esquema: {exc}"
