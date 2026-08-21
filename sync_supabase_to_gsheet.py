#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de sincronización: Supabase → Google Sheets.
Ejecuta: python sync_supabase_to_gsheet.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

import toml

secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")

print(f"\nBuscando {secrets_path}...")

if os.path.exists(secrets_path):
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = toml.load(f)
            
            if "supabase" in secrets:
                os.environ["SUPABASE_URL"] = secrets["supabase"].get("SUPABASE_URL", "")
                os.environ["SUPABASE_SERVICE_ROLE_KEY"] = secrets["supabase"].get("SUPABASE_SERVICE_ROLE_KEY", "")
            
            if "gcp_service_account" in secrets:
                os.environ["GCP_SERVICE_ACCOUNT"] = json.dumps(secrets["gcp_service_account"])
            
            if "GSHEET_INVENTARIO_ID" in secrets:
                os.environ["GSHEET_INVENTARIO_ID"] = secrets["GSHEET_INVENTARIO_ID"]
    except Exception as e:
        print(f"✗ Error leyendo {secrets_path}: {e}")
        sys.exit(1)
else:
    print(f"✗ No se encontró {secrets_path}")
    sys.exit(1)

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

import streamlit as st

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

fake_secrets_data = {
    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
    "SUPABASE_SERVICE_ROLE_KEY": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
    "GSHEET_INVENTARIO_ID": os.environ.get("GSHEET_INVENTARIO_ID", "1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg"),
}

if "GCP_SERVICE_ACCOUNT" in os.environ:
    try:
        fake_secrets_data["gcp_service_account"] = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    except:
        pass

st.secrets = FakeSecrets(fake_secrets_data)

from modules.supabase_sync_to_gsheet import run_sync_to_gsheet

if __name__ == "__main__":
    success = run_sync_to_gsheet()
    sys.exit(0 if success else 1)
