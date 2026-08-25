# 🚀 Guía de Despliegue en Streamlit Cloud

## Paso 1: Preparar tu repositorio en GitHub

### 1.1 Inicializar Git (si no lo has hecho)
```bash
cd "c:\Users\GPS\Desktop\Planilla inventario"
git init
git add .
git commit -m "Initial commit: Planilla Inventario setup"
```

### 1.2 Crear un repositorio en GitHub
1. Ve a [github.com](https://github.com) y crea una cuenta (si no tienes)
2. Haz clic en el **+** (arriba a la derecha) → **New repository**
3. Nombre: `planilla-inventario`
4. Descripción: `Sistema de Gestión de Inventario y Remitos Digitales - Taller Automotor`
5. **Privado** (recomendado porque contiene datos sensibles)
6. No inicialices con README ni .gitignore (ya los tienes)
7. Crea el repositorio

### 1.3 Conectar tu código local a GitHub
```bash
git remote add origin https://github.com/TU_USUARIO/planilla-inventario.git
git branch -M main
git push -u origin main
```

Reemplaza `TU_USUARIO` con tu usuario de GitHub.

---

## Paso 2: Desplegar en Streamlit Cloud

### 2.1 Crear cuenta en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Haz clic en **Sign up** → **Sign up with GitHub**
3. Autoriza Streamlit para acceder a tu GitHub

### 2.2 Desplegar la app
1. Una vez en Streamlit Cloud, haz clic en **Create app**
2. Selecciona:
   - Repository: `TU_USUARIO/planilla-inventario`
   - Branch: `main`
   - Main file path: `app.py`
3. Haz clic en **Deploy**

Streamlit comenzará a construir e implementar tu app. **Espera 2-5 minutos**.

### 2.3 Agregar secretos a Streamlit Cloud
1. Una vez desplegada, haz clic en el menú **≡** (arriba a la derecha) → **Settings**
2. Ve a la pestaña **Secrets**
3. **Copia TODO el contenido de tu archivo local** `.streamlit/secrets.toml`
4. **Pégalo** en el editor de Secrets de Streamlit Cloud
5. Haz clic en **Save**

**⚠️ IMPORTANTE:** No expongas tus secretos en el repositorio. El archivo `.gitignore` ya los protege, pero asegúrate de NO hacer git push de `secrets.toml`.

---

## Paso 3: Verificar la conexión con Google Sheets

Una vez que la app esté desplegada:

1. Abre tu app en Streamlit Cloud (URL: `https://share.streamlit.io/TU_USUARIO/planilla-inventario`)
2. En la sidebar, deberías ver un mensaje indicando la conexión con Google Sheets
3. Navega por las diferentes vistas:
   - **Remitos** - Ver y crear remitos
   - **Inventario** - Gestionar stock de productos
   - **Trazabilidad** - Seguimiento de baterías y neumáticos
   - **Órdenes** - Coordinación de trabajo en taller
   - **Historial** - Log de todas las operaciones

---

## Paso 4: Compartir con el equipo

Una vez desplegada, puedes compartir la URL con tu equipo:
```
https://share.streamlit.io/TU_USUARIO/planilla-inventario
```

**Para que otros vean la app**, necesitan:
- El enlace (puede ser público o privado según configuración)
- Los PINs de acceso:
  - Admin: `1234`
  - Taller: `0000`

---

## 🔧 Solución de problemas

### "No puedo conectarme a Google Sheets"
- Verifica que los **secretos estén correctamente copiados** en Streamlit Cloud Settings
- Asegúrate de que la **credencial de Google Cloud es válida**
- Comprueba que los **IDs de los Sheets sean correctos**

### "Error de permisos con Google Drive"
- Ve a [Google Drive](https://drive.google.com)
- Comparte cada Sheet con la email de la cuenta de servicio:
  ```
  EMAIL_DE_LA_NUEVA_CUENTA_DE_SERVICIO
  ```
- Dale permisos de **Editor**

### La app se demora mucho en cargar
- Esto es normal la primera vez (Streamlit descarga todas las dependencias)
- Actualizaciones posteriores serán más rápidas

### Necesito hacer cambios al código
1. Haz cambios localmente en tu editor
2. Haz `git add .` → `git commit -m "descripción"` → `git push`
3. Streamlit Cloud **detectará automáticamente** los cambios y redesplegará en ~30-60 segundos

---

## 📋 Checklist final

- [ ] Repositorio en GitHub creado y código pusheado
- [ ] Cuenta en Streamlit Cloud creada
- [ ] App desplegada en Streamlit Cloud
- [ ] Secretos agregados en Streamlit Cloud Settings
- [ ] Probada la conexión con Google Sheets
- [ ] Probadas todas las vistas (Remitos, Inventario, Órdenes, etc.)
- [ ] Compartida la URL con el equipo
- [ ] Google Sheets compartidos con la cuenta de servicio

---

## 📞 Próximos pasos

Una vez desplegado, podemos:
- Optimizar el rendimiento
- Agregar más funcionalidades
- Configurar notificaciones por email
- Exportar reportes automáticos
- Integrar más Sheets si es necesario
