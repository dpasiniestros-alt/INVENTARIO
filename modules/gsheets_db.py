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

    def _web_sheet(self, title: str, headers: list):
        """Obtiene o crea una hoja auxiliar dentro del libro de inventario."""
        if not self.spreadsheet_inventario or not self.is_connected_gsheets:
            raise RuntimeError("Google Sheets no está conectado")
        try:
            sheet = self.spreadsheet_inventario.worksheet(title)
        except Exception:
            sheet = self.spreadsheet_inventario.add_worksheet(title=title, rows=1000, cols=max(20, len(headers)))
            sheet.append_row(headers)
        if not sheet.row_values(1):
            sheet.append_row(headers)
        return sheet

    def _sheet_dataframe(self, title: str, headers: list) -> pd.DataFrame:
        sheet = self._web_sheet(title, headers)
        try:
            # get_all_records falla si la hoja tiene encabezados repetidos o
            # restos de una creacion incompleta. Los valores crudos no tienen
            # esa restriccion y permiten reconstruir las columnas esperadas.
            values = sheet.get_all_values()
            if len(values) <= 1:
                return pd.DataFrame(columns=headers)
            rows = []
            for values_row in values[1:]:
                padded = list(values_row) + [""] * max(0, len(headers) - len(values_row))
                rows.append(padded[:len(headers)])
            return pd.DataFrame(rows, columns=headers)
        except Exception as exc:
            print(f"Error leyendo la hoja {title}: {exc}")
            return pd.DataFrame(columns=headers)

    def _save_sheet_dataframe(self, title: str, headers: list, df: pd.DataFrame):
        sheet = self._web_sheet(title, headers)
        self._save_sheet_dataframe_external(sheet, headers, df)

    def _save_sheet_dataframe_external(self, sheet, headers: list, df: pd.DataFrame):
        values = [headers]
        for record in df.reindex(columns=headers, fill_value="").fillna("").to_dict(orient="records"):
            values.append([record.get(header, "") for header in headers])
        sheet.clear()
        sheet.update(range_name="A1", values=values)

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
        return

        # Código histórico de respaldo local conservado temporalmente debajo.
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
        headers = ["Numero_Marcado", "Tipo_Articulo", "ID_Producto", "Marca", "Modelo_Medida", "Estado", "Vehiculo_Actual", "Fecha_Ultimo_Movimiento", "Historial_JSON"]
        df = self._sheet_dataframe("UNIDADES_SERIALIZADAS", headers)
        units = []
        for row in df.to_dict(orient="records"):
            row["Historial"] = json.loads(row.pop("Historial_JSON", "[]") or "[]")
            units.append(row)
        return units

    def save_unidades_seriales(self, units_list: list):
        headers = ["Numero_Marcado", "Tipo_Articulo", "ID_Producto", "Marca", "Modelo_Medida", "Estado", "Vehiculo_Actual", "Fecha_Ultimo_Movimiento", "Historial_JSON"]
        rows = []
        for unit in units_list:
            row = dict(unit)
            row["Historial_JSON"] = json.dumps(row.pop("Historial", []), ensure_ascii=False)
            rows.append(row)
        self._save_sheet_dataframe("UNIDADES_SERIALIZADAS", headers, pd.DataFrame(rows))

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
            for sheet_name in ["VEHICULOS", "VEHICULO", "Vehiculos", "Patentes"]:
                try:
                    sheet = self.spreadsheet_vehiculos.worksheet(sheet_name)
                    values = sheet.get_all_values()
                    if len(values) > 1:
                        headers = [str(value).strip() for value in values[0]]
                        rows = []
                        for values_row in values[1:]:
                            padded = list(values_row) + [""] * max(0, len(headers) - len(values_row))
                            rows.append(padded[:len(headers)])
                        df = pd.DataFrame(rows, columns=headers)
                        break
                except Exception:
                    pass
        if df is None:
            df = pd.DataFrame(columns=["PATENTE", "AÑO", "MARCA", "MODELO", "GERENCIA", "STATUS", "FECHA DE BAJA"])

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

        # La hoja VEHICULOS tiene varias columnas repetidas (STATUS, GERENCIA,
        # etc.). Consolidarlas evita que pandas devuelva un DataFrame al pedir
        # una columna y permite usar siempre el primer dato no vacio.
        if df.columns.duplicated().any():
            consolidated = {}
            for column in dict.fromkeys(df.columns):
                same_columns = df.loc[:, df.columns == column]
                if same_columns.shape[1] == 1:
                    consolidated[column] = same_columns.iloc[:, 0]
                else:
                    consolidated[column] = same_columns.replace("", pd.NA).bfill(axis=1).iloc[:, 0].fillna("")
            df = pd.DataFrame(consolidated, index=df.index)

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
        # El libro DPA PARQUE Automotor es solo lectura para esta aplicación.
        return False

    def save_vehiculos(self, df: pd.DataFrame):
        return False

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

        if df is None:
            df = pd.DataFrame()

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
        headers = ["ID", "Categoria", "Marca", "Modelo_Detalle", "Codigo_Pieza", "Stock_Actual", "Stock_Minimo", "Unidad", "Requiere_Serial"]
        df = self._sheet_dataframe("STOCK_PRODUCTOS", headers)
        if df.empty:
            df = pd.DataFrame(get_initial_products())
            self.save_productos(df)

        if "Stock_Actual" in df.columns:
            df["Stock_Actual"] = pd.to_numeric(df["Stock_Actual"], errors="coerce").fillna(0).astype(int)
        if "Stock_Minimo" in df.columns:
            df["Stock_Minimo"] = pd.to_numeric(df["Stock_Minimo"], errors="coerce").fillna(0).astype(int)
        return df

    def save_productos(self, df: pd.DataFrame):
        headers = ["ID", "Categoria", "Marca", "Modelo_Detalle", "Codigo_Pieza", "Stock_Actual", "Stock_Minimo", "Unidad", "Requiere_Serial"]
        self._save_sheet_dataframe("STOCK_PRODUCTOS", headers, df)

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
        headers = ["nombre", "pin"]
        df = self._sheet_dataframe("RESPONSABLES", headers)
        if df.empty:
            df = pd.DataFrame(RESPONSABLES_INICIALES)
            try:
                self._save_sheet_dataframe("RESPONSABLES", headers, df)
            except Exception as exc:
                print(f"Error inicializando RESPONSABLES: {exc}")
        return df

    def add_responsable(self, nombre: str, pin: str = "1234"):
        df = self.get_responsables()
        if nombre not in df["nombre"].values:
            df = pd.concat([df, pd.DataFrame([{"nombre": nombre, "pin": pin}])], ignore_index=True)
            self._save_sheet_dataframe("RESPONSABLES", ["nombre", "pin"], df)

    def get_receptores(self) -> pd.DataFrame:
        return self._sheet_dataframe("RECEPTORES", ["nombre", "email", "gerencia"])

    def save_receptores(self, df: pd.DataFrame):
        self._save_sheet_dataframe("RECEPTORES", ["nombre", "email", "gerencia"], df)

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
        sheet_rows = self.obtener_remitos_de_gsheet()
        imported = []
        for row in sheet_rows:
            tipo = str(row.get("TIPO_REMITO", "SALIDA")).upper()
            imported.append({
                    "Nro_Remito": row.get("ID_REMITO", ""),
                    "Tipo": tipo,
                    "Fecha_Hora": f"{row.get('FECHA', '')} {row.get('HORA', '')}".strip(),
                    "Responsable_Entrega": row.get("RESPONSABLE", ""),
                    "Receptor_Nombre": row.get("RECEPTOR", ""),
                    "Receptor_Email": row.get("EMAIL_RECEPTOR", ""),
                    "Gerencia": row.get("GERENCIA", ""),
                    "Patente": row.get("PATENTE", ""),
                    "Articulo_Principal": row.get("ARTICULO_PRINCIPAL", ""),
                    "Marca": row.get("MARCA", ""),
                    "Modelo": row.get("MODELO", ""),
                    "Cantidad": row.get("CANTIDAD", ""),
                    "Observaciones": row.get("OBSERVACIONES", ""),
                    "Numero_Factura": row.get("NUMERO_FACTURA", ""),
                    "Foto_Factura": row.get("FOTO_FACTURA", ""),
                    "Link_PDF": "",
                    "Enviado_Email": "NO",
                })
        return pd.DataFrame(imported)

    def get_remito_items(self, nro_remito: str = None) -> pd.DataFrame:
        headers = ["Nro_Remito", "ID_Producto", "Categoria", "Marca", "Descripcion", "Codigo_Pieza", "Cantidad", "Nro_Serie_Bateria_Neumatico"]
        df = self._sheet_dataframe("BASE_DATOS_REMITO_ITEMS", headers)
        if nro_remito and not df.empty and "Nro_Remito" in df.columns:
            return df[df["Nro_Remito"] == nro_remito]
        return df

    def guardar_remito(self, remito_header: dict, items: list) -> bool:
        if not self.is_connected_gsheets:
            return False
        item_headers = ["Nro_Remito", "ID_Producto", "Categoria", "Marca", "Descripcion", "Codigo_Pieza", "Cantidad", "Nro_Serie_Bateria_Neumatico"]
        item_sheet = self._web_sheet("BASE_DATOS_REMITO_ITEMS", item_headers)
        for item in items:
            item_sheet.append_row([item.get(header, "") for header in item_headers])

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

    def reiniciar_datos_operativos(self) -> bool:
        """Deja el inventario operativo en cero sin borrar catalogo ni flota."""
        if not self.is_connected_gsheets:
            return False
        try:
            productos = self.get_productos()
            if not productos.empty:
                productos["Stock_Actual"] = 0
                self.save_productos(productos)

            unidades_headers = ["Numero_Marcado", "Tipo_Articulo", "ID_Producto", "Marca", "Modelo_Medida", "Estado", "Vehiculo_Actual", "Fecha_Ultimo_Movimiento", "Historial_JSON"]
            self._save_sheet_dataframe("UNIDADES_SERIALIZADAS", unidades_headers, pd.DataFrame(columns=unidades_headers))

            remitos_headers = [
                "ID_REMITO", "FECHA", "HORA", "RESPONSABLE", "TIPO_REMITO", "ARTICULO_PRINCIPAL",
                "MARCA", "MODELO", "CANTIDAD", "GERENCIA", "PATENTE", "RECEPTOR", "EMAIL_RECEPTOR",
                "REGION_EDENOR", "NUMERO_FACTURA", "FOTO_FACTURA", "OBSERVACIONES", "ESTADO", "FECHA_PROCESAMIENTO"
            ]
            self._save_sheet_dataframe("BASE_DATOS_REMITOS", remitos_headers, pd.DataFrame(columns=remitos_headers))

            items_headers = ["Nro_Remito", "ID_Producto", "Categoria", "Marca", "Descripcion", "Codigo_Pieza", "Cantidad", "Nro_Serie_Bateria_Neumatico"]
            self._save_sheet_dataframe("BASE_DATOS_REMITO_ITEMS", items_headers, pd.DataFrame(columns=items_headers))
            return True
        except Exception as exc:
            print(f"Error reiniciando datos operativos: {exc}")
            return False

    def mark_remito_email_sent(self, nro_remito: str):
        if not self.spreadsheet_inventario:
            return
        sheet = self.spreadsheet_inventario.worksheet("BASE_DATOS_REMITOS")
        headers = sheet.row_values(1)
        if "ESTADO" in headers:
            id_col = headers.index("ID_REMITO") + 1
            status_col = headers.index("ESTADO") + 1
            for row_idx, value in enumerate(sheet.col_values(id_col)[1:], start=2):
                if value == nro_remito:
                    sheet.update_cell(row_idx, status_col, "Email enviado")
                    break

    def guardar_remito_en_gsheet(self, remito_data: dict, numero_factura: str = "", foto_factura_url: str = "") -> bool:
        """
        Guarda un remito en la hoja BASE_DATOS_REMITOS del LIBRO Inventario/Remitos.
        
        Parámetros:
        - remito_data: dict con los datos del remito
        - numero_factura: str con el número de factura (solo para ENTRADA)
        - foto_factura_url: str con la URL de la foto (solo para ENTRADA)
        
        Retorna: True si fue exitoso, False si no
        """
        if not self.spreadsheet_inventario or not self.is_connected_gsheets:
            return False
        
        try:
            sheet = self.spreadsheet_inventario.worksheet('BASE_DATOS_REMITOS')
            
            # Extraer datos del remito
            id_remito = remito_data.get('Nro_Remito', '')
            fecha_hora = str(remito_data.get('Fecha_Hora', ''))
            fecha = remito_data.get('Fecha', '') or fecha_hora[:10] or datetime.datetime.now().strftime('%Y-%m-%d')
            hora = remito_data.get('Hora', '') or (fecha_hora[11:16] if len(fecha_hora) >= 16 else datetime.datetime.now().strftime('%H:%M:%S'))
            responsable = remito_data.get('Responsable', '') or remito_data.get('Responsable_Entrega', '')
            tipo_remito = remito_data.get('Tipo', '').upper()
            
            # Determinar tipo (ENTRADA, SALIDA, TRASPASO)
            if 'ENTRADA' in tipo_remito:
                tipo_str = 'Entrada'
            elif 'TRASPASO' in tipo_remito:
                tipo_str = 'Traspaso'
            else:
                tipo_str = 'Salida'
            
            articulo_principal = remito_data.get('Articulo_Principal', '')
            marca = remito_data.get('Marca', '')
            modelo = remito_data.get('Modelo', '')
            cantidad = remito_data.get('Cantidad', 0)
            
            gerencia = remito_data.get('Gerencia', '')
            patente = remito_data.get('Patente', '')
            receptor = remito_data.get('Receptor_Nombre', '')
            email_receptor = remito_data.get('Receptor_Email', '')
            
            # Para región EDENOR
            region = ''
            if gerencia.upper() == 'EDENOR':
                region = remito_data.get('Region', '')
            
            observaciones = remito_data.get('Observaciones', '')
            
            # Nueva fila
            row = [
                id_remito,
                fecha,
                hora,
                responsable,
                tipo_str,
                articulo_principal,
                marca,
                modelo,
                cantidad,
                gerencia,
                patente,
                receptor,
                email_receptor,
                region,
                numero_factura,
                foto_factura_url,
                observaciones,
                'Procesado',
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            sheet.append_row(row)
            return True
        
        except Exception as e:
            print(f"Error guardando remito en Google Sheets: {e}")
            return False

    def obtener_remitos_de_gsheet(self, filtro_tipo: str = None) -> list:
        """
        Obtiene los remitos de la hoja BASE_DATOS_REMITOS.
        
        Parámetros:
        - filtro_tipo: 'Entrada', 'Salida', 'Traspaso' (opcional)
        
        Retorna: Lista de remitos
        """
        if not self.spreadsheet_inventario:
            return []
        
        try:
            headers = [
                'ID_REMITO', 'FECHA', 'HORA', 'RESPONSABLE', 'TIPO_REMITO',
                'ARTICULO_PRINCIPAL', 'MARCA', 'MODELO', 'CANTIDAD', 'GERENCIA',
                'PATENTE', 'RECEPTOR', 'EMAIL_RECEPTOR', 'REGION_EDENOR',
                'NUMERO_FACTURA', 'FOTO_FACTURA', 'OBSERVACIONES', 'ESTADO',
                'FECHA_PROCESAMIENTO'
            ]
            data = self._sheet_dataframe('BASE_DATOS_REMITOS', headers).to_dict(orient='records')
            
            if filtro_tipo:
                data = [r for r in data if r.get('TIPO_REMITO', '').lower() == filtro_tipo.lower()]
            
            return data
        
        except Exception:
            return []

    def registrar_patente_no_catalogada(self, patente: str, gerencia: str = "", receptor: str = "", remito_id: str = "") -> bool:
        """
        Registra una patente usada que NO está en el GSHEET de VEHICULOS.
        
        Parámetros:
        - patente: Patente del vehículo
        - gerencia: Gerencia asociada
        - receptor: Persona que recibió
        - remito_id: ID del remito donde se usó
        
        Retorna: True si fue exitoso
        """
        if not self.spreadsheet_inventario or not patente:
            return False
        
        try:
            # Crear hoja si no existe
            try:
                sheet = self.spreadsheet_inventario.worksheet('PATENTES_NO_CATALOGADAS')
            except:
                sheet = self.spreadsheet_inventario.add_worksheet(title='PATENTES_NO_CATALOGADAS', rows=500, cols=10)
                # Agregar encabezados
                headers = ['PATENTE', 'GERENCIA', 'RECEPTOR', 'REMITO_ID', 'FECHA_USO', 'ESTADO', 'OBSERVACIONES']
                sheet.append_row(headers)
            
            # Verificar si ya existe
            all_data = self._sheet_dataframe('PATENTES_NO_CATALOGADAS', ['PATENTE', 'GERENCIA', 'RECEPTOR', 'REMITO_ID', 'FECHA_USO', 'ESTADO', 'OBSERVACIONES']).to_dict(orient='records')
            for row in all_data:
                if row.get('PATENTE', '').upper() == patente.upper():
                    # Ya existe, actualizar
                    return True
            
            # Agregar nueva patente
            row = [
                patente.upper(),
                gerencia,
                receptor,
                remito_id,
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Pendiente de catalogar',
                'Usada en remito, esperando ser agregada a VEHICULOS'
            ]
            sheet.append_row(row)
            return True
        
        except Exception as e:
            print(f"Error registrando patente no catalogada: {e}")
            return False

    def subir_archivo_a_drive(self, archivo_bytes, nombre_archivo: str, carpeta_id: str = None) -> str:
        """
        Sube un archivo a Google Drive.
        
        Parámetros:
        - archivo_bytes: Contenido del archivo en bytes
        - nombre_archivo: Nombre del archivo
        - carpeta_id: ID de la carpeta en Drive (opcional)
        
        Retorna: URL de acceso al archivo o string vacío si falla
        """
        if not self.is_connected_gsheets:
            return ""
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            from io import BytesIO
            from google.oauth2.service_account import Credentials
            
            # Usar las mismas credenciales que para gsheets
            import os
            import streamlit as st
            
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                drive_service = build('drive', 'v3', credentials=creds)
                
                # Preparar archivo
                file_metadata = {'name': nombre_archivo}
                if carpeta_id:
                    file_metadata['parents'] = [carpeta_id]
                
                # Subir archivo
                media = MediaIoBaseUpload(BytesIO(archivo_bytes), mimetype='application/octet-stream', resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()

                try:
                    drive_service.permissions().create(
                        fileId=file["id"],
                        body={"type": "anyone", "role": "reader"},
                        fields="id",
                    ).execute()
                except Exception:
                    # Algunas cuentas Workspace bloquean enlaces publicos; el enlace
                    # autenticado sigue siendo valido para usuarios autorizados.
                    pass
                
                # Retornar enlace
                return f"https://drive.google.com/file/d/{file['id']}/view"
            else:
                return ""
        
        except Exception as e:
            print(f"Error subiendo archivo a Drive: {e}")
            return ""


@st.cache_resource(show_spinner=False)
def get_db():
    return DatabaseManager()