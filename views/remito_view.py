# -*- coding: utf-8 -*-
"""
Vista Principal de Creacion de Remitos (Entrada, Salida y Traspaso) con Trazabilidad Unitaria.
"""

import datetime
from PIL import Image as PILImage
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from modules.gsheets_db import get_db
from modules.catalog_seed import (
    GERENCIAS, MARCAS_BATERIAS, VOLTAJES_BATERIA, AMPERAJES_BATERIA,
    MARCAS_NEUMATICOS, ANCHOS_NEUMATICO, PERFILES_NEUMATICO, RODADOS_NEUMATICO,
    MARCAS_LUBRICANTES, BASES_LUBRICANTE, VISCOSIDADES_LUBRICANTE, ENVASES_LUBRICANTE
)
from modules.pdf_generator import generate_remito_pdf, get_pdf_bytes
from modules.email_sender import send_remito_email
from modules.supabase_db import now_local


def _reset_remito_form():
    st.session_state["cart_items"] = []
    st.session_state["remito_exitoso"] = None
    for key in list(st.session_state):
        if key.startswith(("qty_", "new_qty_", "new_serial_", "in_num_", "mail_in_")):
            del st.session_state[key]
    st.session_state.pop("canvas_firma", None)

def render_remito_view():
    db = get_db()

    if "cart_items" not in st.session_state:
        st.session_state["cart_items"] = []
    if "remito_exitoso" not in st.session_state:
        st.session_state["remito_exitoso"] = None

    if st.session_state["remito_exitoso"]:
        res = st.session_state["remito_exitoso"]
        st.success(f"✅ ¡Remito **{res['nro_remito']}** generado con éxito!")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            pdf_bytes = get_pdf_bytes(res["pdf_path"])
            st.download_button(
                label="📥 Descargar Remito PDF",
                data=pdf_bytes,
                file_name=f"{res['nro_remito']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_d2:
            if st.button("📝 Nuevo Remito", use_container_width=True):
                _reset_remito_form()
                st.rerun()

        if res.get("email_status"):
            st.info(f"📧 Estado de envío: {res['email_status']}")

        st.divider()
        st.markdown("### Detalle del Remito Emitido:")
        st.write(f"**Tipo:** Remito de {res['header']['Tipo']}")
        if "SALIDA" in res['header']['Tipo']:
            st.write(f"**Receptor:** {res['header']['Receptor_Nombre']} ({res['header']['Receptor_Email']})")
            st.write(f"**Gerencia:** {res['header']['Gerencia']} | **Vehículo:** {res['header'].get('Patente', '-')}")
        elif "TRASPASO" in res['header']['Tipo']:
            st.write(f"**Vehículo Origen:** {res['header'].get('Vehiculo_Origen', '-')}")
            st.write(f"**Vehículo Destino:** {res['header'].get('Patente', '-')}")
            st.write(f"**Receptor:** {res['header']['Receptor_Nombre']}")
        else:
            st.write(f"**Responsable de Ingreso:** {res['header']['Responsable_Entrega']}")
            if res['header'].get('Patente') and res['header'].get('Patente') != "-":
                st.write(f"**Vehículo Origen:** {res['header']['Patente']}")
        if res['header'].get("Nro_Orden_Taller"):
            st.write(f"**Orden de Taller (OT):** {res['header']['Nro_Orden_Taller']}")
        return

    st.markdown("## 📋 Emisión de Remitos")
    st.caption("Gestión de movimientos de taller, trazabilidad por unidad y firmas digitales")

    # 1. TIPO DE REMITO
    tipo_remito = st.radio(
        "Seleccione Tipo de Operación:",
        [
            "SALIDA (Entrega de Materiales a Vehículo/Receptor)",
            "ENTRADA (Ingreso a Stock / Devolución)",
            "TRASPASO (Cambio directo entre Vehículos)"
        ],
        horizontal=False
    )
    es_salida = ("SALIDA" in tipo_remito)
    es_traspaso = ("TRASPASO" in tipo_remito)
    es_entrada = ("ENTRADA" in tipo_remito)

    if es_salida:
        tipo_str = "SALIDA"
    elif es_traspaso:
        tipo_str = "TRASPASO"
    else:
        tipo_str = "ENTRADA"

    df_veh = db.get_vehiculos(solo_activos=True)
    lista_veh_etiquetas = sorted(df_veh["ETIQUETA_COMPLETA"].dropna().unique().tolist()) if not df_veh.empty else []

    # 2. RESPONSABLE DE TALLER
    responsable_final = str(st.session_state.get("current_user", "")).strip()
    st.markdown(f"#### 👤 1. Responsable del Taller: **{responsable_final or 'Sesión no identificada'}**")

    # 3. DATOS DE DESTINATARIO Y VEHICULOS SEGUN OPERACION
    veh_origen_final = ""
    patente_final = ""
    receptor_nombre = ""
    receptor_email = ""
    gerencia_final = "GPS EDENOR"
    gerencia_sugerida = ""

    if es_traspaso:
        st.markdown("#### 🔄 2. Vehículos Involucrados en el Traspaso")
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            veh_origen_final = st.selectbox("Vehículo ORIGEN (de donde se retira la pieza):", ["Seleccione Vehículo"] + lista_veh_etiquetas)
        with c_v2:
            patente_final = st.selectbox("Vehículo DESTINO (donde se coloca la pieza):", ["Seleccione Vehículo"] + lista_veh_etiquetas)

        st.markdown("##### Receptor del Traspaso:")
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            receptor_nombre = st.text_input("Nombre y Apellido de quien recibe / traslada:", placeholder="Ej: Perez, Juan").strip()
        with c_tr2:
            receptor_email = st.text_input("Email (opcional):", placeholder="correo@empresa.com").strip()

    elif es_salida:
        st.markdown("#### 📥 2. Persona que Recibe (Destinatario)")
        df_rec = db.get_receptores()
        nombres_receptores = df_rec["nombre"].tolist() if not df_rec.empty else []
        
        col_r1, col_r2 = st.columns([1.2, 1.8])
        with col_r1:
            modo_rec = st.radio("Tipo de Receptor:", ["Existente", "Nuevo Receptor"], horizontal=True)
        
        if modo_rec == "Existente" and nombres_receptores:
            sel_rec = st.selectbox("Seleccione persona que recibe:", nombres_receptores)
            rec_data = df_rec[df_rec["nombre"] == sel_rec].iloc[0]
            receptor_nombre = sel_rec
            receptor_email = st.text_input("Correo Electrónico (para envío automático del remito):", value=str(rec_data.get("email", "")), placeholder="correo@empresa.com")
            if rec_data.get("gerencia") in GERENCIAS:
                gerencia_sugerida = rec_data.get("gerencia")
        else:
            receptor_nombre = st.text_input("Apellido y Nombre de quien recibe:", placeholder="Ej: Perez, Juan").strip()
            receptor_email = st.text_input("Correo Electrónico (para envío automático del remito):", placeholder="juan.perez@empresa.com").strip()

        idx_ger = GERENCIAS.index(gerencia_sugerida) if gerencia_sugerida in GERENCIAS else 0
        gerencia_final = st.selectbox("Gerencia / Servicio Solicitante:", GERENCIAS, index=idx_ger)
        if gerencia_final == "OTRA":
            gerencia_final = st.text_input("Especifique otra gerencia:").strip()

        st.markdown("#### 🚗 3. Vehículo de la Flota (Destino)")
        sel_veh_lbl = st.selectbox("Seleccione Vehículo:", ["Sin Vehículo / No Aplica"] + lista_veh_etiquetas)
        if sel_veh_lbl == "Sin Vehículo / No Aplica":
            patente_manual = st.text_input(
                "Patente no incluida en VEHICULOS (opcional):",
                placeholder="Se registrará para revisión, sin modificar el libro DPA"
            ).strip().upper()
            patente_final = patente_manual
        elif sel_veh_lbl != "Sin Vehículo / No Aplica":
            patente_final = sel_veh_lbl

    else:
        # ENTRADA
        receptor_nombre = responsable_final
        receptor_email = ""
        gerencia_final = "TALLER"

        st.markdown("#### 🚗 2. Vehículo de Origen (Opcional - si proviene de un vehículo)")
        sel_veh_ent = st.selectbox("Vehículo del que se desmontó (o Sin Vehículo para ingreso general):", ["Sin Vehículo (Ingreso Nuevo a Stock)"] + lista_veh_etiquetas)
        if sel_veh_ent != "Sin Vehículo (Ingreso Nuevo a Stock)":
            patente_final = sel_veh_ent

    # 4. ORDEN DE TRABAJO (OT)
    st.markdown("#### 🔧 Orden de Trabajo / Taller (OT)")
    patente_pura = ""
    if "[" in patente_final and "]" in patente_final:
        patente_pura = patente_final.split("[")[1].split("]")[0].strip()

    df_ots = db.get_ordenes_taller(solo_pendientes=True, patente_filtro=patente_pura if patente_pura else None)
    
    opciones_ot = ["Sin OT asociada", "Ingresar N° OT Manualmente"]
    dict_ots = {}
    if not df_ots.empty:
        for _, row in df_ots.iterrows():
            ot_nro = str(row.get("Nro_OT", "")).strip()
            ot_falla = str(row.get("Descripcion_Trabajo", "")).strip()
            ot_pat = str(row.get("Patente", "")).strip()
            lbl = f"{ot_nro} - {ot_pat} - {ot_falla[:35]}"
            opciones_ot.append(lbl)
            dict_ots[lbl] = row

    sel_ot = st.selectbox("Vincular a Orden de Trabajo pendiente (opcional):", opciones_ot)
    
    nro_ot_final = ""
    if sel_ot == "Ingresar N° OT Manualmente":
        nro_ot_final = st.text_input("Escriba el número de Orden de Trabajo (ej. OT-1050):", placeholder="OT-...").strip()
    elif sel_ot != "Sin OT asociada":
        ot_row = dict_ots.get(sel_ot)
        if ot_row is not None:
            nro_ot_final = str(ot_row.get("Nro_OT", ""))
            st.info(f"**Reporte de Falla / Motivo:** {ot_row.get('Descripcion_Trabajo', '-')}")

    # 5. ARTICULOS Y TRAZABILIDAD
    st.markdown("#### 📦 Selección de Artículos y Números Marcados")
    
    df_prod = db.get_productos()
    if df_prod.empty:
        st.warning("No hay productos disponibles en STOCK_PRODUCTOS. Verifique la conexión con Google Sheets.")
        return
    if es_salida:
        categorias_disponibles = sorted(
            df_prod.loc[df_prod["Stock_Actual"] > 0, "Categoria"].unique().tolist()
        )
    else:
        categorias_disponibles = sorted(df_prod["Categoria"].unique().tolist()) if not df_prod.empty else []

    with st.expander("➕ Agregar Artículo al Remito", expanded=True):
        cat_sel = st.selectbox("Categoría de Artículo:", categorias_disponibles)
        
        df_cat_all = df_prod[df_prod["Categoria"] == cat_sel]
        df_cat = df_cat_all.copy()
        unidades_origen = db.get_unidades_en_vehiculo(veh_origen_final) if es_traspaso and veh_origen_final else []
        if es_traspaso and unidades_origen:
            ids_origen = {str(unit.get("ID_Producto", "")) for unit in unidades_origen}
            df_cat_origen = df_cat[df_cat["ID"].astype(str).isin(ids_origen)]
            if not df_cat_origen.empty:
                df_cat = df_cat_origen
        if es_salida:
            df_cat = df_cat[df_cat["Stock_Actual"] > 0]

        modo_item = "Existente en Catálogo"
        if es_entrada:
            modo_item = st.radio("Origen del producto:", ["Existente en Catálogo", "Dar de Alta Producto Nuevo"], horizontal=True)

        if modo_item == "Existente en Catálogo":
            if df_cat.empty and es_salida:
                st.warning(f"⚠️ No hay stock disponible para {cat_sel}.")
            else:
                prod_dict = {}
                opciones_prod = []
                for _, p in df_cat.iterrows():
                    cantidad_carrito = sum(
                        int(item.get("Cantidad", 0))
                        for item in st.session_state["cart_items"]
                        if str(item.get("ID_Producto", "")) == str(p.get("ID", ""))
                    )
                    stock_disponible = max(0, int(p["Stock_Actual"]) - cantidad_carrito) if es_salida else int(p["Stock_Actual"])
                    ya_en_carrito = cantidad_carrito > 0
                    if es_salida and stock_disponible <= 0 and not ya_en_carrito:
                        continue
                    stock_txt = f"(Stock: {stock_disponible})"
                    if ya_en_carrito:
                        stock_txt += f" | En carrito: {cantidad_carrito}"
                    lbl = f"{p['Marca']} | {p['Modelo_Detalle']} {stock_txt}"
                    if p.get("Codigo_Pieza") and p.get("Codigo_Pieza") != "-":
                        lbl += f" [{p['Codigo_Pieza']}]"
                    opciones_prod.append(lbl)
                    prod_dict[lbl] = p

                if not opciones_prod:
                    st.warning("No hay stock disponible para agregar en esta categoría.")
                    st.info("Podés continuar con los artículos que ya están en el carrito y emitir el remito.")
                    productos_carrito = [
                        item for item in st.session_state["cart_items"]
                        if item.get("Categoria") == cat_sel
                    ]
                    p_selected = None
                    if productos_carrito:
                        producto_id_carrito = str(productos_carrito[0].get("ID_Producto", ""))
                        filas_carrito = df_cat_all[df_cat_all["ID"].astype(str) == producto_id_carrito]
                        if not filas_carrito.empty:
                            p_selected = filas_carrito.iloc[0]
                else:
                    prod_sel_lbl = st.selectbox("Seleccione Producto:", opciones_prod)
                    p_selected = prod_dict.get(prod_sel_lbl)
                if p_selected is None:
                    st.info("Seleccione otra categoría para agregar artículos o continúe con el carrito.")
                    st.stop()
                item_key = str(p_selected.get("ID", cat_sel)).replace(" ", "_")
                cantidad_carrito = sum(
                    int(item.get("Cantidad", 0))
                    for item in st.session_state["cart_items"]
                    if str(item.get("ID_Producto", "")) == str(p_selected.get("ID", ""))
                )
                stock_disponible = max(0, int(p_selected["Stock_Actual"]) - cantidad_carrito) if es_salida else int(p_selected["Stock_Actual"])
                puede_agregar = not es_salida or stock_disponible > 0

                if cat_sel in ["BATERIA", "NEUMATICO"]:
                    st.markdown(f"##### 🏷️ Trazabilidad: Números Marcados de {cat_sel}")
                    
                    if es_salida:
                        cantidad_carrito = sum(
                            int(item.get("Cantidad", 0))
                            for item in st.session_state["cart_items"]
                            if str(item.get("ID_Producto", "")) == str(p_selected.get("ID", ""))
                        )
                        stock_disponible = max(0, int(p_selected["Stock_Actual"]) - cantidad_carrito)
                        seriales_en_carrito = {
                            serial.strip().upper()
                            for item in st.session_state["cart_items"]
                            if str(item.get("ID_Producto", "")) == str(p_selected.get("ID", ""))
                            for serial in str(item.get("Nro_Serie_Bateria_Neumatico", "")).split(",")
                            if serial.strip() and serial.strip() != "-"
                        }
                        nums_disponibles = [
                            numero for numero in db.get_unidades_disponibles(
                                cat_sel, marca=p_selected["Marca"], modelo=p_selected["Modelo_Detalle"]
                            ) if not str(numero).upper().startswith("SIN_MARCAR-")
                            and str(numero).upper() not in seriales_en_carrito
                        ]
                        puede_agregar = stock_disponible > 0
                        modo_salida = st.radio(
                            "Tipo de unidad a retirar:",
                            ["Marcada", "Sin marcar"],
                            horizontal=True,
                            key=f"modo_salida_{item_key}",
                        )
                        if modo_salida == "Marcada" and nums_disponibles:
                            st.info(f"Números disponibles: {', '.join(['#' + str(n) for n in nums_disponibles])}")
                            nums_seleccionados = st.multiselect("Números Marcados a entregar:", nums_disponibles, key=f"nums_salida_{item_key}")
                            cant = len(nums_seleccionados)
                            seriales_str = ", ".join(nums_seleccionados)
                        elif modo_salida == "Marcada":
                            st.warning("No hay números físicos marcados disponibles para este producto.")
                            cant = st.number_input("Cantidad sin marcar:", min_value=1, max_value=max(1, stock_disponible), value=1, step=1, key=f"qty_unmarked_{item_key}", disabled=not puede_agregar)
                            seriales_str = "-"
                        else:
                            cant = st.number_input("Cantidad sin marcar:", min_value=1, max_value=max(1, stock_disponible), value=1, step=1, key=f"qty_unmarked_{item_key}", disabled=not puede_agregar)
                            seriales_str = "-"
                    elif es_traspaso:
                        st.info("Ingrese un número marcado asignado al vehículo de origen:")
                        cant = 1
                        seriales_sugeridos = [str(unit.get("Numero_Marcado", "")) for unit in unidades_origen]
                        seriales_str = st.text_input(
                            "Número Marcado de la unidad:",
                            value=seriales_sugeridos[0] if len(seriales_sugeridos) == 1 else "",
                            placeholder="Ej: 32",
                        ).strip()

                    else:
                        # ENTRADA
                        item_key = str(p_selected.get("ID", cat_sel)).replace(" ", "_")
                        cant = st.number_input("Cantidad a Ingresar:", min_value=1, value=1, step=1, key=f"qty_{cat_sel}_{item_key}")
                        st.caption(f"Ingrese los números marcados correspondientes a las {cant} unidad(es):")
                        
                        seriales_list = []
                        for start_idx in range(0, int(cant), 5):
                            cols_num = st.columns(min(5, int(cant) - start_idx))
                            for offset, col_num in enumerate(cols_num):
                                idx_c = start_idx + offset
                                with col_num:
                                    val_n = st.text_input(f"Unidad #{idx_c + 1}:", key=f"in_num_{cat_sel}_{item_key}_{idx_c}", placeholder=f"N° {idx_c + 1}").strip()
                                    if val_n:
                                        seriales_list.append(val_n)
                        seriales_str = ", ".join(seriales_list)

                else:
                    # Otros articulos
                    item_key = str(p_selected.get("ID", cat_sel)).replace(" ", "_")
                    max_cant = int(p_selected["Stock_Actual"]) if es_salida else 500
                    col_c1, col_c2 = st.columns([1, 2])
                    with col_c1:
                        cant = st.number_input("Cantidad:", min_value=1, max_value=max(1, max_cant), value=1, step=1)
                    with col_c2:
                        seriales_str = "-"

                if st.button("📥 Agregar al Carrito", use_container_width=True, disabled=es_salida and not puede_agregar):
                    if es_traspaso:
                        numero_traspaso = str(seriales_str).strip()
                        unidad_traspaso = db.buscar_historial_unidad(numero_traspaso) if numero_traspaso else None
                        vehiculo_unidad = str(unidad_traspaso.get("Vehiculo_Actual", "")) if unidad_traspaso else ""
                        if not unidad_traspaso:
                            st.error(f"No existe una unidad con número marcado {numero_traspaso or '(vacío)'}.")
                            st.stop()
                        if str(unidad_traspaso.get("Tipo_Articulo", "")).upper() != cat_sel.upper() or str(unidad_traspaso.get("ID_Producto", "")) != str(p_selected.get("ID", "")):
                            st.error("El número marcado no corresponde al modelo exacto seleccionado.")
                            st.stop()
                        origen_patente = veh_origen_final.split("[")[1].split("]")[0].strip().upper() if "[" in veh_origen_final and "]" in veh_origen_final else veh_origen_final.strip().upper()
                        unidad_patente = vehiculo_unidad.split("[")[1].split("]")[0].strip().upper() if "[" in vehiculo_unidad and "]" in vehiculo_unidad else vehiculo_unidad.strip().upper()
                        if unidad_patente != origen_patente:
                            st.error(f"La batería/neumático {numero_traspaso} está asignado a otro vehículo. No se puede traspasar desde {veh_origen_final}.")
                            st.stop()
                    if cat_sel in ["BATERIA", "NEUMATICO"] or seriales_str == "-":
                        nuevos_seriales = [s.strip().upper() for s in str(seriales_str).split(",") if s.strip() and s.strip() != "-"]
                        usados = []
                        for cart_item in st.session_state["cart_items"]:
                            if cart_item.get("Categoria") == cat_sel:
                                usados.extend(str(cart_item.get("Nro_Serie_Bateria_Neumatico", "")).upper().split(","))
                        usados = [s.strip() for s in usados if s.strip() and s.strip() != "-" and not s.strip().startswith("SIN_MARCAR-")]
                        repetidos = sorted(set(nuevos_seriales).intersection(usados))
                        existentes = db.numeros_marcados_existentes(cat_sel, nuevos_seriales) if es_entrada else []
                        if len(nuevos_seriales) != len(set(nuevos_seriales)) or repetidos:
                            detalle = ", ".join(sorted(set(repetidos)))
                            st.error(f"No puede agregar dos veces la misma unidad marcada{': ' + detalle if detalle else ''}.")
                            st.stop()
                        if existentes:
                            st.error(f"Los siguientes números de {cat_sel} ya existen: {', '.join(existentes)}. Verifique el marcado físico antes de continuar.")
                            st.stop()
                        st.session_state["cart_items"].append({
                            "ID_Producto": p_selected["ID"],
                            "Categoria": p_selected["Categoria"],
                            "Marca": p_selected["Marca"],
                            "Descripcion": p_selected["Modelo_Detalle"],
                            "Codigo_Pieza": p_selected.get("Codigo_Pieza", "-"),
                            "Cantidad": int(cant),
                            "Nro_Serie_Bateria_Neumatico": seriales_str if seriales_str else "-"
                        })
                        st.session_state.pop(f"qty_{cat_sel}_{item_key}", None)
                        st.session_state.pop(f"seriales_{cat_sel}_{item_key}", None)
                        for idx_c in range(5):
                            st.session_state.pop(f"in_num_{cat_sel}_{item_key}_{idx_c}", None)
                        st.toast(f"Agregado: {p_selected['Modelo_Detalle']} (x{cant})")
                        st.rerun()

        else:
            # ALTA DE PRODUCTO NUEVO
            st.markdown(f"##### 🆕 Especificaciones del Nuevo Artículo ({cat_sel}):")
            n_marca = ""
            n_modelo = ""
            n_codigo = "-"

            if cat_sel == "BATERIA":
                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    n_marca = st.selectbox("Marca:", MARCAS_BATERIAS)
                    if n_marca == "OTRA":
                        n_marca = st.text_input("Escriba Marca:").strip()
                with col_b2:
                    n_volt = st.selectbox("Voltaje:", VOLTAJES_BATERIA + ["OTRO"])
                    if n_volt == "OTRO":
                        n_volt = st.text_input("Escriba voltaje:").strip()
                with col_b3:
                    n_ah = st.selectbox("Capacidad (Ah):", AMPERAJES_BATERIA + ["OTRA"])
                    if n_ah == "OTRA":
                        n_ah = st.text_input("Escriba capacidad:").strip()
                n_modelo = f"{n_volt} {n_ah}"

            elif cat_sel == "NEUMATICO":
                col_neu1, col_neu2 = st.columns(2)
                with col_neu1:
                    n_marca = st.selectbox("Marca:", MARCAS_NEUMATICOS)
                    if n_marca == "OTRA":
                        n_marca = st.text_input("Escriba Marca:").strip()
                with col_neu2:
                    c_ancho, c_perf, c_rod = st.columns(3)
                    with c_ancho:
                        n_ancho = st.selectbox("Ancho:", ANCHOS_NEUMATICO + ["OTRO"])
                        if n_ancho == "OTRO":
                            n_ancho = st.text_input("Escriba ancho:").strip()
                    with c_perf:
                        n_perf = st.selectbox("Perfil:", PERFILES_NEUMATICO + ["OTRO"])
                        if n_perf == "OTRO":
                            n_perf = st.text_input("Escriba perfil:").strip()
                    with c_rod:
                        n_rod = st.selectbox("Rodado:", RODADOS_NEUMATICO + ["OTRO"])
                        if n_rod == "OTRO":
                            n_rod = st.text_input("Escriba rodado:").strip()
                    n_modelo = f"{n_ancho}/{n_perf}{n_rod}"

            elif cat_sel == "LUBRICANTE":
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    n_marca = st.selectbox("Marca:", MARCAS_LUBRICANTES)
                    if n_marca == "OTRA":
                        n_marca = st.text_input("Escriba Marca:").strip()
                    n_base = st.selectbox("Tipo de Base:", BASES_LUBRICANTE)
                with col_l2:
                    n_visc = st.selectbox("Viscosidad:", VISCOSIDADES_LUBRICANTE)
                    n_env = st.selectbox("Envase:", ENVASES_LUBRICANTE)
                n_modelo = f"{n_base} {n_visc} {n_env}"

            else:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    n_marca = st.text_input("Marca / Fabricante:", value="Generico").strip()
                    n_modelo = st.text_input("Descripción:", placeholder="Detalle...").strip()
                with col_g2:
                    n_codigo = st.text_input("Código de Pieza (opcional):").strip()

            new_item_key = f"nuevo_{cat_sel}"
            n_cant = st.number_input("Cantidad a Ingresar:", min_value=1, value=1, step=1, key=f"new_qty_{new_item_key}")
            
            n_seriales_str = "-"
            if cat_sel in ["BATERIA", "NEUMATICO"]:
                st.caption(f"Números marcados opcionales para las {n_cant} unidad(es):")
                new_serial_list = []
                for start_idx in range(0, int(n_cant), 5):
                    serial_cols = st.columns(min(5, int(n_cant) - start_idx))
                    for offset, serial_col in enumerate(serial_cols):
                        serial_idx = start_idx + offset
                        with serial_col:
                            serial_value = st.text_input(f"Unidad #{serial_idx + 1} (opcional):", key=f"new_serial_{new_item_key}_{serial_idx}").strip()
                            if serial_value:
                                new_serial_list.append(serial_value)
                n_seriales_str = ", ".join(new_serial_list) or "-"

            if st.button("✨ Dar de Alta y Agregar al Remito", use_container_width=True):
                if not n_marca or not n_modelo:
                    st.error("Debe completar los campos.")
                else:
                    nuevos_seriales = [s.strip().upper() for s in n_seriales_str.split(",") if s.strip() and s.strip() != "-"]
                    existentes = db.numeros_marcados_existentes(cat_sel, nuevos_seriales)
                    if len(nuevos_seriales) != len(set(nuevos_seriales)):
                        st.error(f"No puede repetir un número marcado dentro del alta de {cat_sel}.")
                        st.stop()
                    if existentes:
                        st.error(f"Los siguientes números de {cat_sel} ya existen: {', '.join(existentes)}. Verifique el marcado físico antes de continuar.")
                        st.stop()
                    new_id = f"{cat_sel[:3]}-{datetime.datetime.now().strftime('%m%d%H%M%S')}"
                    prod_dict_new = {
                        "ID": new_id,
                        "Categoria": cat_sel,
                        "Marca": n_marca,
                        "Modelo_Detalle": n_modelo,
                        "Codigo_Pieza": n_codigo if n_codigo else "-",
                        "Stock_Actual": 0,
                        "Stock_Minimo": 1,
                        "Unidad": "UNIDAD",
                        "Requiere_Serial": "SI" if cat_sel in ["BATERIA", "NEUMATICO"] else "NO"
                    }
                    if not db.add_or_update_producto(prod_dict_new):
                        st.error("No se pudo guardar el producto en la base de datos. El artículo no fue agregado al remito.")
                        st.stop()
                    st.session_state["cart_items"].append({
                        "ID_Producto": new_id,
                        "Categoria": cat_sel,
                        "Marca": n_marca,
                        "Descripcion": n_modelo,
                        "Codigo_Pieza": n_codigo if n_codigo else "-",
                        "Cantidad": int(n_cant),
                        "Nro_Serie_Bateria_Neumatico": n_seriales_str if n_seriales_str else "-"
                    })
                    st.session_state.pop(f"new_qty_{new_item_key}", None)
                    for serial_idx in range(5):
                        st.session_state.pop(f"new_serial_{new_item_key}_{serial_idx}", None)
                    st.success(f"Producto creado: {n_marca} | {n_modelo}")
                    st.rerun()

    # Mostrar Carrito
    if st.session_state["cart_items"]:
        st.markdown("#### 🛒 Artículos en este Remito:")
        for i, item in enumerate(st.session_state["cart_items"]):
            c_info, c_del = st.columns([4, 1])
            with c_info:
                serial_info = f" | **N° Marcados:** `{item['Nro_Serie_Bateria_Neumatico']}`" if item.get('Nro_Serie_Bateria_Neumatico') and item['Nro_Serie_Bateria_Neumatico'] != '-' else ""
                st.markdown(f"**{i+1}. [{item['Categoria']}]** {item['Marca']} - {item['Descripcion']} **(x{item['Cantidad']})**{serial_info}")
            with c_del:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state["cart_items"].pop(i)
                    st.rerun()
    else:
        st.info("El remito no tiene artículos cargados aún.")

    # 6. CAMPOS ESPECÍFICOS PARA ENTRADA
    numero_factura = ""
    foto_factura = None
    foto_factura_url = ""
    
    if es_entrada:
        st.markdown("#### 🧾 Información de Factura (solo para ENTRADA)")
        col_fact1, col_fact2 = st.columns(2)
        
        with col_fact1:
            numero_factura = st.text_input(
                "Número de Factura (opcional):",
                placeholder="Ej: FC-2026-001234",
                help="Número de factura asociado a la compra/ingreso de materiales"
            )
        
        with col_fact2:
            foto_factura = st.file_uploader(
                "Foto de la Factura (opcional):",
                type=["jpg", "jpeg", "png", "pdf"],
                help="Sube la foto o PDF de la factura para referencia"
            )
            if foto_factura:
                st.caption(f"✅ Archivo: {foto_factura.name}")
                foto_factura_url = f"Pendiente de carga: {foto_factura.name}"

    st.markdown("#### 📷 Fotos de evidencia (opcional)")
    fotos_evidencia = st.file_uploader(
        "Fotos del vehículo o de la mercadería instalada:",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Estas fotos se incorporan al PDF del remito y se guardan en Google Drive."
    )
    
    # 6. OBSERVACIONES Y FIRMA DIGITAL
    st.markdown("#### ✍️ Conformidad y Firma")
    observaciones = st.text_area("Observaciones adicionales (opcional):", placeholder="Detalles adicionales sobre el movimiento...")

    if es_salida:
        firmante_label = f"Firma de {receptor_nombre} (Receptor):"
    elif es_traspaso:
        firmante_label = f"Firma de {receptor_nombre} (Receptor del Traspaso):"
    else:
        firmante_label = f"Firma de {responsable_final} (Responsable de Taller):"

    st.caption(f"{firmante_label} - Firme en el recuadro blanco utilizando el dedo o lápiz táctil:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=140,
        width=350,
        drawing_mode="freedraw",
        key="canvas_firma",
    )

    st.markdown("<small style='color: #64748B;'>Certifico que la información provista es correcta y los elementos fueron entregados/recibidos a la fecha y hora indicadas.</small>", unsafe_allow_html=True)
    st.divider()

    # 7. BOTON DE EMISION
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button("🚀 Emitir y Generar Remito", type="primary", use_container_width=True):
            if not responsable_final:
                st.error("Por favor seleccione el Responsable del taller.")
                return
            if (es_salida or es_traspaso) and not receptor_nombre:
                st.error("Por favor ingrese el Nombre de quien recibe.")
                return
            if es_traspaso and (not veh_origen_final or not patente_final or veh_origen_final == patente_final):
                st.error("En un traspaso debe seleccionar un Vehículo Origen y un Vehículo Destino distintos.")
                return
            if not st.session_state["cart_items"]:
                st.error("Debe agregar al menos un artículo al remito.")
                return

            signature_img = None
            if canvas_result.image_data is not None:
                try:
                    img_array = canvas_result.image_data
                    pil_img = PILImage.fromarray(img_array.astype('uint8'), 'RGBA')
                    if pil_img.getbbox():
                        signature_img = pil_img
                except Exception:
                    signature_img = None

            nro_remito = db.get_proximo_numero_remito(tipo_str)
            fecha_hora_now = now_local().strftime("%Y-%m-%d %H:%M")

            remito_header = {
                "Nro_Remito": nro_remito,
                "Tipo": tipo_str,
                "Fecha_Hora": fecha_hora_now,
                "Nro_Orden_Taller": nro_ot_final,
                "Responsable_Entrega": responsable_final,
                "Receptor_Nombre": receptor_nombre,
                "Receptor_Email": receptor_email,
                "Gerencia": gerencia_final,
                "Patente": patente_final,
                "Vehiculo_Origen": veh_origen_final if es_traspaso else "",
                "Observaciones": observaciones,
                "Enviado_Email": "NO"
            }
            remito_header["Numero_Factura"] = numero_factura if es_entrada else ""

            items_to_save = []
            for it in st.session_state["cart_items"]:
                it_copy = dict(it)
                it_copy["Nro_Remito"] = nro_remito
                items_to_save.append(it_copy)

            if items_to_save:
                first_item = items_to_save[0]
                remito_header["Articulo_Principal"] = first_item.get("Categoria", "")
                remito_header["Marca"] = first_item.get("Marca", "")
                remito_header["Modelo"] = first_item.get("Descripcion", "")
                remito_header["Cantidad"] = sum(int(item.get("Cantidad", 0)) for item in items_to_save)

            seriales_remito = []
            for item in items_to_save:
                if item.get("Categoria") in ["BATERIA", "NEUMATICO"]:
                    seriales_remito.extend(
                        s.strip().upper()
                        for s in str(item.get("Nro_Serie_Bateria_Neumatico", "")).split(",")
                        if s.strip() and s.strip() != "-"
                    )
            if len(seriales_remito) != len(set(seriales_remito)):
                st.error("El remito contiene dos veces el mismo número marcado. Quite el duplicado antes de emitirlo.")
                return

            with st.spinner("Generando comprobante PDF, actualizando trazabilidad e inventario..."):
                evidencia_images = []
                for foto in fotos_evidencia or []:
                    try:
                        evidencia_images.append(PILImage.open(foto).convert("RGB"))
                    except Exception:
                        st.warning(f"No se pudo leer la foto {foto.name}.")
                pdf_path = generate_remito_pdf(remito_header, items_to_save, signature_img, evidencia_images)
                remito_header["Link_PDF"] = pdf_path
                if not db.guardar_remito(remito_header, items_to_save):
                    st.error("No se pudo guardar el remito en la base de datos. No se aplicó el movimiento.")
                    return
                
                # Subir foto de factura a Google Drive (si existe)
                foto_factura_url_final = ""
                if es_entrada and foto_factura_url and foto_factura_url.startswith("Pendiente"):
                    try:
                        with st.spinner("Subiendo foto de factura a Google Drive..."):
                            # Leer archivo
                            archivo_bytes = foto_factura.read()
                            # Crear nombre único
                            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                            nombre_archivo = f"Factura_{numero_factura}_{timestamp}_{foto_factura.name}"
                            # Subir a Drive
                            foto_factura_url_final = db.subir_archivo_a_drive(archivo_bytes, nombre_archivo)
                            if foto_factura_url_final:
                                st.success("✅ Foto de factura subida a Google Drive")
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo subir la foto: {str(e)}")
                        foto_factura_url_final = ""

                for foto in fotos_evidencia or []:
                    try:
                        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        db.subir_archivo_a_drive(foto.getvalue(), f"Evidencia_{nro_remito}_{timestamp}_{foto.name}")
                    except Exception as e:
                        st.warning(f"No se pudo subir la evidencia {foto.name}: {str(e)}")
                
                # Registrar patentes no catalogadas
                if patente_final and patente_final != "-":
                    vehiculos_df = db.get_vehiculos()
                    patentes_catalogadas = vehiculos_df["PATENTE"].str.upper().tolist() if not vehiculos_df.empty else []
                    
                    if patente_final.upper() not in patentes_catalogadas:
                        db.registrar_patente_no_catalogada(
                            patente_final,
                            gerencia=gerencia_final,
                            receptor=receptor_nombre if es_salida else responsable_final,
                            remito_id=nro_remito
                        )
                        st.info(f"⚠️ Patente {patente_final} no catalogada. Se agregó a la lista de PATENTES_NO_CATALOGADAS para revisión.")
                
                # Completar en SQL los datos de factura que se obtuvieron después de guardar el remito.
                db.actualizar_datos_remito(
                    remito_header,
                    numero_factura=numero_factura if es_entrada else "",
                    foto_factura_url=foto_factura_url_final if es_entrada else ""
                )

                email_status_msg = ""
                if (es_salida or es_traspaso) and receptor_email and "@" in receptor_email:
                    ok_mail, msg_mail = send_remito_email(receptor_email, receptor_nombre, nro_remito, pdf_path, tipo_remito=tipo_str)
                    if ok_mail:
                        db.mark_remito_email_sent(nro_remito)
                        email_status_msg = msg_mail
                    else:
                        email_status_msg = f"Aviso de email: {msg_mail}"

            st.session_state["remito_exitoso"] = {
                "nro_remito": nro_remito,
                "pdf_path": pdf_path,
                "header": remito_header,
                "email_status": email_status_msg
            }
            st.rerun()

    with col_btn2:
        if st.button("Limpiar Formulario", use_container_width=True):
            _reset_remito_form()
            st.rerun()