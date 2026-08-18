# -*- coding: utf-8 -*-
"""
Capa de Persistencia y Conexion con Google Sheets con Trazabilidad Individual de Baterias y Neumaticos.
"""

import os
import json
import datetime
import pandas as pd
import streamlit as st
from modules.catalog_seed import (
    GERENCIAS, RESPONSABLES_INICIALES, PATENTES_INICIALES, VEHICULOS_INICIALES, get_initial_products
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

def safe_secret(key, default=""):
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.spreadsheet_vehiculos = None
        self.spreadsheet_inventario = None
        self.spreadsheet_ordenes = None
        self.is_connected_gsheets = False
        self._init_connection()
        self._init_local_backup()

    def _init_connection(self):
        try:
            if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                self.client = gspread.authorize(creds)
                
                veh_id = safe_secret("GSHEET_VEHICULOS_ID", "1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU")
                if veh_id:
                    try:
                        self.spreadsheet_vehiculos = self.client.open_by_key(veh_id)
                    except Exception:
                        pass

                inv_id = safe_secret("GSHEET_INVENTARIO_ID", "1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg")
                if inv_id:
                    try:
                        self.spreadsheet_inventario = self.client.open_by_key(inv_id)
                    except Exception:
                        pass

                ord_id = safe_secret("GSHEET_ORDENES_ID", "1yR1k8wufRB108ZEekYaXkT8Q3GlfRKfMej3HDbWRjLY")
                if ord_id:
                    try:
                        self.spreadsheet_ordenes = self.client.open_by_key(ord_id)
                    except Exception:
                        pass

                if self.spreadsheet_vehiculos or self.spreadsheet_inventario or self.spreadsheet_ordenes:
                    self.is_connected_gsheets = True
        except Exception:
            self.is_connected_gsheets = False

    def _init_local_backup(self):
        prod_file = os.path.join(DATA_DIR, "stock_productos.json")
        if not os.path.exists(prod_file):
            with open(prod_file, "w", encoding="utf-8") as f:
                json.dump(get_initial_products(), f, ensure_ascii=False, indent=2)

        unit_file = os.path.join(DATA_DIR, "unidades_seriales.json")
        if not os.path.exists(unit_file):
            initial_units = [
                {
                    "Numero_Marcado": "1",
                    "Tipo_Articulo": "NEUMATICO",
                    "ID_Producto": "NEU-0037",
                    "Marca": "Pirelli",
                    "Modelo_Medida": "185/70R14",
                    "Estado": "EN STOCK",
                    "Vehiculo_Actual": "",
                    "Fecha_Ultimo_Movimiento": "2026-08-18",
                    "Historial": [
                        {"Fecha": "2026-08-18", "Tipo": "INGRESO", "Nro_Remito": "REM-E-0001", "Detalle": "Ingreso a stock inicial"}
                    ]
                },
                {
                    "Numero_Marcado": "32",
                    "Tipo_Articulo": "NEUMATICO",
                    "ID_Producto": "NEU-0037",
                    "Marca": "Pirelli",
                    "Modelo_Medida": "185/70R14",
                    "Estado": "EN STOCK",
                    "Vehiculo_Actual": "",
                    "Fecha_Ultimo_Movimiento": "2026-08-18",
                    "Historial": [
                        {"Fecha": "2026-08-18", "Tipo": "INGRESO", "Nro_Remito": "REM-E-0001", "Detalle": "Ingreso a stock inicial"}
                    ]
                },
                {
                    "Numero_Marcado": "52",
                    "Tipo_Articulo": "NEUMATICO",
                    "ID_Producto": "NEU-0037",
                    "Marca": "Pirelli",
                    "Modelo_Medida": "185/70R14",
                    "Estado": "EN STOCK",
                    "Vehiculo_Actual": "",
                    "Fecha_Ultimo_Movimiento": "2026-08-18",
                    "Historial": [
                        {"Fecha": "2026-08-18", "Tipo": "INGRESO", "Nro_Remito": "REM-E-0001", "Detalle": "Ingreso a stock inicial"}
                    ]
                },
                {
                    "Numero_Marcado": "4",
                    "Tipo_Articulo": "NEUMATICO",
                    "ID_Producto": "NEU-0037",
                    "Marca": "Pirelli",
                    "Modelo_Medida": "185/70R14",
                    "Estado": "EN STOCK",
                    "Vehiculo_Actual": "",
                    "Fecha_Ultimo_Movimiento": "2026-08-18",
                    "Historial": [
                        {"Fecha": "2026-08-18", "Tipo": "INGRESO", "Nro_Remito": "REM-E-0001", "Detalle": "Ingreso a stock inicial"}
                    ]
                },
                {
                    "Numero_Marcado": "BAT-101",
                    "Tipo_Articulo": "BATERIA",
                    "ID_Producto": "BAT-0001",
                    "Marca": "Moura",
                    "Modelo_Medida": "12V 75Ah",
                    "Estado": "EN STOCK",
                    "Vehiculo_Actual": "",
                    "Fecha_Ultimo_Movimiento": "2026-08-18",
                    "Historial": [
                        {"Fecha": "2026-08-18", "Tipo": "INGRESO", "Nro_Remito": "REM-E-0001", "Detalle": "Ingreso inicial"}
                    ]
                }
            ]
            with open(unit_file, "w", encoding="utf-8") as f:
                json.dump(initial_units, f, ensure_ascii=False, indent=2)

        veh_file = os.path.join(DATA_DIR, "vehiculos.json")
        if not os.path.exists(veh_file):
            veh_list = list(VEHICULOS_INICIALES)
            pats_existentes = {v["PATENTE"] for v in veh_list}
            for p in PATENTES_INICIALES:
                if p not in pats_existentes:
                    veh_list.append({
                        "PATENTE": p,
                        "AÑO": "2022",
                        "MARCA": "Flota",
                        "MODELO": "Vehículo Taller",
                        "GERENCIA": "GPS EDENOR",
                        "STATUS": "ACTIVO",
                        "FECHA DE BAJA": "",
                        "OBSERVACIONES": ""
                    })
            with open(veh_file, "w", encoding="utf-8") as f:
                json.dump(veh_list, f, ensure_ascii=False, indent=2)

        resp_file = os.path.join(DATA_DIR, "responsables.json")
        if not os.path.exists(resp_file):
            with open(resp_file, "w", encoding="utf-8") as f:
                json.dump(RESPONSABLES_INICIALES, f, ensure_ascii=False, indent=2)

        rec_file = os.path.join(DATA_DIR, "receptores.json")
        if not os.path.exists(rec_file):
            with open(rec_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        rem_file = os.path.join(DATA_DIR, "remitos.json")
        if not os.path.exists(rem_file):
            with open(rem_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        item_file = os.path.join(DATA_DIR, "remito_items.json")
        if not os.path.exists(item_file):
            with open(item_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

        ot_file = os.path.join(DATA_DIR, "ordenes_taller.json")
        if not os.path.exists(ot_file):
            initial_ots = [
                {
                    "Nro_OT": "OT-1001",
                    "Fecha": datetime.date.today().strftime("%Y-%m-%d"),
                    "Patente": "AF395XD",
                    "Gerencia": "GPS EDENOR",
                    "Descripcion_Trabajo": "Service Preventivo 10.000km + Cambio de Filtros",
                    "Estado": "Pendiente"
                }
            ]
            with open(ot_file, "w", encoding="utf-8") as f:
                json.dump(initial_ots, f, ensure_ascii=False, indent=2)

    def get_unidades_seriales(self) -> list:
        unit_file = os.path.join(DATA_DIR, "unidades_seriales.json")
        if not os.path.exists(unit_file):
            self._init_local_backup()
        with open(unit_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_unidades_seriales(self, units_list: list):
        unit_file = os.path.join(DATA_DIR, "unidades_seriales.json")
        with open(unit_file, "w", encoding="utf-8") as f:
            json.dump(units_list, f, ensure_ascii=False, indent=2)

    def get_unidades_disponibles(self, tipo_articulo: str, marca: str = None, modelo: str = None) -> list:
        units = self.get_unidades_seriales()
        res = []
        for u in units:
            if u.get("Estado") == "EN STOCK" and u.get("Tipo_Articulo") == tipo_articulo:
                if marca and u.get("Marca", "").lower() != marca.lower():
                    continue
                if modelo and u.get("Modelo_Medida", "").lower() != modelo.lower():
                    continue
                res.append(str(u.get("Numero_Marcado")))
        return sorted(list(set(res)))

    def get_unidades_en_vehiculo(self, patente: str) -> list:
        units = self.get_unidades_seriales()
        res = []
        p_clean = patente.strip().upper()
        for u in units:
            if u.get("Estado") == "EN VEHICULO":
                v_act = str(u.get("Vehiculo_Actual", "")).upper()
                if p_clean in v_act:
                    res.append(u)
        return res

    def registrar_ingreso_unidad(self, numero_marcado: str, tipo_articulo: str, marca: str, modelo_medida: str, id_producto: str, nro_remito: str, responsable: str, vehiculo_origen: str = ""):
        numero_marcado = str(numero_marcado).strip()
        if not numero_marcado:
            return
        units = self.get_unidades_seriales()
        fecha_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        found = False
        for u in units:
            if str(u.get("Numero_Marcado")).strip().lower() == numero_marcado.lower() and u.get("Tipo_Articulo") == tipo_articulo:
                u["Estado"] = "EN STOCK"
                u["Vehiculo_Actual"] = ""
                u["Fecha_Ultimo_Movimiento"] = fecha_now
                det = f"Reingreso a stock desde vehículo {vehiculo_origen}" if vehiculo_origen else "Reingreso a stock de taller"
                u["Historial"].append({
                    "Fecha": fecha_now,
                    "Tipo": "REINGRESO",
                    "Nro_Remito": nro_remito,
                    "Responsable": responsable,
                    "Detalle": det
                })
                found = True
                break

        if not found:
            new_unit = {
                "Numero_Marcado": numero_marcado,
                "Tipo_Articulo": tipo_articulo,
                "ID_Producto": id_producto,
                "Marca": marca,
                "Modelo_Medida": modelo_medida,
                "Estado": "EN STOCK",
                "Vehiculo_Actual": "",
                "Fecha_Ultimo_Movimiento": fecha_now,
                "Historial": [
                    {
                        "Fecha": fecha_now,
                        "Tipo": "INGRESO_NUEVO",
                        "Nro_Remito": nro_remito,
                        "Responsable": responsable,
                        "Detalle": f"Alta en inventario de taller ({marca} - {modelo_medida})"
                    }
                ]
            }
            units.append(new_unit)

        self.save_unidades_seriales(units)

    def registrar_salida_unidad(self, numero_marcado: str, tipo_articulo: str, vehiculo_destino: str, receptor: str, responsable: str, nro_remito: str, gerencia: str = ""):
        numero_marcado = str(numero_marcado).strip()
        units = self.get_unidades_seriales()
        fecha_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for u in units:
            if str(u.get("Numero_Marcado")).strip().lower() == numero_marcado.lower() and u.get("Tipo_Articulo") == tipo_articulo:
                u["Estado"] = "EN VEHICULO"
                u["Vehiculo_Actual"] = vehiculo_destino
                u["Fecha_Ultimo_Movimiento"] = fecha_now
                u["Historial"].append({
                    "Fecha": fecha_now,
                    "Tipo": "SALIDA / INSTALACION",
                    "Nro_Remito": nro_remito,
                    "Vehiculo": vehiculo_destino,
                    "Receptor": receptor,
                    "Responsable": responsable,
                    "Gerencia": gerencia,
                    "Detalle": f"Instalado / entregado al vehículo {vehiculo_destino}"
                })
                break
        self.save_unidades_seriales(units)

    def registrar_traspaso_unidad(self, numero_marcado: str, tipo_articulo: str, veh_origen: str, veh_destino: str, responsable: str, receptor: str, nro_remito: str, observaciones: str = ""):
        numero_marcado = str(numero_marcado).strip()
        units = self.get_unidades_seriales()
        fecha_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for u in units:
            if str(u.get("Numero_Marcado")).strip().lower() == numero_marcado.lower() and u.get("Tipo_Articulo") == tipo_articulo:
                u["Estado"] = "EN VEHICULO"
                u["Vehiculo_Actual"] = veh_destino
                u["Fecha_Ultimo_Movimiento"] = fecha_now
                u["Historial"].append({
                    "Fecha": fecha_now,
                    "Tipo": "TRASPASO DIRECTO",
                    "Nro_Remito": nro_remito,
                    "Vehiculo_Origen": veh_origen,
                    "Vehiculo_Destino": veh_destino,
                    "Responsable": responsable,
                    "Receptor": receptor,
                    "Detalle": f"Traspaso directo desde {veh_origen} hacia {veh_destino}. {observaciones}".strip()
                })
                break
        self.save_unidades_seriales(units)

    def buscar_historial_unidad(self, numero_marcado: str) -> dict:
        numero_marcado = str(numero_marcado).strip().lower()
        units = self.get_unidades_seriales()
        for u in units:
            if str(u.get("Numero_Marcado")).strip().lower() == numero_marcado:
                return u
        return None

    def get_vehiculos(self, solo_activos: bool = False) -> pd.DataFrame:
        df = None
        if self.is_connected_gsheets and self.spreadsheet_vehiculos:
            for sheet_name in ["VEHICULO", "Vehiculos", "Patentes"]:
                try:
                    sheet = self.spreadsheet_vehiculos.worksheet(sheet_name)
                    data = sheet.get_all_records()
                    if data:
                        df = pd.DataFrame(data)
                        break
                except Exception:
                    pass
        if df is None or df.empty:
            veh_file = os.path.join(DATA_DIR, "vehiculos.json")
            with open(veh_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)

        cols_map = {}
        for col in df.columns:
            c_clean = str(col).strip().upper()
            if "PATENTE" in c_clean or "DOMINIO" in c_clean:
                cols_map[col] = "PATENTE"
            elif "AÑO" in c_clean or "ANIO" in c_clean or "YEAR" in c_clean:
                cols_map[col] = "AÑO"
            elif "MARCA" in c_clean:
                cols_map[col] = "MARCA"
            elif "MODELO" in c_clean:
                cols_map[col] = "MODELO"
            elif "GERENCIA" in c_clean or "SERVICIO" in c_clean:
                cols_map[col] = "GERENCIA"
            elif "STATUS" in c_clean or "ESTADO" in c_clean:
                cols_map[col] = "STATUS"
            elif "BAJA" in c_clean:
                cols_map[col] = "FECHA DE BAJA"
        
        if cols_map:
            df.rename(columns=cols_map, inplace=True)

        for req in ["PATENTE", "AÑO", "MARCA", "MODELO", "GERENCIA", "STATUS", "FECHA DE BAJA"]:
            if req not in df.columns:
                df[req] = ""

        def format_veh_label(row):
            pat = str(row["PATENTE"]).strip().upper()
            ano = str(row.get("AÑO", "")).strip()
            marca = str(row.get("MARCA", "")).strip()
            mod = str(row.get("MODELO", "")).strip()
            desc = " ".join([p for p in [ano, marca, mod] if p and p != "nan" and p != "-"]).strip()
            if desc:
                return f"[{pat}] {desc}"
            return f"[{pat}]"

        df["ETIQUETA_COMPLETA"] = df.apply(format_veh_label, axis=1)

        if solo_activos and "STATUS" in df.columns:
            df = df[df["STATUS"].astype(str).str.upper().str.contains("ACTIVO", na=False)]

        return df

    def add_vehiculo_si_no_existe(self, patente: str, gerencia: str = "", ano: str = "", marca: str = "", modelo: str = ""):
        patente = patente.strip().upper()
        if not patente:
            return
        df = self.get_vehiculos(solo_activos=False)
        if patente not in df["PATENTE"].values:
            nuevo = {
                "PATENTE": patente,
                "AÑO": ano,
                "MARCA": marca,
                "MODELO": modelo,
                "GERENCIA": gerencia,
                "STATUS": "ACTIVO",
                "FECHA DE BAJA": "",
                "OBSERVACIONES": "Agregado desde Remito"
            }
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            self.save_vehiculos(df)

    def save_vehiculos(self, df: pd.DataFrame):
        df_save = df.copy()
        if "ETIQUETA_COMPLETA" in df_save.columns:
            df_save.drop(columns=["ETIQUETA_COMPLETA"], inplace=True)

        veh_file = os.path.join(DATA_DIR, "vehiculos.json")
        with open(veh_file, "w", encoding="utf-8") as f:
            json.dump(df_save.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    def get_ordenes_taller(self, solo_pendientes: bool = False, patente_filtro: str = None) -> pd.DataFrame:
        df = None
        if self.is_connected_gsheets and self.spreadsheet_vehiculos:
            for sname in ["COORDINACION DE ENVIO A TALLER", "Ordenes_Taller", "Solicitudes_Taller"]:
                try:
                    sheet = self.spreadsheet_vehiculos.worksheet(sname)
                    data = sheet.get_all_records()
                    if data:
                        df = pd.DataFrame(data)
                        break
                except Exception:
                    pass

        if df is None or df.empty:
            ot_file = os.path.join(DATA_DIR, "ordenes_taller.json")
            with open(ot_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)

        cols_norm = {}
        for c in df.columns:
            cl = str(c).strip().upper()
            if "ORDEN" in cl or "OT" in cl or "NRO" in cl:
                cols_norm[c] = "Nro_OT"
            elif "FALLA" in cl or "REPORTE" in cl or "TRABAJO" in cl or "DESCRIPCION" in cl:
                cols_norm[c] = "Descripcion_Trabajo"
            elif "PATENTE" in cl or "DOMINIO" in cl:
                cols_norm[c] = "Patente"
            elif "ESTADO" in cl or "STATUS" in cl:
                cols_norm[c] = "Estado"
            elif "GERENCIA" in cl:
                cols_norm[c] = "Gerencia"

        if cols_norm:
            df.rename(columns=cols_norm, inplace=True)

        for req in ["Nro_OT", "Descripcion_Trabajo", "Patente", "Estado", "Gerencia", "Fecha"]:
            if req not in df.columns:
                df[req] = ""

        if solo_pendientes and "Estado" in df.columns:
            df = df[~df["Estado"].astype(str).str.upper().isin(["COMPLETADA", "FINALIZADA", "CERRADA"])]

        if patente_filtro and not df.empty:
            p_clean = patente_filtro.strip().upper()
            df = df[df["Patente"].astype(str).str.upper().str.contains(p_clean, na=False)]

        return df

    def get_productos(self) -> pd.DataFrame:
        df = None
        if self.is_connected_gsheets and self.spreadsheet_inventario:
            for sname in ["Stock_Productos", "INVENTARIO", "Stock"]:
                try:
                    sheet = self.spreadsheet_inventario.worksheet(sname)
                    data = sheet.get_all_records()
                    if data:
                        df = pd.DataFrame(data)
                        break
                except Exception:
                    pass

        if df is None or df.empty:
            prod_file = os.path.join(DATA_DIR, "stock_productos.json")
            with open(prod_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)

        if "Stock_Actual" in df.columns:
            df["Stock_Actual"] = pd.to_numeric(df["Stock_Actual"], errors="coerce").fillna(0).astype(int)
        return df

    def save_productos(self, df: pd.DataFrame):
        data = df.to_dict(orient="records")
        prod_file = os.path.join(DATA_DIR, "stock_productos.json")
        with open(prod_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_or_update_producto(self, producto_dict: dict):
        df = self.get_productos()
        match = df[df["ID"] == producto_dict["ID"]]
        if not match.empty:
            for k, v in producto_dict.items():
                df.loc[df["ID"] == producto_dict["ID"], k] = v
        else:
            new_row = pd.DataFrame([producto_dict])
            df = pd.concat([df, new_row], ignore_index=True)
        self.save_productos(df)

    def update_stock(self, producto_id: str, cantidad: int, operacion: str = "salida") -> bool:
        df = self.get_productos()
        idx = df.index[df["ID"] == producto_id].tolist()
        if not idx:
            return False
        row_idx = idx[0]
        actual = int(df.at[row_idx, "Stock_Actual"])
        if operacion == "salida":
            if actual < cantidad:
                return False
            nuevo = actual - cantidad
        elif operacion == "entrada":
            nuevo = actual + cantidad
        else:
            nuevo = actual
        df.at[row_idx, "Stock_Actual"] = int(nuevo)
        self.save_productos(df)
        return True

    def get_responsables(self) -> pd.DataFrame:
        resp_file = os.path.join(DATA_DIR, "responsables.json")
        with open(resp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def add_responsable(self, nombre: str, pin: str = "1234"):
        df = self.get_responsables()
        if nombre not in df["nombre"].values:
            df = pd.concat([df, pd.DataFrame([{"nombre": nombre, "pin": pin}])], ignore_index=True)
            resp_file = os.path.join(DATA_DIR, "responsables.json")
            with open(resp_file, "w", encoding="utf-8") as f:
                json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    def get_receptores(self) -> pd.DataFrame:
        rec_file = os.path.join(DATA_DIR, "receptores.json")
        with open(rec_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def save_receptores(self, df: pd.DataFrame):
        rec_file = os.path.join(DATA_DIR, "receptores.json")
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    def add_or_update_receptor(self, nombre: str, email: str, gerencia: str):
        df = self.get_receptores()
        if df.empty:
            df = pd.DataFrame([{"nombre": nombre, "email": email, "gerencia": gerencia}])
        else:
            match = df[df["nombre"].str.lower() == nombre.lower()]
            if not match.empty:
                df.loc[df["nombre"].str.lower() == nombre.lower(), "email"] = email
                df.loc[df["nombre"].str.lower() == nombre.lower(), "gerencia"] = gerencia
            else:
                df = pd.concat([df, pd.DataFrame([{"nombre": nombre, "email": email, "gerencia": gerencia}])], ignore_index=True)
        self.save_receptores(df)

    def get_proximo_numero_remito(self, tipo: str) -> str:
        t_clean = tipo.upper()
        if "ENTRADA" in t_clean:
            prefix = "REM-E"
        elif "TRASPASO" in t_clean:
            prefix = "REM-T"
        else:
            prefix = "REM-S"

        df = self.get_remitos()
        if df.empty or "Nro_Remito" not in df.columns:
            return f"{prefix}-0001"
        filt = df[df["Nro_Remito"].astype(str).str.startswith(prefix, na=False)]
        if filt.empty:
            return f"{prefix}-0001"
        try:
            nums = filt["Nro_Remito"].apply(lambda x: int(str(x).split("-")[-1]) if "-" in str(x) else 0)
            next_num = nums.max() + 1
            return f"{prefix}-{next_num:04d}"
        except Exception:
            return f"{prefix}-{len(filt)+1:04d}"

    def get_remitos(self) -> pd.DataFrame:
        rem_file = os.path.join(DATA_DIR, "remitos.json")
        with open(rem_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data)

    def get_remito_items(self, nro_remito: str = None) -> pd.DataFrame:
        item_file = os.path.join(DATA_DIR, "remito_items.json")
        with open(item_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        if nro_remito and not df.empty and "Nro_Remito" in df.columns:
            return df[df["Nro_Remito"] == nro_remito]
        return df

    def guardar_remito(self, remito_header: dict, items: list) -> bool:
        df_rem = self.get_remitos()
        df_rem = pd.concat([df_rem, pd.DataFrame([remito_header])], ignore_index=True)
        rem_file = os.path.join(DATA_DIR, "remitos.json")
        with open(rem_file, "w", encoding="utf-8") as f:
            json.dump(df_rem.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

        df_items = self.get_remito_items()
        df_items = pd.concat([df_items, pd.DataFrame(items)], ignore_index=True)
        item_file = os.path.join(DATA_DIR, "remito_items.json")
        with open(item_file, "w", encoding="utf-8") as f:
            json.dump(df_items.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

        tipo_rem = remito_header.get("Tipo", "SALIDA").upper()
        nro_remito = remito_header.get("Nro_Remito", "")
        responsable = remito_header.get("Responsable_Entrega", "")
        receptor = remito_header.get("Receptor_Nombre", "")
        vehiculo = remito_header.get("Patente", "")
        gerencia = remito_header.get("Gerencia", "")

        for it in items:
            cat = it.get("Categoria", "")
            cant = int(it.get("Cantidad", 1))
            seriales = str(it.get("Nro_Serie_Bateria_Neumatico", "")).split(",")

            if "ENTRADA" in tipo_rem:
                self.update_stock(it["ID_Producto"], cant, operacion="entrada")
                if cat in ["BATERIA", "NEUMATICO"]:
                    for s in seriales:
                        s_clean = s.strip()
                        if s_clean and s_clean != "-":
                            self.registrar_ingreso_unidad(
                                numero_marcado=s_clean,
                                tipo_articulo=cat,
                                marca=it.get("Marca", ""),
                                modelo_medida=it.get("Descripcion", ""),
                                id_producto=it.get("ID_Producto", ""),
                                nro_remito=nro_remito,
                                responsable=responsable,
                                vehiculo_origen=vehiculo
                            )

            elif "SALIDA" in tipo_rem:
                self.update_stock(it["ID_Producto"], cant, operacion="salida")
                if cat in ["BATERIA", "NEUMATICO"]:
                    for s in seriales:
                        s_clean = s.strip()
                        if s_clean and s_clean != "-":
                            self.registrar_salida_unidad(
                                numero_marcado=s_clean,
                                tipo_articulo=cat,
                                vehiculo_destino=vehiculo,
                                receptor=receptor,
                                responsable=responsable,
                                nro_remito=nro_remito,
                                gerencia=gerencia
                            )

            elif "TRASPASO" in tipo_rem:
                veh_origen = remito_header.get("Vehiculo_Origen", "")
                veh_destino = remito_header.get("Patente", "")
                if cat in ["BATERIA", "NEUMATICO"]:
                    for s in seriales:
                        s_clean = s.strip()
                        if s_clean and s_clean != "-":
                            self.registrar_traspaso_unidad(
                                numero_marcado=s_clean,
                                tipo_articulo=cat,
                                veh_origen=veh_origen,
                                veh_destino=veh_destino,
                                responsable=responsable,
                                receptor=receptor,
                                nro_remito=nro_remito,
                                observaciones=remito_header.get("Observaciones", "")
                            )

        if remito_header.get("Receptor_Nombre") and "SALIDA" in tipo_rem:
            self.add_or_update_receptor(
                remito_header["Receptor_Nombre"],
                remito_header.get("Receptor_Email", ""),
                remito_header.get("Gerencia", "")
            )

        return True

    def mark_remito_email_sent(self, nro_remito: str):
        df = self.get_remitos()
        if not df.empty and "Nro_Remito" in df.columns:
            df.loc[df["Nro_Remito"] == nro_remito, "Enviado_Email"] = "SI"
            rem_file = os.path.join(DATA_DIR, "remitos.json")
            with open(rem_file, "w", encoding="utf-8") as f:
                json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

def get_db():
    return DatabaseManager()