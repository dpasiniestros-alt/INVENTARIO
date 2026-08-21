#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de migración: copia datos de Google Sheets a Supabase.
Uso: python migrate_to_supabase.py
"""

import os
import sys
import json

# Asegura que el módulo esté en el path
sys.path.insert(0, os.path.dirname(__file__))

# Lee .streamlit/secrets.toml (desarrollo local)
import toml

secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

print(f"\nBuscando {secrets_path}...")

if os.path.exists(secrets_path):
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = toml.load(f)
            print("✓ secrets.toml cargado")
            
            # Extrae Supabase
            if "supabase" in secrets:
                os.environ["SUPABASE_URL"] = secrets["supabase"].get("SUPABASE_URL", "")
                os.environ["SUPABASE_SERVICE_ROLE_KEY"] = secrets["supabase"].get("SUPABASE_SERVICE_ROLE_KEY", "")
                print(f"  - SUPABASE_URL: {os.environ.get('SUPABASE_URL', '')[:30]}...")
                print(f"  - SUPABASE_SERVICE_ROLE_KEY: {os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')[:30]}...")
            else:
                print("⚠ No se encontró sección [supabase] en secrets.toml")
            
            # Extrae Google Cloud
            if "gcp_service_account" in secrets:
                os.environ["GCP_SERVICE_ACCOUNT"] = json.dumps(secrets["gcp_service_account"])
                print("  - GCP_SERVICE_ACCOUNT: configurado")
    except Exception as e:
        print(f"✗ Error leyendo {secrets_path}: {e}")
        sys.exit(1)
else:
    print(f"✗ No se encontró {secrets_path}")
    sys.exit(1)

# Simula un ambiente de Streamlit (necesario para gsheets)
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# Importa después de cargar variables de entorno
import streamlit as st

# Crea un contexto de secretos simulado para que los módulos los encuentren
class FakeSecrets:
    def __init__(self, env_vars):
        self._data = env_vars
    
    def get(self, key, default=""):
        if key in self._data:
            return self._data[key]
        return os.environ.get(key, default)
    
    def __contains__(self, key):
        return key in self._data or key in os.environ
    
    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        value = os.environ.get(key)
        if value is None:
            raise KeyError(key)
        return value

# Carga los datos para FakeSecrets
fake_secrets_data = {
    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
    "SUPABASE_SERVICE_ROLE_KEY": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
}

if "GCP_SERVICE_ACCOUNT" in os.environ:
    try:
        fake_secrets_data["gcp_service_account"] = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    except:
        pass

# Reemplaza st.secrets con nuestro fake
st.secrets = FakeSecrets(fake_secrets_data)

from modules.supabase_migration import run_migration

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Migración: Google Sheets → Supabase")
    print("="*60 + "\n")

    success = run_migration()
    
    if success:
        print("\n✓ Migración completada exitosamente.\n")
        sys.exit(0)
    else:
        print("\n✗ La migración falló. Verifica las conexiones.\n")
        sys.exit(1)
