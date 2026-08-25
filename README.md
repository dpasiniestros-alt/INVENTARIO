# 🚗 Sistema de Remitos e Inventario Digital - Taller Automotor

Aplicación web desarrollada en **Streamlit** para la gestión ágil de remitos de entrada/salida, control de stock en tiempo real, trazabilidad de números de serie (baterías y neumáticos), firma manuscrita táctil, generación de comprobantes en PDF, envío automático por correo electrónico e integración directa con **Google Sheets**.

---

## 📱 Características Principales

- **Optimizado para Celulares**: Diseñado para ser utilizado de forma táctil en el taller desde navegadores móviles.
- **Remitos de Salida con Validación de Stock**: Selección directa desde el stock disponible (evita entregar artículos que no están en inventario).
- **Remitos de Entrada**: Permite sumar existencias de productos existentes o registrar nuevos artículos en el momento.
- **Trazabilidad**: Registro de Número de Serie / Lote / DOT para Baterías y Neumáticos.
- **Órdenes de Taller (OT)**: Vinculación de remitos a solicitudes u órdenes de trabajo pendientes.
- **Firma Manuscrita en Pantalla**: Lienzo digital táctil para que la persona que retira firme en el teléfono.
- **Generación de PDF**: Remitos oficiales con diseño profesional, membrete y firma digital estampada.
- **Envío Automático por Email**: Despacho automático del remito en PDF al correo del destinatario.
- **Historial & Reenvíos**: Consulta de movimientos históricos, descarga de comprobantes y reenvío de correos.
- **Panel de Control**: Edición de datos de receptores (para corregir errores tipográficos en emails), flota de patentes (ACTIVO, BAJA, ACTIVO (OTROS)), responsables y ajustes de stock.
- **100% en la Nube (Google Sheets)**: No requiere tener ninguna computadora encendida. Funciona 24/7 conectado a tu hoja de cálculo.

---

## 🚀 Puesta en Marcha Local (Para Pruebas)

1. **Instalar dependencias**:
   `ash
   pip install -r requirements.txt
   `

2. **Iniciar la aplicación**:
   `ash
   streamlit run app.py
   `

La aplicación se abrirá automáticamente en tu navegador web (por defecto http://localhost:8501).

---

## ☁️ Despliegue 100% Online en Streamlit Community Cloud (Gratis)

### Paso 1: Subir el proyecto a GitHub
1. Crea un nuevo repositorio en [GitHub.com](https://github.com) (por ejemplo 	aller-inventario-remitos).
2. En tu computadora, dentro de la carpeta del proyecto, ejecuta:
   `ash
   git init
   git add .
   git commit -m \"Version inicial del sistema de remitos e inventario\"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/taller-inventario-remitos.git
   git push -u origin main
   `

### Paso 2: Desplegar en Streamlit Cloud
1. Entra a [share.streamlit.io](https://share.streamlit.io/) e inicia sesión con tu cuenta de GitHub.
2. Haz clic en **\"New app\"**.
3. Selecciona tu repositorio TU_USUARIO/taller-inventario-remitos, rama main, y archivo principal pp.py.
4. Haz clic en **\"Deploy!\"**. En un par de minutos tu aplicación estará online en una URL pública (ej. https://taller-automotor.streamlit.app).

---

## 🔐 Configuración de Secrets (Google Sheets & Correo Electrónico)

La migración hacia Supabase está preparada en `supabase_schema.sql`. Antes de activar
la nueva base online, ejecuta ese archivo en el SQL Editor de Supabase y configura los
Secrets indicados en `SUPABASE_SETUP.md`.

En Streamlit Cloud, entra a tu App, ve a **Settings > Secrets**, y pega la configuración:

`	oml
ADMIN_PIN = \"1234\"
GSHEET_SPREADSHEET_ID = \"1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU\"

# Credenciales de Google Cloud Service Account
[gcp_service_account]
type = \"service_account\"
project_id = \"tu-proyecto-google\"
private_key_id = \"...\"
private_key = \"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n\"
client_email = \"tu-servicio@tu-proyecto.iam.gserviceaccount.com\"
client_id = \"...\"
auth_uri = \"https://accounts.google.com/o/oauth2/auth\"
token_uri = \"https://oauth2.googleapis.com/token\"
auth_provider_x509_cert_url = \"https://www.googleapis.com/oauth2/v1/certs\"
client_x509_cert_url = \"https://www.googleapis.com/robot/v1/metadata/x509/...\"

# Configuracion de Correo Electronico (Gmail)
[email]
smtp_server = \"smtp.gmail.com\"
smtp_port = 587
sender_email = \"taller.empresa@gmail.com\"
sender_password = \"xxxx xxxx xxxx xxxx\" # Contraseña de aplicación de 16 letras de Google
sender_name = \"Taller Automotor - Remitos Digitales\"
copy_to_taller = \"taller.empresa@gmail.com\"
`

> **Nota**: Para conectar con Google Sheets, solo debes compartir tu planilla de Google Sheets con el correo client_email de tu cuenta de servicio de Google Cloud dándole permiso de **Editor**.
# INVENTARIO
