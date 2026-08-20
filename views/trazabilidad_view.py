# -*- coding: utf-8 -*-
"""
Vista de Trazabilidad y Seguimiento Individual de Baterias y Neumaticos.
"""

import streamlit as st
import pandas as pd
from modules.gsheets_db import get_db

def render_trazabilidad_view():
    db = get_db()
    st.markdown("## 🔍 Trazabilidad de Baterías y Neumáticos")
    st.caption("Seguimiento individual por número marcado: historial de vehículos, fechas y movimientos")

    tab_buscar, tab_general, tab_editar = st.tabs([
        "🔎 Consultar por Número",
        "📋 Listado General de Unidades",
        "✏️ Asignar / Modificar Números"
    ])

    units = db.get_unidades_seriales()

    # -------------------------------------------------------------
    # TAB 1: BUSCADOR POR NUMERO
    # -------------------------------------------------------------
    with tab_buscar:
        st.markdown("### 🔎 Buscar Historial de Unidad")
        
        # Sugerencias de numeros existentes
        nums_existentes = [str(u.get("Numero_Marcado")) for u in units]
        
        c_s1, c_s2 = st.columns([2, 1])
        with c_s1:
            q_num = st.text_input("Ingrese o busque el número marcado de Batería o Neumático:", placeholder="Ej: 32, 1, 52, 4, BAT-101...").strip()
        with c_s2:
            st.markdown("<br/>", unsafe_allow_html=True)
            btn_buscar = st.button("Buscar Historial", use_container_width=True)

        if q_num:
            unidad_info = db.buscar_historial_unidad(q_num)
            if unidad_info:
                st.divider()
                # Encabezado de la unidad
                estado = unidad_info.get("Estado", "EN STOCK")
                badge = "🟢 EN STOCK (DISPONIBLE)" if estado == "EN STOCK" else ("🔵 EN VEHÍCULO" if estado == "EN VEHICULO" else "🔴 BAJA")
                
                col_u1, col_u2 = st.columns([2, 2])
                with col_u1:
                    st.markdown(f"### Número Marcado: **#{unidad_info.get('Numero_Marcado')}**")
                    st.markdown(f"**Tipo:** {unidad_info.get('Tipo_Articulo')}")
                    st.markdown(f"**Marca:** {unidad_info.get('Marca')}")
                    st.markdown(f"**Modelo / Medida:** {unidad_info.get('Modelo_Medida')}")
                with col_u2:
                    st.markdown(f"#### Estado: **{badge}**")
                    if estado == "EN VEHICULO":
                        st.info(f"📍 **Vehículo Actual:** {unidad_info.get('Vehiculo_Actual', '-')}")
                    else:
                        st.success("🏢 Ubicación actual: **Taller Automotor (Disponible)**")
                    st.markdown(f"**Última actualización:** {unidad_info.get('Fecha_Ultimo_Movimiento', '-')}")

                st.divider()
                st.markdown("#### 📜 Línea de Tiempo y Recorrido Histórico:")
                
                historial = unidad_info.get("Historial", [])
                if historial:
                    for i, h in enumerate(reversed(historial), start=1):
                        tipo_mov = h.get("Tipo", "")
                        fecha = h.get("Fecha", "")
                        rem = h.get("Nro_Remito", "")
                        detalle = h.get("Detalle", "")
                        
                        icon = "📥" if "INGRESO" in tipo_mov else ("📤" if "SALIDA" in tipo_mov else "🔄")
                        with st.container():
                            st.markdown(f"**{icon} {fecha}** - *{tipo_mov}* | Remito: `{rem}`")
                            st.markdown(f"> {detalle}")
                            if h.get("Receptor"):
                                st.caption(f"Receptor: {h.get('Receptor')} | Responsable Taller: {h.get('Responsable', '-')}")
                            st.markdown("---")
                else:
                    st.write("No hay eventos registrados para esta unidad.")
            else:
                st.warning(f"No se encontró ninguna batería o neumático con el número marcado **#{q_num}**.")

    # -------------------------------------------------------------
    # TAB 2: LISTADO GENERAL
    # -------------------------------------------------------------
    with tab_general:
        st.markdown("### 📋 Todas las Unidades Registradas")
        
        df_units = pd.DataFrame(units)
        if not df_units.empty:
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                tipo_f = st.selectbox("Filtrar por Tipo:", ["TODOS", "BATERIA", "NEUMATICO"])
            with c_f2:
                est_f = st.selectbox("Filtrar por Estado:", ["TODOS", "EN STOCK", "EN VEHICULO"])

            df_show = df_units.copy()
            if tipo_f != "TODOS":
                df_show = df_show[df_show["Tipo_Articulo"] == tipo_f]
            if est_f != "TODOS":
                df_show = df_show[df_show["Estado"] == est_f]

            cols_to_disp = ["Numero_Marcado", "Tipo_Articulo", "Marca", "Modelo_Medida", "Estado", "Vehiculo_Actual", "Fecha_Ultimo_Movimiento"]
            st.dataframe(
                df_show[cols_to_disp],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Numero_Marcado": st.column_config.TextColumn("N° Marcado"),
                    "Tipo_Articulo": st.column_config.TextColumn("Tipo"),
                    "Modelo_Medida": st.column_config.TextColumn("Modelo / Medida"),
                    "Vehiculo_Actual": st.column_config.TextColumn("Vehículo Asignado"),
                    "Fecha_Ultimo_Movimiento": st.column_config.TextColumn("Último Movimiento")
                }
            )
        else:
            st.info("No hay unidades registradas aún.")

    # -------------------------------------------------------------
    # TAB 3: ASIGNAR / MODIFICAR NUMEROS
    # -------------------------------------------------------------
    with tab_editar:
        st.markdown("### ✏️ Modificar o Asignar Número Marcado")
        st.info("Utilice esta opción si ingresó unidades a stock pero aún no las había marcado con su número definitivo.")

        if units:
            opciones_u = [
                f"{'⚠️ ' if str(u.get('Numero_Marcado', '')).startswith('SIN_MARCAR-') else ''}#{u['Numero_Marcado']} | [{u['Tipo_Articulo']}] {u['Marca']} - {u['Modelo_Medida']} ({u['Estado']})"
                for u in units
            ]
            sel_u_edit = st.selectbox("Seleccione la unidad a modificar:", opciones_u)
            
            num_actual = sel_u_edit.split("|")[0].replace("#", "").replace("⚠️", "").strip()
            u_obj = db.buscar_historial_unidad(num_actual)

            if u_obj:
                with st.form("form_edit_num"):
                    c_n1, c_n2 = st.columns(2)
                    with c_n1:
                        nuevo_num = st.text_input("Nuevo Número Marcado:", value=str(u_obj.get("Numero_Marcado", ""))).strip()
                        nuevo_estado = st.selectbox("Estado de la Unidad:", ["EN STOCK", "EN VEHICULO", "BAJA / SCRAP"], index=0 if u_obj.get("Estado") == "EN STOCK" else 1)
                    with c_n2:
                        df_veh = db.get_vehiculos(solo_activos=True)
                        pats = ["Sin Vehículo (En Taller)"] + sorted(df_veh["ETIQUETA_COMPLETA"].dropna().unique().tolist())
                        
                        idx_v = 0
                        if u_obj.get("Vehiculo_Actual") in pats:
                            idx_v = pats.index(u_obj.get("Vehiculo_Actual"))
                        
                        nuevo_veh = st.selectbox("Vehículo Asignado:", pats, index=idx_v)

                    motivo_mod = st.text_input("Motivo de la Modificación:", placeholder="Ej: Corrección de grabado, marcado tardío...")

                    if st.form_submit_button("Guardar Cambios de Unidad", use_container_width=True):
                        if not nuevo_num:
                            st.error("Debe ingresar un número.")
                        elif any(
                            str(item.get("Numero_Marcado", "")).strip().upper() == nuevo_num.upper()
                            and str(item.get("Numero_Marcado", "")).strip().lower() != num_actual.lower()
                            and str(item.get("Tipo_Articulo", "")).strip().upper() == str(u_obj.get("Tipo_Articulo", "")).strip().upper()
                            for item in units
                        ):
                            st.error(f"El número {nuevo_num} ya existe para otra unidad del mismo tipo. Verifique el marcado físico.")
                        else:
                            # Actualizar en lista
                            for item in units:
                                if str(item.get("Numero_Marcado")).strip().lower() == num_actual.lower():
                                    item["Numero_Marcado"] = nuevo_num
                                    item["Estado"] = nuevo_estado
                                    item["Vehiculo_Actual"] = "" if nuevo_veh == "Sin Vehículo (En Taller)" else nuevo_veh
                                    item["Fecha_Ultimo_Movimiento"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                                    if motivo_mod:
                                        item["Historial"].append({
                                            "Fecha": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                                            "Tipo": "MODIFICACION MANUAL",
                                            "Detalle": motivo_mod
                                        })
                                    break
                            db.save_unidades_seriales(units)
                            st.success(f"Unidad actualizada al número #{nuevo_num}.")
                            st.rerun()