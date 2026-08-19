# -*- coding: utf-8 -*-
"""
Script para procesar datos del formulario y crear BASE_DATOS_REMITOS
"""

import os
import sys
import csv
import json
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.gsheets_db import DatabaseManager

def procesar_csv(csv_path):
    """Lee el CSV y extrae datos relevantes"""
    datos = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extraer datos principales
            fecha_str = row.get('Marca temporal', '').split()[0]
            hora_str = row.get('Marca temporal', '').split()[1] if ' ' in row.get('Marca temporal', '') else '00:00:00'
            
            responsable = row.get('Responsable - Apellido y Nombre', '').strip()
            tipo_remito = row.get('Tipo de remito', '').strip()
            articulo_principal = row.get('Tipo de articulo', '').strip()
            
            # Para salidas
            receptor = row.get('Apellido y Nombre de quien recibe:', '').strip()
            email_receptor = row.get('Correo - Ingresa la casilla de mail de quien recibe:', '').strip()
            gerencia = row.get('Al servicio de', '').strip()
            patente = row.get('Patente/s (en caso de corresponder)', '').strip()
            region = row.get('Usted eligio Gerencia EDENOR, indique la region:', '').strip()
            
            # Si está vacío, saltar
            if not responsable or not tipo_remito:
                continue
            
            remito_data = {
                'FECHA': fecha_str,
                'HORA': hora_str,
                'RESPONSABLE': responsable,
                'TIPO_REMITO': tipo_remito,
                'ARTICULO_PRINCIPAL': articulo_principal,
                'MARCA': '',
                'MODELO': '',
                'CANTIDAD': 0,
                'GERENCIA': gerencia if tipo_remito == 'Salida' else '',
                'PATENTE': patente if tipo_remito == 'Salida' else '',
                'RECEPTOR': receptor if tipo_remito == 'Salida' else '',
                'EMAIL_RECEPTOR': email_receptor if tipo_remito == 'Salida' else '',
                'REGION_EDENOR': region if tipo_remito == 'Salida' else '',
                'NUMERO_FACTURA': '',
                'FOTO_FACTURA': '',
                'OBSERVACIONES': row.get('Repuesto', '').strip(),
                'ESTADO': 'Procesado',
                'FECHA_PROCESAMIENTO': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extraer marca y cantidad según tipo de artículo
            if 'BATERIA' in articulo_principal.upper():
                marca = row.get('Marca de Bateria', '').strip()
                # Buscar cantidad en columnas de baterías
                for col_name in row.keys():
                    if '12V' in col_name:
                        qty = row.get(col_name, '').strip()
                        if qty and qty != '' and qty != '0':
                            try:
                                cantidad = int(qty)
                                if cantidad != 0:
                                    remito_data['MARCA'] = marca
                                    remito_data['MODELO'] = col_name.strip('[]')
                                    remito_data['CANTIDAD'] = cantidad
                                    datos.append(remito_data.copy())
                                    remito_data['CANTIDAD'] = 0
                            except:
                                pass
                
                # Si no encontró cantidad, crear un registro igual
                if remito_data['CANTIDAD'] == 0 and marca:
                    remito_data['MARCA'] = marca
                    datos.append(remito_data)
            
            elif 'NEUMATICO' in articulo_principal.upper():
                marca = row.get('Marca de neumatico', '').strip()
                for col_name in row.keys():
                    if any(x in col_name for x in ['R14', 'R15', 'R16', 'R17', 'R19']):
                        qty = row.get(col_name, '').strip()
                        if qty and qty != '' and qty != '0':
                            try:
                                cantidad = int(qty)
                                if cantidad != 0:
                                    remito_data['MARCA'] = marca
                                    remito_data['MODELO'] = col_name.strip('[]')
                                    remito_data['CANTIDAD'] = cantidad
                                    datos.append(remito_data.copy())
                                    remito_data['CANTIDAD'] = 0
                            except:
                                pass
                
                if remito_data['CANTIDAD'] == 0 and marca:
                    remito_data['MARCA'] = marca
                    datos.append(remito_data)
            
            elif 'LUBRICANTE' in articulo_principal.upper():
                marca = row.get('Marca Lubricante', '').strip()
                # Buscar viscosidades
                viscosidades = ['0W-16', '0W-20', '0W-30', '0W-40', '5W-20', '5W-30', '5W-40', 
                               '10W-30', '10W-40', '10W-50', '10W-60', '15W-50', '20W-50', '2T']
                for visc in viscosidades:
                    for col_name in row.keys():
                        if visc in col_name:
                            qty = row.get(col_name, '').strip()
                            if qty and qty != '' and qty != '0':
                                try:
                                    cantidad = int(qty)
                                    if cantidad != 0:
                                        remito_data['MARCA'] = marca
                                        remito_data['MODELO'] = col_name.strip('[]')
                                        remito_data['CANTIDAD'] = cantidad
                                        datos.append(remito_data.copy())
                                        remito_data['CANTIDAD'] = 0
                                except:
                                    pass
                
                if remito_data['CANTIDAD'] == 0 and marca:
                    remito_data['MARCA'] = marca
                    datos.append(remito_data)
            
            elif 'LAMPARA' in articulo_principal.upper() or 'LAMPARA' in articulo_principal.upper():
                for col_name in row.keys():
                    if any(x in col_name for x in ['H1', 'H4', 'H7', 'H11', 'P21']):
                        qty = row.get(col_name, '').strip()
                        if qty and qty != '' and qty != '0':
                            try:
                                cantidad = int(qty)
                                if cantidad != 0:
                                    remito_data['MODELO'] = col_name.strip('[]')
                                    remito_data['CANTIDAD'] = cantidad
                                    datos.append(remito_data.copy())
                                    remito_data['CANTIDAD'] = 0
                            except:
                                pass
            
            elif 'VARIOS' in articulo_principal.upper():
                # Para varios, buscar en la columna de observaciones
                remito_data['MODELO'] = 'Artículos varios'
                datos.append(remito_data)
            
            elif 'REPUESTO' in articulo_principal.upper():
                repuesto = row.get('Repuesto', '').strip()
                remito_data['MODELO'] = repuesto if repuesto else 'Repuesto'
                datos.append(remito_data)
            
            else:
                # Por defecto, agregar aunque sea
                datos.append(remito_data)
    
    return datos

def crear_hoja_y_insertar(db, datos):
    """Crea la hoja BASE_DATOS_REMITOS e inserta los datos"""
    
    if not db.spreadsheet_inventario:
        print("❌ No hay conexión con el LIBRO Inventario/Remitos")
        return False
    
    try:
        # Intentar obtener la hoja, si no existe, crearla
        try:
            sheet = db.spreadsheet_inventario.worksheet('BASE_DATOS_REMITOS')
            print("✅ Hoja BASE_DATOS_REMITOS ya existe")
            # Limpiar la hoja (mantener encabezados)
            sheet.clear()
        except:
            print("📝 Creando nueva hoja BASE_DATOS_REMITOS...")
            sheet = db.spreadsheet_inventario.add_worksheet(title='BASE_DATOS_REMITOS', rows=1000, cols=20)
        
        # Encabezados
        headers = [
            'ID_REMITO', 'FECHA', 'HORA', 'RESPONSABLE', 'TIPO_REMITO', 
            'ARTICULO_PRINCIPAL', 'MARCA', 'MODELO', 'CANTIDAD',
            'GERENCIA', 'PATENTE', 'RECEPTOR', 'EMAIL_RECEPTOR', 'REGION_EDENOR',
            'NUMERO_FACTURA', 'FOTO_FACTURA', 'OBSERVACIONES', 'ESTADO', 'FECHA_PROCESAMIENTO'
        ]
        
        sheet.append_row(headers)
        print(f"✅ Encabezados insertados")
        
        # Insertar datos
        for idx, dato in enumerate(datos, 1):
            id_remito = f"REM-{idx:06d}"
            row = [
                id_remito,
                dato['FECHA'],
                dato['HORA'],
                dato['RESPONSABLE'],
                dato['TIPO_REMITO'],
                dato['ARTICULO_PRINCIPAL'],
                dato['MARCA'],
                dato['MODELO'],
                dato['CANTIDAD'],
                dato['GERENCIA'],
                dato['PATENTE'],
                dato['RECEPTOR'],
                dato['EMAIL_RECEPTOR'],
                dato['REGION_EDENOR'],
                dato['NUMERO_FACTURA'],
                dato['FOTO_FACTURA'],
                dato['OBSERVACIONES'],
                dato['ESTADO'],
                dato['FECHA_PROCESAMIENTO']
            ]
            sheet.append_row(row)
            
            if idx % 10 == 0:
                print(f"✅ Insertados {idx} registros...")
        
        print(f"✅ ¡Listo! {len(datos)} remitos insertados en BASE_DATOS_REMITOS")
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Ruta del CSV
    csv_path = r"c:\Users\GPS\Downloads\Remitos Entrada_Salida - Inventario (respuestas)2 - Respuestas de formulario 1.csv"
    
    print("🔄 Procesando datos del formulario...")
    datos = procesar_csv(csv_path)
    print(f"✅ {len(datos)} registros procesados")
    
    print("\n🔗 Conectando con Google Sheets...")
    db = DatabaseManager()
    
    if db.is_connected_gsheets:
        print("✅ Conexión exitosa")
        crear_hoja_y_insertar(db, datos)
    else:
        print("❌ No hay conexión con Google Sheets")
