"""Migración de datos de Google Sheets a Supabase (ejecución única)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from modules.gsheets_db import DatabaseManager as OldDatabaseManager
from modules.supabase_client import get_supabase_client


def migrate_productos(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra STOCK_PRODUCTOS de Sheets a Supabase."""
    df = gsheets_db.get_productos()
    if df.empty:
        print("No hay productos para migrar.")
        return 0

    try:
        for _, row in df.iterrows():
            sb_client.table("productos").upsert({
                "id": str(row.get("ID", "")),
                "categoria": str(row.get("Categoria", "")),
                "marca": str(row.get("Marca", "")),
                "modelo_detalle": str(row.get("Modelo_Detalle", "")),
                "codigo_pieza": str(row.get("Codigo_Pieza", "")),
                "stock_actual": int(row.get("Stock_Actual", 0)),
                "stock_minimo": int(row.get("Stock_Minimo", 0)),
                "unidad": str(row.get("Unidad", "UNIDAD")),
                "requiere_serial": bool(row.get("Requiere_Serial", False)),
            }).execute()
        count = len(df)
        print(f"✓ Migrados {count} productos.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando productos: {exc}")
        return 0


def migrate_unidades_serializadas(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra UNIDADES_SERIALIZADAS de Sheets a Supabase."""
    units = gsheets_db.get_unidades_seriales()
    if not units:
        print("No hay unidades para migrar.")
        return 0

    try:
        for unit in units:
            historial = unit.get("Historial", [])
            sb_client.table("unidades_serializadas").insert({
                "numero_marcado": str(unit.get("Numero_Marcado", "")),
                "tipo_articulo": str(unit.get("Tipo_Articulo", "")),
                "id_producto": str(unit.get("ID_Producto", "")),
                "marca": str(unit.get("Marca", "")),
                "modelo_medida": str(unit.get("Modelo_Medida", "")),
                "estado": str(unit.get("Estado", "EN STOCK")),
                "vehiculo_actual": str(unit.get("Vehiculo_Actual", "")),
                "fecha_ultimo_movimiento": unit.get("Fecha_Ultimo_Movimiento"),
                "historial": json.dumps(historial, ensure_ascii=False),
            }).execute()
        count = len(units)
        print(f"✓ Migradas {count} unidades serializadas.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando unidades: {exc}")
        return 0


def migrate_remitos(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra remitos de BASE_DATOS_REMITOS de Sheets a Supabase."""
    remitos_raw = gsheets_db.obtener_remitos_de_gsheet()
    if not remitos_raw:
        print("No hay remitos para migrar.")
        return 0

    try:
        for rem in remitos_raw:
            nro = rem.get("ID_REMITO", "")
            if not nro or nro in [r.get("nro_remito") for r in 
                                   sb_client.table("remitos").select("nro_remito").execute().data]:
                continue

            sb_client.table("remitos").insert({
                "nro_remito": nro,
                "fecha": rem.get("FECHA", ""),
                "hora": rem.get("HORA", ""),
                "responsable": rem.get("RESPONSABLE", ""),
                "tipo_remito": rem.get("TIPO_REMITO", ""),
                "articulo_principal": rem.get("ARTICULO_PRINCIPAL", ""),
                "marca": rem.get("MARCA", ""),
                "modelo": rem.get("MODELO", ""),
                "cantidad": rem.get("CANTIDAD", 0),
                "gerencia": rem.get("GERENCIA", ""),
                "patente": rem.get("PATENTE", ""),
                "receptor": rem.get("RECEPTOR", ""),
                "email_receptor": rem.get("EMAIL_RECEPTOR", ""),
                "region_edenor": rem.get("REGION_EDENOR", ""),
                "numero_factura": rem.get("NUMERO_FACTURA", ""),
                "foto_factura": rem.get("FOTO_FACTURA", ""),
                "observaciones": rem.get("OBSERVACIONES", ""),
                "estado": rem.get("ESTADO", "Procesado"),
                "fecha_procesamiento": rem.get("FECHA_PROCESAMIENTO", ""),
            }).execute()
        count = len(remitos_raw)
        print(f"✓ Migrados {count} remitos.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando remitos: {exc}")
        return 0


def migrate_remito_items(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra BASE_DATOS_REMITO_ITEMS de Sheets a Supabase."""
    items_df = gsheets_db.get_remito_items()
    if items_df.empty:
        print("No hay ítems de remitos para migrar.")
        return 0

    try:
        for _, row in items_df.iterrows():
            sb_client.table("remito_items").insert({
                "nro_remito": str(row.get("Nro_Remito", "")),
                "id_producto": str(row.get("ID_Producto", "")),
                "categoria": str(row.get("Categoria", "")),
                "marca": str(row.get("Marca", "")),
                "descripcion": str(row.get("Descripcion", "")),
                "codigo_pieza": str(row.get("Codigo_Pieza", "")),
                "cantidad": int(row.get("Cantidad", 0)),
                "numeros_seriales": str(row.get("Nro_Serie_Bateria_Neumatico", "")),
            }).execute()
        count = len(items_df)
        print(f"✓ Migrados {count} ítems de remitos.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando ítems de remitos: {exc}")
        return 0


def migrate_responsables(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra RESPONSABLES de Sheets a Supabase."""
    df = gsheets_db.get_responsables()
    if df.empty:
        print("No hay responsables para migrar.")
        return 0

    try:
        for _, row in df.iterrows():
            sb_client.table("responsables").upsert({
                "nombre": str(row.get("nombre", "")),
                "pin": str(row.get("pin", "1234")),
            }).execute()
        count = len(df)
        print(f"✓ Migrados {count} responsables.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando responsables: {exc}")
        return 0


def migrate_receptores(sb_client: Any, gsheets_db: OldDatabaseManager) -> int:
    """Migra RECEPTORES de Sheets a Supabase."""
    df = gsheets_db.get_receptores()
    if df.empty:
        print("No hay receptores para migrar.")
        return 0

    try:
        for _, row in df.iterrows():
            sb_client.table("receptores").upsert({
                "nombre": str(row.get("nombre", "")),
                "email": str(row.get("email", "")),
                "gerencia": str(row.get("gerencia", "")),
            }).execute()
        count = len(df)
        print(f"✓ Migrados {count} receptores.")
        return count
    except Exception as exc:
        print(f"✗ Error migrando receptores: {exc}")
        return 0


def run_migration() -> bool:
    """Ejecuta la migración completa."""
    sb_client = get_supabase_client()
    if sb_client is None:
        print("✗ No hay conexión a Supabase. Verifica los Secrets.")
        return False

    gsheets_db = OldDatabaseManager()
    if not gsheets_db.is_connected_gsheets:
        print("✗ No hay conexión a Google Sheets.")
        return False

    print("\n=== Iniciando migración de datos ===\n")

    total = 0
    total += migrate_productos(sb_client, gsheets_db)
    total += migrate_unidades_serializadas(sb_client, gsheets_db)
    total += migrate_responsables(sb_client, gsheets_db)
    total += migrate_receptores(sb_client, gsheets_db)
    total += migrate_remitos(sb_client, gsheets_db)
    total += migrate_remito_items(sb_client, gsheets_db)

    print(f"\n✓ Migración completada: {total} registros importados.\n")
    return True
