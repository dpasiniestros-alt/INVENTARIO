# Configuración de Supabase

## ⚠️ Importante: SQL es la única fuente de verdad

**La aplicación operativa ahora usa EXCLUSIVAMENTE Supabase (PostgreSQL online).**

- **Google Sheets**: La app solo lee dos libros externos: vehículos y órdenes de trabajo.
- **Informes**: Se conectará más adelante un libro nuevo que leerá Supabase; no forma parte de la app operativa.
- **La aplicación web**: Lee y escribe en Supabase, no en Sheets.
- **Si Supabase no funciona**: La app no inicia. No hay fallback a Sheets.

## 1. Crear las tablas en Supabase

1. Abrir [Supabase Console](https://app.supabase.com) → tu proyecto.
2. Ir a **SQL Editor**.
3. Hacer clic en **New query**.
4. Copiar el contenido completo de `supabase_schema.sql`.
5. Presionar **Run**.

Debe aparecer el mensaje:  
```
Success. No rows returned
```

Luego verificar en **Table Editor** que existan todas las tablas:
- `productos`
- `unidades_serializadas`
- `remitos`
- `remito_items`
- `responsables`
- `receptores`
- `patentes_no_catalogadas`
- `auditoria`

## 2. Configurar Secrets en Streamlit Cloud

En [Streamlit Cloud](https://share.streamlit.io) → tu app `planilla-inventario`:

1. Menú **≡** (arriba a la derecha) → **Settings**.
2. Pestaña **Secrets**.
3. Agregar:

```toml
[supabase]
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "sb_secret_xxxxx..."
```

**Importante**: La clave es privada. No guardarla en GitHub ni compartirla.

## 3. Migración inicial (CRÍTICO)

**Antes de usar la app en producción, importa los datos de Google Sheets:**

En tu máquina local:

```bash
python migrate_to_supabase.py
```

Deberías ver:
```
✓ Migrados 132 productos.
✓ Migradas 1 unidades serializadas.
✓ Migrados 6 responsables.
✓ Migración completada: XXX registros importados.
```

Si falla:
- Verifica que `.streamlit/secrets.toml` tenga los datos de Supabase.
- Verifica que los dos libros de lectura estén compartidos con el `client_email` de la cuenta de servicio.

## 4. Verificación

1. Abre la app en Streamlit Cloud.
2. Prueba agregar un remito o actualizar stock.
3. En Supabase > **Table Editor**, verifica que los datos aparezcan en tiempo real.

## 5. Ante errores

Si la app dice:  
```
⚠️ Supabase no está configurado. Verifica los Secrets en Streamlit Cloud.
Si esto persiste, llama al técnico.
```

**Acciones:**
1. Verifica en Streamlit Cloud que los Secrets están guardados correctamente.
2. Reinicia la app.
3. Si persiste, contacta al técnico (no hay fallback a Sheets).


