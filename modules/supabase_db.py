"""DatabaseManager basado en Supabase (nuevo backend)."""

from __future__ import annotations

import datetime
import json
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from modules.catalog_seed import get_initial_products
from modules.supabase_client import get_supabase_client, refresh_supabase_client, supabase_configured

APP_TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def now_local() -> datetime.datetime:
    return datetime.datetime.now(APP_TIMEZONE)


class DatabaseManagerSupabase:
    """Interfaz compatible con DatabaseManager, pero usando Supabase como backend."""

    def __init__(self):
        self.client = get_supabase_client()
        self.last_error = ""
        self.is_connected_gsheets = False  # Compatibilidad: usamos Supabase ahora
        self.is_connected_supabase = self.client is not None

    def _safe_execute(self, fn, default=None):
        """Ejecuta una función de Supabase con manejo de errores."""
        try:
            return fn()
        except Exception as exc:
            self.last_error = str(exc)
            print(f"Error en Supabase: {exc}")
            error_text = str(exc).lower()
            transient = any(term in error_text for term in (
                "timeout", "timed out", "connection", "connect", "reset", "temporarily", "503", "502", "504"
            ))
            if transient:
                try:
                    self.client = refresh_supabase_client()
                    return fn()
                except Exception as retry_exc:
                    self.last_error = str(retry_exc)
                    print(f"Error en Supabase tras reconectar: {retry_exc}")
            return default

    def reconnect(self) -> bool:
        """Renueva el cliente y comprueba que el esquema siga disponible."""
        try:
            self.client = refresh_supabase_client()
            self.last_error = ""
            self.client.table("productos").select("id").limit(1).execute()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def registrar_auditoria(self, usuario: str, accion: str, entidad: str, entidad_id: str = "", detalle: dict = None) -> bool:
        """Registra quién realizó una operación y qué entidad afectó."""
        def insert():
            self.client.table("auditoria").insert({
                "usuario": usuario or "",
                "accion": accion,
                "entidad": entidad,
                "entidad_id": entidad_id or "",
                "detalle": detalle or {},
            }).execute()
            return True

        return self._safe_execute(insert, False)

    def get_email_config(self) -> dict:
        defaults = {
            "subject": "Comprobante Digital: Remito de {tipo_remito} N° {nro_remito}",
            "body": "Estimado/a {destinatario_nombre},\n\nAdjunto encontrará el comprobante del movimiento de taller {nro_remito}.\n\nTipo de movimiento: {tipo_remito}",
        }
        def fetch():
            response = self.client.table("configuracion_app").select("valor").eq("clave", "email_template").limit(1).execute()
            if response.data:
                defaults.update(response.data[0].get("valor") or {})
            return defaults
        return self._safe_execute(fetch, defaults)

    def get_administradores(self) -> pd.DataFrame:
        """Obtiene los responsables habilitados para entrar a administración."""
        def fetch():
            response = self.client.table("administradores").select("nombre").order("nombre").execute()
            return pd.DataFrame(response.data or [], columns=["nombre"])

        administradores = self._safe_execute(fetch, pd.DataFrame(columns=["nombre"]))
        if administradores.empty:
            responsables = self.get_responsables()
            if not responsables.empty:
                primer_admin = str(responsables.iloc[0]["nombre"])
                try:
                    self.client.table("administradores").upsert({"nombre": primer_admin}).execute()
                    administradores = pd.DataFrame([{"nombre": primer_admin}])
                except Exception as exc:
                    self.last_error = str(exc)
                    print(f"Error inicializando administradores en Supabase: {exc}")
        return administradores

    def es_administrador(self, nombre: str) -> bool:
        administradores = self.get_administradores()
        return bool(not administradores.empty and nombre in administradores["nombre"].astype(str).tolist())

    def agregar_administrador(self, nombre: str, usuario: str = "") -> bool:
        def insert():
            self.client.table("administradores").upsert({"nombre": nombre}).execute()
            self.registrar_auditoria(usuario, "ALTA_ADMINISTRADOR", "administrador", nombre)
            return True
        return self._safe_execute(insert, False)

    def quitar_administrador(self, nombre: str, usuario: str = "") -> bool:
        def delete():
            administradores = self.get_administradores()
            if len(administradores) <= 1:
                return False
            self.client.table("administradores").delete().eq("nombre", nombre).execute()
            self.registrar_auditoria(usuario, "BAJA_ADMINISTRADOR", "administrador", nombre)
            return True
        return self._safe_execute(delete, False)

    def save_email_config(self, config: dict, usuario: str = "") -> bool:
        def save():
            self.client.table("configuracion_app").upsert({"clave": "email_template", "valor": config}).execute()
            self.registrar_auditoria(usuario, "MODIFICAR_PLANTILLA_EMAIL", "configuracion", "email_template", config)
            return True
        return self._safe_execute(save, False)

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
            producto_sql = {
                "id": str(producto_dict.get("ID", producto_dict.get("id", ""))),
                "categoria": str(producto_dict.get("Categoria", producto_dict.get("categoria", ""))),
                "marca": str(producto_dict.get("Marca", producto_dict.get("marca", ""))),
                "modelo_detalle": str(producto_dict.get("Modelo_Detalle", producto_dict.get("modelo_detalle", ""))),
                "codigo_pieza": str(producto_dict.get("Codigo_Pieza", producto_dict.get("codigo_pieza", "-"))),
                "stock_actual": int(producto_dict.get("Stock_Actual", producto_dict.get("stock_actual", 0))),
                "stock_minimo": int(producto_dict.get("Stock_Minimo", producto_dict.get("stock_minimo", 0))),
                "unidad": str(producto_dict.get("Unidad", producto_dict.get("unidad", "UNIDAD"))),
                "requiere_serial": str(producto_dict.get("Requiere_Serial", producto_dict.get("requiere_serial", "NO"))).upper() in ("SI", "SÍ", "TRUE", "1"),
            }
            if not producto_sql["id"]:
                return False
            self.client.table("productos").upsert(producto_sql).execute()
            self.registrar_auditoria(
                str(st.session_state.get("current_user", "")),
                "ALTA_O_MODIFICACION_PRODUCTO",
                "producto",
                producto_sql["id"],
                {"categoria": producto_sql["categoria"], "modelo": producto_sql["modelo_detalle"]},
            )
            return True

        return self._safe_execute(upsert, False)

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
        if "[" in p_clean and "]" in p_clean:
            p_clean = p_clean.split("[")[1].split("]")[0].strip()
        for u in units:
            if u.get("Estado") == "EN VEHICULO":
                v_act = str(u.get("Vehiculo_Actual", "")).upper()
                if "[" in v_act and "]" in v_act:
                    v_act = v_act.split("[")[1].split("]")[0].strip()
                if p_clean == v_act:
                    res.append(u)
        return res

    def registrar_ingreso_unidad(self, numero_marcado: str, tipo_articulo: str, marca: str, modelo_medida: str, id_producto: str, nro_remito: str, responsable: str, vehiculo_origen: str = ""):
        """Registra el ingreso de una unidad al stock."""
        numero_marcado = str(numero_marcado).strip()
        if not numero_marcado:
            return

        units = self.get_unidades_seriales()
        fecha_now = now_local().strftime("%Y-%m-%d %H:%M")

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
        fecha_now = now_local().strftime("%Y-%m-%d %H:%M")

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
        fecha_now = now_local().strftime("%Y-%m-%d %H:%M")

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

    def registrar_movimiento_unidad(self, unidad: dict, numero_anterior: str, estado_nuevo: str, vehiculo_nuevo: str, responsable: str, motivo: str = "", email_receptor: str = "") -> dict | None:
        """Emite comprobante y actualiza una unidad editada manualmente."""
        def save():
            numero_nuevo = str(unidad.get("Numero_Marcado", "")).strip()
            estado_anterior = str(unidad.get("Estado", "EN STOCK"))
            vehiculo_anterior = str(unidad.get("Vehiculo_Actual", ""))
            if not numero_nuevo or not unidad.get("id"):
                return None

            if estado_nuevo == "BAJA / SCRAP":
                tipo = "BAJA"
            elif estado_nuevo == "EN VEHICULO" and estado_anterior == "EN VEHICULO":
                tipo = "TRASPASO"
            elif estado_nuevo == "EN VEHICULO":
                tipo = "SALIDA"
            else:
                tipo = "ENTRADA"

            nro_remito = self.get_proximo_numero_remito(tipo)
            fecha_hora = now_local().strftime("%Y-%m-%d %H:%M")
            detalle = motivo or f"Movimiento manual de unidad {numero_anterior} a {numero_nuevo}"
            header = {
                "Nro_Remito": nro_remito,
                "Tipo": tipo,
                "Fecha_Hora": fecha_hora,
                "Responsable_Entrega": responsable,
                "Receptor_Nombre": responsable,
                "Receptor_Email": email_receptor,
                "Gerencia": "TALLER",
                "Patente": vehiculo_nuevo,
                "Vehiculo_Origen": vehiculo_anterior,
                "Articulo_Principal": unidad.get("Tipo_Articulo", ""),
                "Marca": unidad.get("Marca", ""),
                "Modelo": unidad.get("Modelo_Medida", ""),
                "Cantidad": 1,
                "Observaciones": detalle,
            }
            item = {
                "Nro_Remito": nro_remito,
                "ID_Producto": unidad.get("ID_Producto", ""),
                "Categoria": unidad.get("Tipo_Articulo", ""),
                "Marca": unidad.get("Marca", ""),
                "Descripcion": unidad.get("Modelo_Medida", ""),
                "Codigo_Pieza": "-",
                "Cantidad": 1,
                "Nro_Serie_Bateria_Neumatico": numero_nuevo,
            }
            self.client.table("remitos").insert({
                "nro_remito": nro_remito,
                "fecha": now_local().date().isoformat(),
                "hora": now_local().strftime("%H:%M:%S"),
                "responsable": responsable,
                "tipo_remito": tipo,
                "articulo_principal": header["Articulo_Principal"],
                "marca": header["Marca"],
                "modelo": header["Modelo"],
                "cantidad": 1,
                "gerencia": header["Gerencia"],
                "patente": vehiculo_nuevo,
                "receptor": responsable,
                "observaciones": detalle,
                "email_receptor": email_receptor,
                "nro_orden_taller": "",
                "vehiculo_origen": vehiculo_anterior,
            }).execute()
            self.client.table("remito_items").insert({
                "nro_remito": nro_remito,
                "id_producto": item["ID_Producto"],
                "categoria": item["Categoria"],
                "marca": item["Marca"],
                "descripcion": item["Descripcion"],
                "codigo_pieza": "-",
                "cantidad": 1,
                "numeros_seriales": numero_nuevo,
            }).execute()
            historial = list(unidad.get("Historial", []))
            historial.append({
                "Fecha": fecha_hora,
                "Tipo": f"MOVIMIENTO / {tipo}",
                "Nro_Remito": nro_remito,
                "Responsable": responsable,
                "Vehiculo_Anterior": vehiculo_anterior,
                "Vehiculo_Nuevo": vehiculo_nuevo,
                "Numero_Anterior": numero_anterior,
                "Numero_Nuevo": numero_nuevo,
                "Detalle": detalle,
            })
            self.client.table("unidades_serializadas").update({
                "numero_marcado": numero_nuevo,
                "estado": "BAJA" if estado_nuevo == "BAJA / SCRAP" else estado_nuevo,
                "vehiculo_actual": vehiculo_nuevo,
                "fecha_ultimo_movimiento": now_local().isoformat(),
                "historial": historial,
            }).eq("id", unidad["id"]).execute()
            self.registrar_auditoria(responsable, "MOVIMIENTO_UNIDAD", "unidad", numero_nuevo, {"remito": nro_remito, "tipo": tipo})
            return {"header": header, "items": [item], "nro_remito": nro_remito}

        return self._safe_execute(save, None)

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
                    'fecha': 'Fecha',
                    'hora': 'Hora',
                    'gerencia': 'Gerencia',
                    'patente': 'Patente',
                    'numero_factura': 'Numero_Factura',
                    'foto_factura': 'Foto_Factura',
                    'observaciones': 'Observaciones',
                    'estado': 'Estado',
                    'nro_orden_taller': 'Nro_Orden_Taller',
                    'vehiculo_origen': 'Vehiculo_Origen',
                    'link_pdf': 'Link_PDF',
                })
                df["Fecha_Hora"] = df.get("Fecha", "").astype(str) + " " + df.get("Hora", "").astype(str)
                df["Enviado_Email"] = df.get("Estado", "").astype(str).eq("Email enviado").map({True: "SI", False: "NO"})
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
                return pd.DataFrame(response.data).rename(columns={
                    "nro_remito": "Nro_Remito",
                    "id_producto": "ID_Producto",
                    "categoria": "Categoria",
                    "marca": "Marca",
                    "descripcion": "Descripcion",
                    "codigo_pieza": "Codigo_Pieza",
                    "cantidad": "Cantidad",
                    "numeros_seriales": "Nro_Serie_Bateria_Neumatico",
                })
            return pd.DataFrame()

        return self._safe_execute(fetch, pd.DataFrame())

    def guardar_remito(self, remito_header: dict, items: list) -> bool:
        """Guarda un remito completo (encabezado + ítems) en Supabase."""
        def save():
            nro_remito = remito_header.get("Nro_Remito", "")
            tipo_rem = remito_header.get("Tipo", "SALIDA").upper()

            if not nro_remito or not items:
                self.last_error = "El remito no tiene número o artículos."
                return False

            if "SALIDA" in tipo_rem:
                stock_por_producto = {}
                for item in items:
                    producto_id = str(item.get("ID_Producto", ""))
                    stock_por_producto[producto_id] = stock_por_producto.get(producto_id, 0) + int(item.get("Cantidad", 0))
                productos = self.get_productos()
                for producto_id, cantidad in stock_por_producto.items():
                    filas = productos[productos["ID"].astype(str) == producto_id] if not productos.empty else pd.DataFrame()
                    stock_actual = int(filas.iloc[0]["Stock_Actual"]) if not filas.empty else -1
                    if stock_actual < cantidad:
                        self.last_error = f"Stock insuficiente para {producto_id}: disponible {max(stock_actual, 0)}, solicitado {cantidad}."
                        return False
            
            # Inserta remito
            self.client.table("remitos").insert({
                "nro_remito": nro_remito,
                "fecha": remito_header.get("Fecha", now_local().date().isoformat()),
                "hora": remito_header.get("Hora", now_local().strftime("%H:%M:%S")),
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
                "nro_orden_taller": remito_header.get("Nro_Orden_Taller", ""),
                "vehiculo_origen": remito_header.get("Vehiculo_Origen", ""),
                "link_pdf": remito_header.get("Link_PDF", ""),
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

            self.registrar_auditoria(
                responsable,
                "EMITIR_REMITO",
                "remito",
                nro_remito,
                {"tipo": tipo_rem, "items": len(items)},
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
        elif "BAJA" in t_clean:
            prefix = "REM-B"
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

    def actualizar_datos_remito(self, remito_data: dict, numero_factura: str = "", foto_factura_url: str = "") -> bool:
        """Actualiza metadatos de un remito ya guardado en Supabase."""
        def save():
            self.client.table("remitos").update({
                "numero_factura": numero_factura,
                "foto_factura": foto_factura_url,
            }).eq("nro_remito", remito_data.get("Nro_Remito", "")).execute()
            return True

        return self._safe_execute(save, False)

    def actualizar_link_pdf(self, nro_remito: str, link_pdf: str) -> bool:
        def update():
            self.client.table("remitos").update({"link_pdf": link_pdf}).eq("nro_remito", nro_remito).execute()
            return True
        return self._safe_execute(update, False)

    def guardar_remito_en_gsheet(self, remito_data: dict, numero_factura: str = "", foto_factura_url: str = "") -> bool:
        """Compatibilidad con el nombre antiguo; nunca escribe en Google Sheets."""
        return self.actualizar_datos_remito(remito_data, numero_factura, foto_factura_url)

    def registrar_patente_no_catalogada(self, patente: str, gerencia: str = "", receptor: str = "", remito_id: str = "") -> bool:
        """Registra en Supabase una patente usada que no está en el catálogo de vehículos."""
        if not patente:
            return False

        def save():
            self.client.table("patentes_no_catalogadas").upsert({
                "patente": patente.strip().upper(),
                "gerencia": gerencia,
                "receptor": receptor,
                "remito_id": remito_id,
            }).execute()
            return True

        return self._safe_execute(save, False)

    def mark_remito_email_sent(self, nro_remito: str) -> bool:
        """Marca en Supabase que el PDF del remito fue enviado por email."""
        def update():
            self.client.table("remitos").update({"estado": "Email enviado"}).eq("nro_remito", nro_remito).execute()
            return True

        return self._safe_execute(update, False)

    def subir_archivo_a_drive(self, archivo_bytes, nombre_archivo: str, carpeta_id: str = None) -> str:
        """Sube evidencias a Google Drive sin escribir datos en Google Sheets."""
        try:
            from io import BytesIO
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload

            if "gcp_service_account" not in st.secrets:
                return ""
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]),
                scopes=["https://www.googleapis.com/auth/drive"],
            )
            drive_service = build("drive", "v3", credentials=creds)
            metadata = {"name": nombre_archivo}
            if carpeta_id:
                metadata["parents"] = [carpeta_id]
            media = MediaIoBaseUpload(BytesIO(archivo_bytes), mimetype="application/octet-stream", resumable=True)
            archivo = drive_service.files().create(
                body=metadata, media_body=media, fields="id"
            ).execute()
            try:
                drive_service.permissions().create(
                    fileId=archivo["id"], body={"type": "anyone", "role": "reader"}
                ).execute()
            except Exception:
                pass
            return f"https://drive.google.com/file/d/{archivo['id']}/view"
        except Exception as exc:
            print(f"Error subiendo archivo a Drive: {exc}")
            return ""

    def descargar_archivo_de_drive(self, enlace: str) -> bytes:
        """Descarga el archivo original guardado en Drive."""
        try:
            import io
            import re
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload

            match = re.search(r"/d/([^/]+)", str(enlace))
            if not match or "gcp_service_account" not in st.secrets:
                return b""
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]),
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            service = build("drive", "v3", credentials=creds)
            buffer = io.BytesIO()
            request = service.files().get_media(fileId=match.group(1))
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buffer.getvalue()
        except Exception as exc:
            print(f"Error descargando archivo de Drive: {exc}")
            return b""

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
            try:
                self.client.table("responsables").upsert(
                    RESPONSABLES_INICIALES,
                    on_conflict="nombre",
                ).execute()
            except Exception as exc:
                self.last_error = str(exc)
                print(f"Error inicializando responsables en Supabase: {exc}")
        
        return df

    def add_responsable(self, nombre: str, pin: str = "1234"):
        """Agrega un responsable a Supabase."""
        def insert():
            df = self.get_responsables()
            if nombre not in df["nombre"].values:
                self.client.table("responsables").insert({"nombre": nombre, "pin": pin}).execute()
                self.registrar_auditoria(nombre, "ALTA_RESPONSABLE", "responsable", nombre)

        self._safe_execute(insert)

    def eliminar_responsable(self, nombre: str, usuario: str = "") -> bool:
        def delete():
            if self.es_administrador(nombre):
                return False
            self.client.table("responsables").delete().eq("nombre", nombre).execute()
            self.registrar_auditoria(usuario, "BAJA_RESPONSABLE", "responsable", nombre)
            return True
        return self._safe_execute(delete, False)

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
            self.registrar_auditoria(
                str(st.session_state.get("current_user", "")),
                "ALTA_O_MODIFICACION_RECEPTOR",
                "receptor",
                nombre,
                {"email": email, "gerencia": gerencia},
            )

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
