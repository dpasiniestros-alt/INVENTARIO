# ✅ Configuración Lista para Despliegue

## Resumen de cambios realizados

### 1. **Credenciales de Google Cloud** ✅
- Archivo: [.streamlit/secrets.toml](.streamlit/secrets.toml)
- ✓ Agregada credencial de `planilla-inventario@inventario-505919.iam.gserviceaccount.com`
- ✓ Credencial protegida en `.gitignore` (no se subirá a GitHub)

### 2. **Google Sheets Configurados** ✅
```
GSHEET_VEHICULOS_ID = "1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU"
GSHEET_INVENTARIO_ID = "1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg"
GSHEET_ORDENES_ID = "1yR1k8wufRB108ZEekYaXkT8Q3GlfRKfMej3HDbWRjLY"
```

### 3. **Código Actualizado** ✅
- Archivo: [modules/gsheets_db.py](modules/gsheets_db.py)
- ✓ Agregado soporte para Sheet de "Órdenes de Trabajo"
- ✓ Ahora conecta automáticamente con los 3 Sheets

### 4. **Protección de Secretos** ✅
- Archivo: [.gitignore](.gitignore)
- ✓ `.streamlit/secrets.toml` está protegido
- ✓ No se subirá la credencial a GitHub

---

## ⚠️ PASO CRÍTICO: Compartir Google Sheets

Antes de desplegar en la nube, **DEBE compartir cada Sheet** con la cuenta de servicio:

1. Ve a cada Google Sheet:
   - [Vehículos/Flota](https://docs.google.com/spreadsheets/d/1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU/)
   - [Inventario/Remitos](https://docs.google.com/spreadsheets/d/1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg/)
   - [Órdenes de Trabajo](https://docs.google.com/spreadsheets/d/1yR1k8wufRB108ZEekYaXkT8Q3GlfRKfMej3HDbWRjLY/)

2. Haz clic en **Compartir** (arriba a la derecha)

3. Pega este email:
   ```
   planilla-inventario@inventario-505919.iam.gserviceaccount.com
   ```

4. Dale permisos de **Editor**

5. Haz clic en **Compartir**

**Repite para los 3 Sheets.**

---

## 🚀 Próximos pasos para desplegar

Sigue esta guía en orden:

### Paso 1: Preparar GitHub
```bash
cd "c:\Users\GPS\Desktop\Planilla inventario"
git init
git add .
git commit -m "Initial commit: Sistema de Inventario"
git remote add origin https://github.com/TU_USUARIO/planilla-inventario.git
git branch -M main
git push -u origin main
```

### Paso 2: Desplegar en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Crea una cuenta con GitHub
3. Haz clic en **Create app**
4. Selecciona: 
   - Repository: `TU_USUARIO/planilla-inventario`
   - Branch: `main`
   - Main file: `app.py`

### Paso 3: Agregar Secretos en Streamlit Cloud
1. Una vez desplegada la app, ve a **≡** → **Settings**
2. Pestaña **Secrets**
3. Copia TODO el contenido de `.streamlit/secrets.toml`
4. Pégalo en el editor
5. Haz clic en **Save**

### Paso 4: Validar funcionamiento
- Abre tu app: `https://share.streamlit.io/TU_USUARIO/planilla-inventario`
- Verifica que veas los datos de los Google Sheets
- Prueba crear un remito, ver inventario, etc.

---

## 📞 Detalles de la configuración

### Archivo de Secretos Local
- **Ubicación:** `.streamlit/secrets.toml`
- **Uso:** Streamlit Lee esta archivo en desarrollo local
- **Seguridad:** Está en `.gitignore`, no se sube a GitHub
- **En la nube:** Debes copiar el contenido en Streamlit Cloud Settings

### Variables de Entorno
| Variable | Valor |
|----------|-------|
| `GSHEET_VEHICULOS_ID` | `1ZLxa6UaMNJ8irgTUNqPhLr2qENyMLwXnJY8B-y0UlVU` |
| `GSHEET_INVENTARIO_ID` | `1oWdR8mEhS2oe7XyhGMI_SAEQOmPPd46Z2Rf5lyexCxg` |
| `GSHEET_ORDENES_ID` | `1yR1k8wufRB108ZEekYaXkT8Q3GlfRKfMej3HDbWRjLY` |

### Cuenta de Servicio
| Campo | Valor |
|-------|-------|
| **Email** | `planilla-inventario@inventario-505919.iam.gserviceaccount.com` |
| **Project ID** | `inventario-505919` |
| **Permiso requerido** | Editor en cada Google Sheet |

---

## 🆘 Solución de problemas frecuentes

### "Permiso denegado al conectar con Google Sheets"
**Solución:** Compartir cada Sheet con la cuenta de servicio (ver paso ⚠️ arriba)

### "Error: gcp_service_account not found in secrets"
**Solución:** Verificar que copiaste TODO el contenido de `secrets.toml` en Streamlit Cloud Settings (incluyendo la sección `[gcp_service_account]`)

### "La app demora mucho en cargar"
**Solución:** Normal en el primer despliegue. Actualizaciones posteriores serán más rápidas.

### "Cambié el código pero no se actualiza en la nube"
**Solución:** 
1. Haz `git add .` → `git commit` → `git push`
2. Streamlit Cloud redesplegará automáticamente en ~30-60 segundos

---

## 📋 Checklist Final

- [ ] Leí toda esta guía
- [ ] Compartí los 3 Google Sheets con `planilla-inventario@inventario-505919.iam.gserviceaccount.com`
- [ ] Creé cuenta en GitHub (si no tenía)
- [ ] Subí el código a GitHub
- [ ] Creé cuenta en Streamlit Cloud
- [ ] Desplegué la app
- [ ] Copié los secretos en Streamlit Cloud Settings
- [ ] Probé que funciona la app en la nube
- [ ] Probé crear un remito, ver inventario, órdenes, etc.

¡Una vez hecho todo esto, tu app estará lista en la nube! 🎉
