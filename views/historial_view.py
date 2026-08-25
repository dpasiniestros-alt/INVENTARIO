# -*- coding: utf-8 -*-
"""
Vista de Historial de Remitos, Descargas y Reenvio de Emails.
"""

import os
import tempfile
import urllib.request
import streamlit as st
import pandas as pd
from modules.gsheets_db import get_db
from modules.pdf_generator import generate_remito_pdf, get_pdf_bytes
from modules.email_sender import send_remito_email

def render_historial_view():
    db = get_db()
    st.markdown("## 📜 Historial de Remitos")
    st.caption("Consulta de remitos de entrada y salida, reimpresión y reenvío de comprobantes")

    df_remitos = db.get_remitos()
    if df_remitos.empty:
        st.info("No se han emitido remitos hasta el momento.")
        return

    df_remitos = df_remitos.iloc[::-1].reset_index(drop=True)

    c_f1, c_f2, c_f3 = st.columns([1, 1, 2])
    with c_f1:
        filtro_tipo = st.selectbox("Filtrar por Tipo:", ["TODOS", "SALIDA", "ENTRADA", "TRASPASO", "BAJA"])
    with c_f2:
        gerencias = ["TODAS"] + sorted(df_remitos["Gerencia"].dropna().unique().tolist()) if "Gerencia" in df_remitos.columns else ["TODAS"]
        filtro_ger = st.selectbox("Filtrar por Gerencia:", gerencias)
    with c_f3:
        query = st.text_input("🔍 Buscar por Remito N°, OT, Patente, Receptor o Responsable:", placeholder="Ej: REM-S-0001, AF395XD, Gomez...").strip().lower()

    df_filt = df_remitos.copy()
    if filtro_tipo != "TODOS":
        df_filt = df_filt[df_filt["Tipo"].str.upper() == filtro_tipo]
    if filtro_ger != "TODAS":
        df_filt = df_filt[df_filt["Gerencia"] == filtro_ger]
    if query:
        df_filt = df_filt[
            df_filt["Nro_Remito"].astype(str).str.lower().str.contains(query, na=False) |
            df_filt.get("Nro_Orden_Taller", pd.Series()).astype(str).str.lower().str.contains(query, na=False) |
            df_filt.get("Patente", pd.Series()).astype(str).str.lower().str.contains(query, na=False) |
            df_filt.get("Receptor_Nombre", pd.Series()).astype(str).str.lower().str.contains(query, na=False) |
            df_filt.get("Responsable_Entrega", pd.Series()).astype(str).str.lower().str.contains(query, na=False)
        ]

    st.write(f"**Se encontraron {len(df_filt)} remito(s):**")

    for _, rem in df_filt.iterrows():
        nro_rem = rem.get("Nro_Remito", "S/N")
        tipo = rem.get("Tipo", "SALIDA")
        fecha = rem.get("Fecha_Hora", "")
        receptor = rem.get("Receptor_Nombre", "-")
        patente = rem.get("Patente", "-")
        ot = rem.get("Nro_Orden_Taller", "-")
        tipo_upper = str(tipo).upper()
        badge = "📤 SALIDA" if tipo_upper == "SALIDA" else ("📥 ENTRADA" if tipo_upper == "ENTRADA" else ("🔄 TRASPASO" if tipo_upper == "TRASPASO" else "🗑️ BAJA"))
        
        ot_txt = f" | OT: {ot}" if ot and str(ot) != "-" and str(ot) != "" else ""
        pat_txt = f" | Patente: {patente}" if patente and str(patente) != "-" and str(patente) != "" else ""
        
        with st.expander(f"**{nro_rem}** [{badge}] - {fecha} - Receptor: {receptor}{pat_txt}{ot_txt}"):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**Responsable Entrega:** {rem.get('Responsable_Entrega', '-')}")
                st.markdown(f"**Persona que Recibe:** {receptor}")
                st.markdown(f"**Correo Receptor:** {rem.get('Receptor_Email', '-')}")
            with col_info2:
                st.markdown(f"**Gerencia:** {rem.get('Gerencia', '-')}")
                st.markdown(f"**Vehículo / Patente:** {patente if patente else 'No aplica'}")
                st.markdown(f"**Orden de Taller (OT):** {ot if ot else 'Sin OT'}")
                st.markdown(f"**Enviado por Email:** {'🟢 SÍ' if rem.get('Enviado_Email') == 'SI' else '⚪ NO'}")

            if rem.get("Observaciones"):
                st.info(f"**Observaciones:** {rem.get('Observaciones')}")

            factura_url = rem.get("Foto_Factura", "")
            numero_factura = rem.get("Numero_Factura", "")
            if numero_factura or factura_url:
                st.markdown(f"**Factura:** {numero_factura or 'Sin número'}")
                if factura_url and str(factura_url).startswith("http"):
                    st.link_button("📎 Ver factura adjunta", str(factura_url), use_container_width=True)
                elif factura_url:
                    st.caption(f"Archivo de factura: {factura_url}")

            df_items = db.get_remito_items(nro_rem)
            if not df_items.empty:
                st.markdown("##### 📦 Artículos Entregados / Recibidos:")
                cols_to_show = [c for c in ["Categoria", "Marca", "Descripcion", "Cantidad", "Nro_Serie_Bateria_Neumatico"] if c in df_items.columns]
                st.dataframe(
                    df_items[cols_to_show],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Nro_Serie_Bateria_Neumatico": st.column_config.TextColumn("N° Serie / Lote / DOT"),
                        "Cantidad": st.column_config.NumberColumn("Cant.", format="%d un.")
                    }
                )
            elif rem.get("Articulo_Principal"):
                st.markdown("##### 📦 Artículo importado:")
                st.write(
                    f"{rem.get('Articulo_Principal')} | {rem.get('Marca', '-')} | "
                    f"{rem.get('Modelo', '-')} | Cantidad: {rem.get('Cantidad', '-') }"
                )

            st.divider()
            c_btn1, c_btn2 = st.columns([1, 2])
            
            pdf_link = str(rem.get("Link_PDF", "") or "")
            pdf_path = pdf_link if os.path.exists(pdf_link) else ""
            pdf_bytes = b""
            if pdf_link.startswith("https://drive.google.com/"):
                pdf_bytes = db.descargar_archivo_de_drive(pdf_link)
            elif pdf_link.startswith("http"):
                try:
                    with urllib.request.urlopen(pdf_link, timeout=30) as response:
                        pdf_bytes = response.read()
                except Exception:
                    pdf_bytes = b""
            if not pdf_bytes and not pdf_path:
                st.warning("El PDF original de este remito no está disponible en el almacenamiento permanente.")

            with c_btn1:
                if pdf_bytes or pdf_path:
                    st.download_button(
                        label="📥 Descargar PDF original",
                        data=pdf_bytes or get_pdf_bytes(pdf_path),
                        file_name=f"{nro_rem}.pdf",
                        mime="application/pdf",
                        key=f"dl_{nro_rem}",
                        use_container_width=True
                    )

            with c_btn2:
                with st.popover("📧 Reenviar por Email"):
                    email_dest = st.text_input("Confirmar o corregir correo:", value=str(rem.get("Receptor_Email", "")), key=f"mail_in_{nro_rem}")
                    if st.button("Enviar Ahora", key=f"btn_mail_{nro_rem}", use_container_width=True):
                        if not email_dest or "@" not in email_dest:
                            st.error("Ingrese un correo válido.")
                        else:
                            temporary_pdf = None
                            if not pdf_path and pdf_bytes:
                                temporary_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                                temporary_pdf.write(pdf_bytes)
                                temporary_pdf.close()
                                pdf_path = temporary_pdf.name
                            ok_mail, msg_mail = send_remito_email(email_dest, receptor, nro_rem, pdf_path, tipo_remito=tipo)
                            if temporary_pdf:
                                os.unlink(temporary_pdf.name)
                            if ok_mail:
                                db.mark_remito_email_sent(nro_rem)
                                st.success(msg_mail)
                                st.rerun()
                            else:
                                st.error(msg_mail)
