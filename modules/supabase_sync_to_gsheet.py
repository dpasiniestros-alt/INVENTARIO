"""Sincronización: Supabase (fuente) → Google Sheets (informes)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd

from modules.supabase_client import get_supabase_client


def sync_remitos_to_gsheet(sb_client: Any, gsheets_inventario: Any) -> bool:
    """Sincroniza remitos desde Supabase a la hoja BASE_DATOS_REMITOS de Sheets."""
    try:
        # Lee remitos de Supabase
        response = sb_client.table("remitos").select("*").execute()
        remitos_data = response.data or []
        
        if not remitos_data:
            print("✓ No hay remitos para sincronizar a Sheets.")
            return True
        
        # Convierte a DataFrame
        df = pd.DataFrame(remitos_data)
        
        # Renombra columnas para compatibilidad con Sheets
        column_map = {
            'nro_remito': 'ID_REMITO',
            'fecha': 'FECHA',
            'hora': 'HORA',
            'responsable': 'RESPONSABLE',
            'tipo_remito': 'TIPO_REMITO',
            'articulo_principal': 'ARTICULO_PRINCIPAL',
            'marca': 'MARCA',
            'modelo': 'MODELO',
            'cantidad': 'CANTIDAD',
            'gerencia': 'GERENCIA',
            'patente': 'PATENTE',
            'receptor': 'RECEPTOR',
            'email_receptor': 'EMAIL_RECEPTOR',
            'region_edenor': 'REGION_EDENOR',
            'numero_factura': 'NUMERO_FACTURA',
            'foto_factura': 'FOTO_FACTURA',
            'observaciones': 'OBSERVACIONES',
            'estado': 'ESTADO',
            'fecha_procesamiento': 'FECHA_PROCESAMIENTO',
        }
        
        df = df.rename(columns=column_map)
        
        # Guarda en la hoja
        headers = list(column_map.values())
        values = [headers]
        for _, row in df.iterrows():
            values.append([row.get(h, "") for h in headers])
        
        sheet = gsheets_inventario.worksheet('BASE_DATOS_REMITOS')
        sheet.clear()
        sheet.update(range_name="A1", values=values)
        
        print(f"✓ Sincronizados {len(remitos_data)} remitos a Google Sheets.")
        return True
    except Exception as exc:
        print(f"✗ Error sincronizando remitos: {exc}")
        return False


def sync_productos_to_gsheet(sb_client: Any, gsheets_inventario: Any) -> bool:
    """Sincroniza productos desde Supabase a la hoja STOCK_PRODUCTOS de Sheets."""
    try:
        response = sb_client.table("productos").select("*").execute()
        productos_data = response.data or []
        
        if not productos_data:
            print("✓ No hay productos para sincronizar a Sheets.")
            return True
        
        df = pd.DataFrame(productos_data)
        
        column_map = {
            'id': 'ID',
            'categoria': 'Categoria',
            'marca': 'Marca',
            'modelo_detalle': 'Modelo_Detalle',
            'codigo_pieza': 'Codigo_Pieza',
            'stock_actual': 'Stock_Actual',
            'stock_minimo': 'Stock_Minimo',
            'unidad': 'Unidad',
            'requiere_serial': 'Requiere_Serial',
        }
        
        df = df.rename(columns=column_map)
        
        headers = list(column_map.values())
        values = [headers]
        for _, row in df.iterrows():
            values.append([row.get(h, "") for h in headers])
        
        sheet = gsheets_inventario.worksheet('STOCK_PRODUCTOS')
        sheet.clear()
        sheet.update(range_name="A1", values=values)
        
        print(f"✓ Sincronizados {len(productos_data)} productos a Google Sheets.")
        return True
    except Exception as exc:
        print(f"✗ Error sincronizando productos: {exc}")
        return False


def sync_unidades_to_gsheet(sb_client: Any, gsheets_inventario: Any) -> bool:
    """Sincroniza unidades serializadas desde Supabase a Sheets."""
    try:
        response = sb_client.table("unidades_serializadas").select("*").execute()
        unidades_data = response.data or []
        
        if not unidades_data:
            print("✓ No hay unidades para sincronizar a Sheets.")
            return True
        
        headers = [
            "Numero_Marcado", "Tipo_Articulo", "ID_Producto", "Marca",
            "Modelo_Medida", "Estado", "Vehiculo_Actual", 
            "Fecha_Ultimo_Movimiento", "Historial_JSON"
        ]
        
        values = [headers]
        for unit in unidades_data:
            row = [
                unit.get("numero_marcado", ""),
                unit.get("tipo_articulo", ""),
                unit.get("id_producto", ""),
                unit.get("marca", ""),
                unit.get("modelo_medida", ""),
                unit.get("estado", ""),
                unit.get("vehiculo_actual", ""),
                unit.get("fecha_ultimo_movimiento", ""),
                json.dumps(unit.get("historial", []), ensure_ascii=False),
            ]
            values.append(row)
        
        sheet = gsheets_inventario.worksheet('UNIDADES_SERIALIZADAS')
        sheet.clear()
        sheet.update(range_name="A1", values=values)
        
        print(f"✓ Sincronizadas {len(unidades_data)} unidades a Google Sheets.")
        return True
    except Exception as exc:
        print(f"✗ Error sincronizando unidades: {exc}")
        return False


def run_sync_to_gsheet() -> bool:
    """Ejecuta la sincronización completa de Supabase a Google Sheets."""
    sb_client = get_supabase_client()
    if sb_client is None:
        print("✗ No hay conexión a Supabase.")
        return False
    
    # Conecta a Google Sheets
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import streamlit as st
        
        if not hasattr(st, "secrets") or "gcp_service_account" not in st.secrets:
            print("✗ No hay credenciales de Google Cloud en Secrets.")
            return False
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gs_client = gspread.authorize(creds)
        
        # IDs de los Google Sheets
        inv_id = st.secrets.get("GSHEET_INVENTARIO_ID", "1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg")
        gsheets_inventario = gs_client.open_by_key(inv_id)
        
    except Exception as exc:
        print(f"✗ No se pudo conectar a Google Sheets: {exc}")
        return False
    
    print("\n=== Sincronizando Supabase → Google Sheets ===\n")
    
    success = True
    success &= sync_productos_to_gsheet(sb_client, gsheets_inventario)
    success &= sync_unidades_to_gsheet(sb_client, gsheets_inventario)
    success &= sync_remitos_to_gsheet(sb_client, gsheets_inventario)
    
    if success:
        print("\n✓ Sincronización completada.\n")
    else:
        print("\n✗ Hubo errores durante la sincronización.\n")
    
    return success
