# -*- coding: utf-8 -*-
"""
Catalogo inicial precargado y datos maestros de la empresa.
"""

GERENCIAS = [
    "AEP",
    "AEP - ITC",
    "DPA GRUPO SIMA",
    "ECOKLIN",
    "EZE",
    "EZE - ITC",
    "GLOBAL",
    "GLOBAL HANDL",
    "GPS EDENOR",
    "LA BIZANTINA",
    "LIB GRUPO SIMA",
    "MOTOS",
    "OTRA"
]

RESPONSABLES_INICIALES = [
    {"nombre": "Anabia, Sebastian", "pin": "1234"},
    {"nombre": "Canela, Agustin", "pin": "1234"},
    {"nombre": "Cordoba, Alan", "pin": "1234"},
    {"nombre": "Gomez, Damian", "pin": "1234"},
    {"nombre": "Machado, Claudio", "pin": "1234"},
    {"nombre": "Serrano, Cristian", "pin": "1234"}
]

# Flota base con AÑO MARCA MODELO
VEHICULOS_INICIALES = [
    {"PATENTE": "AF395XD", "AÑO": "2022", "MARCA": "Fiat", "MODELO": "Cronos 1.3 Drive", "GERENCIA": "GPS EDENOR", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AF395XE", "AÑO": "2022", "MARCA": "Fiat", "MODELO": "Cronos 1.3 Drive", "GERENCIA": "GPS EDENOR", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AF395XF", "AÑO": "2022", "MARCA": "Fiat", "MODELO": "Cronos 1.3 Drive", "GERENCIA": "GPS EDENOR", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AF449PL", "AÑO": "2022", "MARCA": "Renault", "MODELO": "Kangoo II 1.6", "GERENCIA": "GLOBAL", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AF536RA", "AÑO": "2023", "MARCA": "Mercedes-Benz", "MODELO": "Sprinter 416 CDI", "GERENCIA": "AEP", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AG596VA", "AÑO": "2023", "MARCA": "Toyota", "MODELO": "Corolla 2.0", "GERENCIA": "EZE", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AG871VD", "AÑO": "2023", "MARCA": "Ford", "MODELO": "Transit 2.2 TDCI", "GERENCIA": "ECOKLIN", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AH015DD", "AÑO": "2024", "MARCA": "Iveco", "MODELO": "Daily 3.0", "GERENCIA": "LA BIZANTINA", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
    {"PATENTE": "AH565PQ", "AÑO": "2024", "MARCA": "Honda", "MODELO": "XR 150L", "GERENCIA": "MOTOS", "STATUS": "ACTIVO", "FECHA DE BAJA": ""},
]

PATENTES_INICIALES = [
    "A165XKI", "A165XKJ", "A165XKK", "A165XKR", "A192BBO", "A192BBQ", "A192BBR", "A192BBS",
    "A286SLR", "A286SLS", "A286SLT", "A286SLU", "A286SLV", "A286SLW", "A286SLY", "AC699UE",
    "AD306JJ", "AE716OB", "AE716OR", "AE896KP", "AF084JC", "AF084JD", "AF164NO", "AF207TE",
    "AF207TF", "AF272UT", "AF312UB", "AF312UW", "AF327QU", "AF327QV", "AF395XD", "AF395XE",
    "AF395XF", "AF395XG", "AF395XH", "AF395XI", "AF395XJ", "AF395XK", "AF395XL", "AF395XM",
    "AF395XZ", "AF423RA", "AF423RD", "AF423RF", "AF423RH", "AF423RI", "AF423RZ", "AF425OA",
    "AF449PL", "AF449PM", "AF449PN", "AF449PO", "AF477GA", "AF477GB", "AF477GC", "AF513MG",
    "AF513MH", "AF513MI", "AF513MJ", "AF513MV", "AF536RA", "AF536RB", "AF536RD", "AF536RE",
    "AF536RF", "AF536RG", "AF536RH", "AF536RI", "AF665ZL", "AF665ZN", "AF716SJ", "AG120TU",
    "AG120TV", "AG126TQ", "AG257AE", "AG323IH", "AG332MC", "AG332MD", "AG536XV", "AG536XW",
    "AG536XX", "AG536XY", "AG581DK", "AG581DP", "AG581DV", "AG581DW", "AG581DX", "AG581DY",
    "AG581DZ", "AG596VA", "AG596VB", "AG596VC", "AG596VD", "AG596VE", "AG596VF", "AG596VG",
    "AG596VH", "AG596VJ", "AG596VK", "AG596VL", "AG596VM", "AG596VN", "AG596VP", "AG596VQ",
    "AG596VR", "AG596VS", "AG596VT", "AG863FZ", "AG871VD", "AG871VE", "AG871VF", "AG871VG",
    "AG871VH", "AG871VI", "AG871VJ", "AG871VK", "AG871VL", "AG871VM", "AG871VO", "AG871VP",
    "AG871VQ", "AG871VR", "AG871VS", "AG875LE", "AG875LV", "AG882MN", "AG915WG", "AG915WH",
    "AG915WI", "AG915WJ", "AH015DD", "AH015DG", "AH283OQ", "AH283OR", "AH497JW", "AH497JX",
    "AH565PQ", "AH565PR", "AH565PS", "AH565PT", "AH565PU", "AH826SM", "AH826SN", "AI153QP",
    "NMF607"
]

MARCAS_BATERIAS = [
    "USADA", "ACDelco", "Bari", "Bosch", "Dinor", "Edna", "Energy Safe", "Heliar",
    "Herbo", "Mateo", "Moura", "Padua", "Pioneiro", "Prestolite", "Rombat",
    "Sermat", "Tudor", "Varta", "Volta", "Willard", "OTRA"
]

VOLTAJES_BATERIA = ["12V", "6V", "24V"]
AMPERAJES_BATERIA = [
    "4Ah", "5Ah", "6Ah", "7Ah", "9Ah", "10Ah", "12Ah",
    "45Ah", "50Ah", "55Ah", "60Ah", "65Ah", "70Ah", "75Ah", "80Ah", "85Ah", "90Ah", "95Ah", "100Ah", "110Ah", "140Ah", "180Ah", "220Ah"
]

MARCAS_NEUMATICOS = [
    "NEUMATICO AUTO USADO", "NEUMATICO MOTO NUEVO", "NEUMATICO MOTO USADO",
    "Aplus", "BFGoodrich", "Bridgestone", "Continental", "Double Coin", "Dunlop",
    "Fate", "Firemax", "Firestone", "Goodyear", "Hankook", "Kumho", "Linglong",
    "Maxisport", "Michelin", "Onyx", "Pirelli", "Triangle", "Xbri", "Yokohama", "OTRA"
]

ANCHOS_NEUMATICO = [
    "165", "175", "185", "195", "205", "215", "225", "235", "245", "255", "265",
    "90", "100", "110", "120", "130"
]
PERFILES_NEUMATICO = ["45", "50", "55", "60", "65", "70", "75", "80", "85", "90"]
RODADOS_NEUMATICO = ["R13", "R14", "R15", "R16", "R17", "R17.5", "R18", "R19", "R20", "R22.5"]

MARCAS_LUBRICANTES = [
    "Ama Lubricantes", "Axion Energy / Mobil", "Bardahl", "Castrol", "Chevron",
    "Elf", "Eneos", "Fuchs / Fercol", "Gulf", "Honda Genuino", "Ipone",
    "John Deere", "Liqui Moly", "Motul", "Petronas", "Puma Lubricants",
    "Repsol", "Shell", "TotalEnergies", "YPF (Elaion)", "OTRA"
]

BASES_LUBRICANTE = ["Sintetico", "Semi-Sintetico", "Mineral", "2T (2 Tiempos)"]
VISCOSIDADES_LUBRICANTE = [
    "0W-16", "0W-20", "0W-30", "0W-40",
    "5W-20", "5W-30", "5W-40",
    "10W-30", "10W-40", "10W-50", "10W-60",
    "15W-40", "15W-50", "20W-50"
]
ENVASES_LUBRICANTE = ["1 LITRO", "4 LITROS", "20 LITROS", "205 LITROS (Tambor)"]

LAMPARAS = [
    "H1 - Alta - Aux",
    "H11 - Baja - Antiniebla",
    "H4 - Baja y alta",
    "H7 - Alta - Baja",
    "H8 / H16 - Aux",
    "HB3 / 9005 - Alta - Pick-ups",
    "P21/5W / 1034 - Doble polo posición y freno",
    "P21W / 1141 - Marcha atras - Giro",
    "PY21W / 7507 - Un polo AMBAR Giro",
    "R5W / 67 - Posicion un polo chica - Delimitadores de techo",
    "W5W / T10 - Posicion - Interior - Patente"
]

FILTROS_AIRE = [
    {"modelo": "Fiat Cronos 1.3 / 1.8", "codigo_fram": "CA11457", "codigo_mann": "C21014"},
    {"modelo": "Renault Logan / Sandero / Kangoo 1.6 16v (Motor H4M)", "codigo_fram": "CA12291", "codigo_mann": "C27030"},
    {"modelo": "Volkswagen Gol / Voyage 1.6 8v (Motor Trend)", "codigo_fram": "CA10244", "codigo_mann": "C29108"},
    {"modelo": "Toyota Corolla (2014-2020)", "codigo_fram": "CA11418", "codigo_mann": "C24009"},
    {"modelo": "Toyota Corolla (Desde 2020)", "codigo_fram": "CA12423", "codigo_mann": "C25018"},
    {"modelo": "Ford Ecosport 1.5 3cil / 2.0 GDI (Kinetic)", "codigo_fram": "CA12115", "codigo_mann": "C22030"},
    {"modelo": "Renault Alaskan 2.3 dCi", "codigo_fram": "CA12093", "codigo_mann": "C25015"},
    {"modelo": "Citroen Jumpy 1.6 BlueHDi", "codigo_fram": "CA12145", "codigo_mann": "C30012"},
    {"modelo": "Toyota Hiace 2.8 D-4D", "codigo_fram": "CA12674", "codigo_mann": "C32014"},
    {"modelo": "Mercedes-Benz Sprinter (Motor OM 651 - 415/515)", "codigo_fram": "CA11059", "codigo_mann": "C4312X"},
    {"modelo": "Mercedes-Benz Sprinter (Motor OM 654 - 416/516)", "codigo_fram": "CA12869", "codigo_mann": "C25042"},
    {"modelo": "Ford Transit 2.2 / 2.0 TDCI", "codigo_fram": "CA11264", "codigo_mann": "C29011"},
    {"modelo": "Peugeot Boxer / Citroen Jumper 2.2 HDI", "codigo_fram": "CA11218", "codigo_mann": "C30137"},
    {"modelo": "DFSK Mamut Box 1.5", "codigo_fram": "CA12344", "codigo_mann": "C18005"},
    {"modelo": "Iveco Daily 3.0 (16v / Euro 5)", "codigo_fram": "CA10697", "codigo_mann": "C17237"},
    {"modelo": "Mercedes-Benz Accelo 815 / 1016", "codigo_fram": "CA9668", "codigo_mann": "C25710"},
    {"modelo": "Honda XR 150L (Filtro de espuma/aire)", "codigo_fram": "H0133-KRE-G00", "codigo_mann": "MH-2041"}
]

FILTROS_ACEITE = [
    {"modelo": "Fiat Cronos 1.3 / 1.8", "codigo_fram": "PH5949", "codigo_mann": "W6018"},
    {"modelo": "Renault Logan / Sandero / Kangoo 1.6 16v (Motor H4M)", "codigo_fram": "PH5796", "codigo_mann": "W6025"},
    {"modelo": "Volkswagen Gol / Voyage 1.6 8v (Motor Trend)", "codigo_fram": "PH5548", "codigo_mann": "W712/94"},
    {"modelo": "Toyota Corolla (Todos los modelos)", "codigo_fram": "CH10358ECO", "codigo_mann": "HU6006X"},
    {"modelo": "Ford Ecosport 1.5 3cil / 2.0 GDI (Kinetic)", "codigo_fram": "PH10044", "codigo_mann": "W7015"},
    {"modelo": "Renault Alaskan 2.3 dCi", "codigo_fram": "CH11275ECO", "codigo_mann": "HU6011X"},
    {"modelo": "Citroen Jumpy 1.6 BlueHDi", "codigo_fram": "CH11299ECO", "codigo_mann": "HU7018X"},
    {"modelo": "Toyota Hiace 2.8 D-4D", "codigo_fram": "CH11993ECO", "codigo_mann": "HU7023X"},
    {"modelo": "Mercedes-Benz Sprinter (Motor OM 651 / OM 654)", "codigo_fram": "CH11252ECO", "codigo_mann": "HU7010X"},
    {"modelo": "Ford Transit 2.2 / 2.0 TDCI", "codigo_fram": "CH11283ECO", "codigo_mann": "HU7002X"},
    {"modelo": "Peugeot Boxer / Citroen Jumper 2.2 HDI", "codigo_fram": "CH11283ECO", "codigo_mann": "HU7002X"},
    {"modelo": "DFSK Mamut Box 1.5", "codigo_fram": "PH6607", "codigo_mann": "W67/80"},
    {"modelo": "Iveco Daily 3.0 (16v / Euro 5)", "codigo_fram": "PH11221", "codigo_mann": "W10009"},
    {"modelo": "Mercedes-Benz Accelo 815 / 1016", "codigo_fram": "CH11494ECO", "codigo_mann": "HU951X"}
]

ARTICULOS_VARIOS = [
    "AdBlue", "Agua destilada", "Baliza", "Crique", "Liquido de Freno",
    "Liquido Hidraulico", "Liquido Lavaparabrisas", "Liquido Limpia Inyectores",
    "Llave L", "Lubricante de Cadena", "Lubricante Multiuso", "Matafuegos",
    "Refrigerante - Anticongelante", "Kit de seguridad COMPLETO EN BOLSA"
]

REPUESTOS = [
    "Espejo Completo", "Espejo - Solo Carcaza", "Espejo - Solo Espejo",
    "Deposito de agua", "Tapa Deposito de Agua"
]

def get_initial_products():
    products = []
    pid = 1

    for marca in ["Moura", "Bosch", "Willard", "ACDelco", "Varta", "USADA"]:
        for modelo in ["12V 50Ah", "12V 60Ah", "12V 70Ah", "12V 75Ah"]:
            products.append({
                "ID": f"BAT-{pid:04d}",
                "Categoria": "BATERIA",
                "Marca": marca,
                "Modelo_Detalle": modelo,
                "Codigo_Pieza": "-",
                "Stock_Actual": 2,
                "Stock_Minimo": 1,
                "Unidad": "UNIDAD",
                "Requiere_Serial": "SI"
            })
            pid += 1

    for marca in ["Pirelli", "Fate", "Michelin", "Bridgestone", "NEUMATICO AUTO USADO"]:
        for medida in ["175/65R14", "185/65R15", "195/65R15", "205/55R16", "215/65R16"]:
            products.append({
                "ID": f"NEU-{pid:04d}",
                "Categoria": "NEUMATICO",
                "Marca": marca,
                "Modelo_Detalle": medida,
                "Codigo_Pieza": "-",
                "Stock_Actual": 4,
                "Stock_Minimo": 2,
                "Unidad": "UNIDAD",
                "Requiere_Serial": "SI"
            })
            pid += 1

    for marca in ["Shell", "YPF (Elaion)", "TotalEnergies", "Castrol", "Motul"]:
        for tipo in ["Sintetico 5W-30 4 LITROS", "Sintetico 5W-40 4 LITROS", "Semi 10W-40 4 LITROS", "Sintetico 5W-30 1 LITRO"]:
            products.append({
                "ID": f"LUB-{pid:04d}",
                "Categoria": "LUBRICANTE",
                "Marca": marca,
                "Modelo_Detalle": tipo,
                "Codigo_Pieza": "-",
                "Stock_Actual": 6,
                "Stock_Minimo": 2,
                "Unidad": "BIDON/BOTELLA",
                "Requiere_Serial": "NO"
            })
            pid += 1

    for lamp in LAMPARAS:
        products.append({
            "ID": f"LAM-{pid:04d}",
            "Categoria": "LAMPARA",
            "Marca": "Generica / Philips / Osram",
            "Modelo_Detalle": lamp,
            "Codigo_Pieza": "-",
            "Stock_Actual": 10,
            "Stock_Minimo": 5,
            "Unidad": "UNIDAD",
            "Requiere_Serial": "NO"
        })
        pid += 1

    for fa in FILTROS_AIRE:
        products.append({
            "ID": f"FAI-{pid:04d}",
            "Categoria": "FILTRO DE AIRE",
            "Marca": "Fram / Mann",
            "Modelo_Detalle": fa["modelo"],
            "Codigo_Pieza": f"{fa['codigo_fram']} / {fa['codigo_mann']}",
            "Stock_Actual": 3,
            "Stock_Minimo": 1,
            "Unidad": "UNIDAD",
            "Requiere_Serial": "NO"
        })
        pid += 1

    for fo in FILTROS_ACEITE:
        products.append({
            "ID": f"FAC-{pid:04d}",
            "Categoria": "FILTRO DE ACEITE",
            "Marca": "Fram / Mann",
            "Modelo_Detalle": fo["modelo"],
            "Codigo_Pieza": f"{fo['codigo_fram']} / {fo['codigo_mann']}",
            "Stock_Actual": 3,
            "Stock_Minimo": 1,
            "Unidad": "UNIDAD",
            "Requiere_Serial": "NO"
        })
        pid += 1

    for var in ARTICULOS_VARIOS:
        products.append({
            "ID": f"VAR-{pid:04d}",
            "Categoria": "VARIOS",
            "Marca": "Varios",
            "Modelo_Detalle": var,
            "Codigo_Pieza": "-",
            "Stock_Actual": 5,
            "Stock_Minimo": 2,
            "Unidad": "UNIDAD",
            "Requiere_Serial": "NO"
        })
        pid += 1

    for rep in REPUESTOS:
        products.append({
            "ID": f"REP-{pid:04d}",
            "Categoria": "REPUESTO",
            "Marca": "Original / Generico",
            "Modelo_Detalle": rep,
            "Codigo_Pieza": "-",
            "Stock_Actual": 2,
            "Stock_Minimo": 1,
            "Unidad": "UNIDAD",
            "Requiere_Serial": "NO"
        })
        pid += 1

    return products
