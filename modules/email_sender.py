# -*- coding: utf-8 -*-
"""
Modulo de Envio Automatico de Remitos por Email (SMTP).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st

def send_remito_email(destinatario_email: str, destinatario_nombre: str, nro_remito: str, pdf_path: str, tipo_remito: str = "SALIDA") -> tuple[bool, str]:
    if not destinatario_email or "@" not in destinatario_email:
        return False, "El destinatario no tiene una dirección de correo válida."

    email_cfg = {}
    if hasattr(st, "secrets") and "email" in st.secrets:
        email_cfg = st.secrets["email"]

    if not email_cfg or not email_cfg.get("sender_email") or not email_cfg.get("sender_password"):
        return False, "Configuración SMTP no establecida en secrets.toml. Complete las credenciales de correo."

    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = int(email_cfg.get("smtp_port", 587))
    sender_email = email_cfg.get("sender_email")
    sender_password = email_cfg.get("sender_password")
    sender_name = email_cfg.get("sender_name", "Taller Automotor")
    copy_taller = email_cfg.get("copy_to_taller", "")

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = destinatario_email
        msg['Subject'] = f"Comprobante Digital: Remito de {tipo_remito} N° {nro_remito}"

        recipients = [destinatario_email]
        if copy_taller and copy_taller != destinatario_email:
            msg['Cc'] = copy_taller
            recipients.append(copy_taller)

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #334155; line-height: 1.6;">
            <div style="max-width: 600px; margin: auto; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #0284C7; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">Comprobante de Remito Digital</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Departamento Automotor - Área de Taller</p>
                </div>
                <div style="padding: 24px;">
                    <p>Estimado/a <strong>{destinatario_nombre}</strong>,</p>
                    <p>Adjunto a este correo encontrará el remito oficial correspondiente al movimiento de taller:</p>
                    <div style="background-color: #F8FAFC; border-left: 4px solid #0284C7; padding: 12px 16px; margin: 16px 0;">
                        <p style="margin: 4px 0;"><strong>N° de Remito:</strong> {nro_remito}</p>
                        <p style="margin: 4px 0;"><strong>Tipo de Movimiento:</strong> Remito de {tipo_remito}</p>
                    </div>
                    <p>Este documento contiene el detalle completo de los artículos entregados/recibidos y la conformidad registrada.</p>
                    <p style="font-size: 12px; color: #64748B; margin-top: 24px;">Este es un mensaje generado automáticamente por el Sistema de Remitos de Taller.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                filename = os.path.basename(pdf_path)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())

        return True, f"Email enviado con éxito a {destinatario_email}"
    except Exception as e:
        return False, f"Error al enviar correo: {str(e)}"
