"""DatabaseManager basado en Supabase (nuevo backend)."""

from __future__ import annotations

import datetime
import json
from typing import Any

import pandas as pd
import streamlit as st

from modules.catalog_seed import get_initial_products
from modules.supabase_client import get_supabase_client, supabase_configured


class DatabaseManagerSupabase:
    """Interfaz compatible con DatabaseManager, pero usando Supabase como backend."""

    def __init__(self):
        self.client = get_supabase_client()
        self.is_connected_gsheets = False  # Compatibilidad: usamos Supabase ahora
        self.is_connected_supabase = self.client is not None

    def _safe_execute(self, fn, default=None):
        """Ejecuta una función de Supabase con manejo de errores."""
        try:
            return fn()
        except Exception as exc:
            print(f"Error en Supabase: {exc}")
            return default

    # ===== PRODUCTOS =====
    def get_productos(self) -> pd.DataFrame:
        """Lee productos de Supabase."""
        columnas_sql = ["id", "categoria", "marca", "modelo_detalle", "codigo_pieza", "stock_actual", "stock_minimo", "unidad", "requiere_serial"]
        columnas_vista = ["ID", "Categoria", "Marca", "Modelo_Detalle", "Codigo_Pieza", "Stock_Actual", "Stock_Minimo", "Unidad", "Requiere_Serial"]

        def fetch():
            response = self.client.table("productos").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame(columns=columnas_sql)

        df = self._safe_execute(fetch, pd.DataFrame(columns=columnas_sql))
        
        if not df.empty:
            df = df.rename(columns=dict(zip(columnas_sql, columnas_vista)))

        for col in ["Stock_Actual", "Stock_Minimo"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        return df

    def save_productos(self, df: pd.DataFrame):
        """Guarda productos en Supabase."""
        if df.empty:
            return
        
        def save():
            for _, row in df.iterrows():
                self.client.table("productos").upsert({
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

        self._safe_execute(save)

    def update_stock(self, producto_id: str, cantidad: int, operacion: str = "salida") -> bool:
        """Actualiza el stock de un producto."""
        def update():
            df = self.get_productos()
            if df.empty or "ID" not in df.columns:
                return False
            
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
            
            self.client.table("productos").update({"stock_actual": int(nuevo)}).eq("id", producto_id).execute()
            return True

        return self._safe_execute(update, False)

    def add_or_update_producto(self, producto_dict: dict):
        """Agrega o actualiza un producto."""
        def upsert():
            self.client.table("productos").upsert(producto_dict).execute()

        self._safe_execute(upsert)

    # ===== UNIDADES SERIALIZADAS =====
    def get_unidades_seriales(self) -> list:
        """Lee unidades serializadas de Supabase."""
        def fetch():
            response = self.client.table("unidades_serializadas").select("*").execute()
            units = []
            for row in response.data:
                row["Numero_Marcado"] = row.get("numero_marcado", "")
                row["Tipo_Articulo"] = row.get("tipo_articulo", "")
                row["ID_Producto"] = row.get("id_producto", "")
                row["Marca"] = row.get("marca", "")
                row["Modelo_Medida"] = row.get("modelo_medida", "")
                row["Estado"] = row.get("estado", "EN STOCK")
                row["Vehiculo_Actual"] = row.get("vehiculo_actual", "")
                row["Fecha_Ultimo_Movimiento"] = row.get("fecha_ultimo_movimiento", "")
                row["Historial"] = json.loads(row.get("historial", "[]") or "[]")
                units.append(row)
            return units

        return self._safe_execute(fetch, [])

    def save_unidades_seriales(self, units_list: list):
        """Guarda unidades serializadas en Supabase."""
        def save():
            self.client.table("unidades_serializadas").delete().neq("id", -1).execute()  # Limpia
            for unit in units_list:
                self.client.table("unidades_serializadas").insert({
                    "numero_marcado": str(unit.get("Numero_Marcado", "")),
                    "tipo_articulo": str(unit.get("Tipo_Articulo", "")),
                    "id_producto": str(unit.get("ID_Producto", "")),
                    "marca": str(unit.get("Marca", "")),
                    "modelo_medida": str(unit.get("Modelo_Medida", "")),
                    "estado": str(unit.get("Estado", "EN STOCK")),
                    "vehiculo_actual": str(unit.get("Vehiculo_Actual", "")),
                    "fecha_ultimo_movimiento": unit.get("Fecha_Ultimo_Movimiento"),
                    "historial": json.dumps(unit.get("Historial", []), ensure_ascii=False),
                }).execute()

        self._safe_execute(save)

    def get_unidades_disponibles(self, tipo_articulo: str, marca: str = None, modelo: str = None) -> list:
        """Lista unidades disponibles (EN STOCK) con filtros opcionales."""
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
        """Lista unidades actualmente instaladas en un vehículo."""
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
        """Registra el ingreso de una unidad al stock."""
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
                "Historial": [{
                    "Fecha": fecha_now,
                    "Tipo": "INGRESO_NUEVO",
                    "Nro_Remito": nro_remito,
                    "Responsable": responsable,
                    "Detalle": f"Alta en inventario de taller ({marca} - {modelo_medida})"
                }]
            }
            units.append(new_unit)

        self.save_unidades_seriales(units)

    def registrar_salida_unidad(self, numero_marcado: str, tipo_articulo: str, vehiculo_destino: str, receptor: str, responsable: str, nro_remito: str, gerencia: str = ""):
        """Registra la salida de una unidad hacia un vehículo."""
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
        """Registra el traspaso de una unidad entre vehículos."""
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
        """Busca el historial completo de una unidad por número marcado."""
        numero_marcado = str(numero_marcado).strip().lower()
        units = self.get_unidades_seriales()
        for u in units:
            if str(u.get("Numero_Marcado")).strip().lower() == numero_marcado:
                return u
        return None

    def numeros_marcados_existentes(self, tipo_articulo: str, numeros: list) -> list:
        """Devuelve cuáles números ya existen para ese tipo de artículo."""
        buscados = {str(numero).strip().upper() for numero in numeros if str(numero).strip()}
        if not buscados:
            return []
        existentes = {
            str(unit.get("Numero_Marcado", "")).strip().upper()
            for unit in self.get_unidades_seriales()
            if str(unit.get("Tipo_Articulo", "")).strip().upper() == tipo_articulo.upper()
        }
        return sorted(buscados.intersection(existentes))

    # ===== REMITOS =====
    def get_remitos(self) -> pd.DataFrame:
        """Lee remitos desde Supabase."""
        def fetch():
            response = self.client.table("remitos").select("*").order("fecha", desc=True).execute()
            if response.data:
                df = pd.DataFrame(response.data)
                # Renombra columnas para compatibilidad
                df = df.rename(columns={
                    'nro_remito': 'Nro_Remito',
                    'tipo_remito': 'Tipo',
                    'responsable': 'Responsable_Entrega',
                    'receptor': 'Receptor_Nombre',
                    'email_receptor': 'Receptor_Email',
                })
                return df
            return pd.DataFrame()

        return self._safe_execute(fetch, pd.DataFrame())

    def get_remito_items(self, nro_remito: str = None) -> pd.DataFrame:
        """Lee ítems de remitos desde Supabase."""
        def fetch():
            if nro_remito:
                response = self.client.table("remito_items").select("*").eq("nro_remito", nro_remito).execute()
            else:
                response = self.client.table("remito_items").select("*").execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()

        return self._safe_execute(fetch, pd.DataFrame())

    def guardar_remito(self, remito_header: dict, items: list) -> bool:
        """Guarda un remito completo (encabezado + ítems) en Supabase."""
        def save():
            nro_remito = remito_header.get("Nro_Remito", "")
            
            # Inserta remito
            self.client.table("remitos").insert({
                "nro_remito": nro_remito,
                "fecha": remito_header.get("Fecha", datetime.date.today().isoformat()),
                "hora": remito_header.get("Hora", datetime.datetime.now().strftime("%H:%M:%S")),
                "responsable": remito_header.get("Responsable_Entrega", ""),
                "tipo_remito": remito_header.get("Tipo", "SALIDA"),
                "articulo_principal": remito_header.get("Articulo_Principal", ""),
                "marca": remito_header.get("Marca", ""),
                "modelo": remito_header.get("Modelo", ""),
                "cantidad": remito_header.get("Cantidad", 0),
                "gerencia": remito_header.get("Gerencia", ""),
                "patente": remito_header.get("Patente", ""),
                "receptor": remito_header.get("Receptor_Nombre", ""),
                "email_receptor": remito_header.get("Receptor_Email", ""),
                "observaciones": remito_header.get("Observaciones", ""),
            }).execute()

            # Inserta ítems
            for item in items:
                self.client.table("remito_items").insert({
                    "nro_remito": nro_remito,
                    "id_producto": item.get("ID_Producto", ""),
                    "categoria": item.get("Categoria", ""),
                    "marca": item.get("Marca", ""),
                    "descripcion": item.get("Descripcion", ""),
                    "codigo_pieza": item.get("Codigo_Pieza", ""),
                    "cantidad": item.get("Cantidad", 0),
                    "numeros_seriales": item.get("Nro_Serie_Bateria_Neumatico", ""),
                }).execute()

            # Procesa cambios de stock y trazabilidad
            tipo_rem = remito_header.get("Tipo", "SALIDA").upper()
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
                        seriales_validos = [s.strip() for s in seriales if s.strip() and s.strip() != "-"]
                        while len(seriales_validos) < cant:
                            seriales_validos.append(f"SIN_MARCAR-{nro_remito}-{len(seriales_validos) + 1}")
                        for s in seriales_validos[:cant]:
                            self.registrar_ingreso_unidad(
                                numero_marcado=s.strip(),
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

            # Agrega o actualiza receptor
            if remito_header.get("Receptor_Nombre") and "SALIDA" in tipo_rem:
                self.add_or_update_receptor(
                    remito_header["Receptor_Nombre"],
                    remito_header.get("Receptor_Email", ""),
                    remito_header.get("Gerencia", "")
                )

            return True

        return self._safe_execute(save, False)

    def obtener_remitos_de_gsheet(self, filtro_tipo: str = None) -> list:
        """Compatibilidad: obtiene remitos desde Supabase."""
        def fetch():
            if filtro_tipo:
                response = self.client.table("remitos").select("*").eq("tipo_remito", filtro_tipo).execute()
            else:
                response = self.client.table("remitos").select("*").execute()
            
            imported = []
            for row in response.data:
                imported.append({
                    "ID_REMITO": row.get("nro_remito", ""),
                    "FECHA": row.get("fecha", ""),
                    "HORA": row.get("hora", ""),
                    "RESPONSABLE": row.get("responsable", ""),
                    "TIPO_REMITO": row.get("tipo_remito", ""),
                    "ARTICULO_PRINCIPAL": row.get("articulo_principal", ""),
                    "MARCA": row.get("marca", ""),
                    "MODELO": row.get("modelo", ""),
                    "CANTIDAD": row.get("cantidad", ""),
                    "GERENCIA": row.get("gerencia", ""),
                    "PATENTE": row.get("patente", ""),
                    "RECEPTOR": row.get("receptor", ""),
                    "EMAIL_RECEPTOR": row.get("email_receptor", ""),
                    "REGION_EDENOR": row.get("region_edenor", ""),
                    "NUMERO_FACTURA": row.get("numero_factura", ""),
                    "FOTO_FACTURA": row.get("foto_factura", ""),
                    "OBSERVACIONES": row.get("observaciones", ""),
                    "ESTADO": row.get("estado", ""),
                    "FECHA_PROCESAMIENTO": row.get("fecha_procesamiento", ""),
                })
            return imported

        return self._safe_execute(fetch, [])

    def get_proximo_numero_remito(self, tipo: str) -> str:
        """Genera el próximo número de remito disponible."""
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

    def guardar_remito_en_gsheet(self, remito_data: dict, numero_factura: str = "", foto_factura_url: str = "") -> bool:
        """Compatibilidad: guarda remito en Supabase."""
        def save():
            self.client.table("remitos").insert({
                "nro_remito": remito_data.get("Nro_Remito", ""),
                "fecha": remito_data.get("Fecha", ""),
                "hora": remito_data.get("Hora", ""),
                "responsable": remito_data.get("Responsable", ""),
                "tipo_remito": remito_data.get("Tipo", "").upper(),
                "articulo_principal": remito_data.get("Articulo_Principal", ""),
                "marca": remito_data.get("Marca", ""),
                "modelo": remito_data.get("Modelo", ""),
                "cantidad": remito_data.get("Cantidad", 0),
                "gerencia": remito_data.get("Gerencia", ""),
                "patente": remito_data.get("Patente", ""),
                "receptor": remito_data.get("Receptor_Nombre", ""),
                "email_receptor": remito_data.get("Receptor_Email", ""),
                "numero_factura": numero_factura,
                "foto_factura": foto_factura_url,
                "observaciones": remito_data.get("Observaciones", ""),
                "estado": "Procesado",
                "fecha_procesamiento": datetime.datetime.now().isoformat(),
            }).execute()
            return True

        return self._safe_execute(save, False)

    # ===== RESPONSABLES =====
    def get_responsables(self) -> pd.DataFrame:
        """Lee responsables de Supabase."""
        def fetch():
            response = self.client.table("responsables").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame(columns=["nombre", "pin"])

        df = self._safe_execute(fetch, pd.DataFrame(columns=["nombre", "pin"]))
        if df.empty:
            from modules.catalog_seed import RESPONSABLES_INICIALES
            df = pd.DataFrame(RESPONSABLES_INICIALES)
            self.client.table("responsables").insert(RESPONSABLES_INICIALES).execute()
        
        return df

    def add_responsable(self, nombre: str, pin: str = "1234"):
        """Agrega un responsable a Supabase."""
        def insert():
            df = self.get_responsables()
            if nombre not in df["nombre"].values:
                self.client.table("responsables").insert({"nombre": nombre, "pin": pin}).execute()

        self._safe_execute(insert)

    # ===== RECEPTORES =====
    def get_receptores(self) -> pd.DataFrame:
        """Lee receptores de Supabase."""
        def fetch():
            response = self.client.table("receptores").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame(columns=["nombre", "email", "gerencia"])

        return self._safe_execute(fetch, pd.DataFrame(columns=["nombre", "email", "gerencia"]))

    def save_receptores(self, df: pd.DataFrame):
        """Guarda receptores en Supabase."""
        if df.empty:
            return
        
        def save():
            self.client.table("receptores").delete().neq("nombre", "").execute()
            for _, row in df.iterrows():
                self.client.table("receptores").insert({
                    "nombre": str(row.get("nombre", "")),
                    "email": str(row.get("email", "")),
                    "gerencia": str(row.get("gerencia", "")),
                }).execute()

        self._safe_execute(save)

    def add_or_update_receptor(self, nombre: str, email: str, gerencia: str):
        """Agrega o actualiza un receptor en Supabase."""
        def upsert():
            self.client.table("receptores").upsert({
                "nombre": nombre,
                "email": email,
                "gerencia": gerencia,
            }).execute()

        self._safe_execute(upsert)

    # ===== VEHÍCULOS (solo lectura desde Google Sheets) =====
    def get_vehiculos(self, solo_activos: bool = False) -> pd.DataFrame:
        """Lee vehículos desde Google Sheets (compatibilidad)."""
        from modules.gsheets_db import DatabaseManager as OldDM
        old_db = OldDM()
        return old_db.get_vehiculos(solo_activos)

    # ===== ÓRDENES (solo lectura desde Google Sheets) =====
    def get_ordenes_taller(self, solo_pendientes: bool = False, patente_filtro: str = None) -> pd.DataFrame:
        """Lee órdenes de taller desde Google Sheets (compatibilidad)."""
        from modules.gsheets_db import DatabaseManager as OldDM
        old_db = OldDM()
        return old_db.get_ordenes_taller(solo_pendientes, patente_filtro)

    # ===== UTILIDADES =====
    def reiniciar_datos_operativos(self) -> bool:
        """Limpia el inventario operativo sin borrar catálogo."""
        def reset():
            productos = self.get_productos()
            if not productos.empty:
                productos["Stock_Actual"] = 0
                self.save_productos(productos)

            self.client.table("unidades_serializadas").delete().neq("id", -1).execute()
            self.client.table("remitos").delete().neq("nro_remito", "").execute()
            self.client.table("remito_items").delete().neq("id", -1).execute()
            return True

        return self._safe_execute(reset, False)


@st.cache_resource(show_spinner=False)
def get_db():
    """Retorna DatabaseManager: Supabase si está configurado, sino Google Sheets (fallback)."""
    if supabase_configured():
        return DatabaseManagerSupabase()
    else:
        from modules.gsheets_db import DatabaseManager as OldDatabaseManager
        return OldDatabaseManager()
