# -*- coding: utf-8 -*-
import csv
import random
from datetime import datetime, timedelta

# Fijar semilla para reproducibilidad
random.seed(42)

# Listas base
NOMBRES = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Lucia", "Pedro", "Elena", "Diego", "Sofia", 
           "Manuel", "Carmen", "Rosa", "Jose", "Javier", "Patricia", "Fiorella", "Christian", "Katia", "Fernando"]
APELLIDOS = ["Gomez", "Perez", "Rodriguez", "Lopez", "Garcia", "Martinez", "Sanchez", "Torres", 
             "Flores", "Diaz", "Vargas", "Rojas", "Vasquez", "Castro", "Romero", "Mendoza"]

# Coordenadas de referencia de las capitales distritales de Lambayeque
PROVINCIAS_GPS = {
    'Chiclayo': {
        'Chiclayo': (-6.7714, -79.8409),
        'La Victoria': (-6.7956, -79.8441),
        'José Leonardo Ortiz': (-6.7485, -79.8353),
        'Pimentel': (-6.8366, -79.9344),
        'Monsefú': (-6.8788, -79.8721),
        'Reque': (-6.8658, -79.8177),
        'Pomalca': (-6.7686, -79.7734),
    },
    'Lambayeque': {
        'Lambayeque': (-6.7011, -79.9063),
        'Mochumí': (-6.5438, -79.8621),
        'Túcume': (-6.5078, -79.8589),
        'Íllimo': (-6.4665, -79.8542),
        'Pacora': (-6.4305, -79.8388),
        'Olmos': (-5.9847, -79.7454),
    },
    'Ferreñafe': {
        'Ferreñafe': (-6.6389, -79.7889),
        'Pueblo Nuevo': (-6.6501, -79.7971),
        'Pitipo': (-6.5664, -79.7332),
    },
}

TIPOS_VIA = ['Av.', 'Ca.', 'Jr.', 'Pje.']
NOMBRES_VIAS = ['Balta', 'Bolognesi', 'Grau', 'Salaverry', 'Luis Gonzales', 'Pedro Cieza', 'Arequipa', 'Tacna', 'Sáenz Peña']
URBANIZACIONES = ['Urb. Santa Victoria', 'Urb. Los Parques', 'Urb. La Primavera', 'Urb. San Eduardo']
ASENTAMIENTOS = ['A.H. Primero de Mayo', 'A.H. Cruz del Médano', 'A.H. San Antonio', 'A.H. Diego Ferré']

TECNICOS = [
    'Cuadrilla Chiclayo Centro - C-01',
    'Cuadrilla La Victoria / JLO - C-02',
    'Cuadrilla Pimentel / Costa - C-03',
    'Cuadrilla Lambayeque Norte - C-04',
    'Cuadrilla Ferreñafe - C-05'
]

ASESORES = [
    'Asesor - Carlos Ruiz', 'Asesor - Maria Mendoza', 'Asesor - Jorge Silva',
    'Asesor - Ana Paredes', 'Asesor - Luis Delgado', 'Asesor - Sofia Castro'
]

def generar_direccion():
    if random.random() < 0.60:
        return f"{random.choice(TIPOS_VIA)} {random.choice(NOMBRES_VIAS)} Nro. {random.randint(100, 2400)}"
    else:
        sector = random.choice(URBANIZACIONES) if random.random() < 0.5 else random.choice(ASENTAMIENTOS)
        return f"{sector} Mz. {chr(random.randint(65, 77))} Lte. {random.randint(1, 30)}"

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
PERIOD_END = END_DATE + timedelta(days=1) - timedelta(seconds=1)

sales_dates = [
    START_DATE + timedelta(days=offset)
    for offset in range((END_DATE - START_DATE).days + 1)
]
daily_sales_schedule = [random.randint(8, 20) for _ in sales_dates]
additional_sales = (-sum(daily_sales_schedule)) % 100
for day_index in range(len(daily_sales_schedule) - 1, -1, -1):
    extra = min(20 - daily_sales_schedule[day_index], additional_sales)
    daily_sales_schedule[day_index] += extra
    additional_sales -= extra

total_orders = sum(daily_sales_schedule)
sale_outcomes = (
    ['direct_approved'] * (total_orders * 65 // 100)
    + ['returned'] * (total_orders * 20 // 100)
    + ['direct_rejected'] * (total_orders * 15 // 100)
)
random.shuffle(sale_outcomes)
correction_recovery_outcomes = (
    [True] * (total_orders * 15 // 100)
    + [False] * (total_orders * 5 // 100)
)
random.shuffle(correction_recovery_outcomes)

bo_events = []
almacen_events = []

order_counter = 1
dispatch_counter = 1
correction_counter = 0

print("Procesando simulación histórica de 3 años (2023 - 2025) con soporte ONT y GPS...")

for current_date, daily_sales in zip(sales_dates, daily_sales_schedule):
    for _ in range(daily_sales):
        ord_code = f"BO/{order_counter:05d}"
        client_name = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        client_dni = str(random.randint(10000000, 79999999))
        client_age = random.randint(18, 75)
        client_phone = f"9{random.randint(10000000, 99999999)}"
        
        province = random.choices(['Chiclayo', 'Lambayeque', 'Ferreñafe'], weights=[70, 20, 10])[0]
        district = random.choice(list(PROVINCIAS_GPS[province]))
        address = f"{generar_direccion()}, {district}"
        
        lat_base, lon_base = PROVINCIAS_GPS[province][district]
        lat = round(lat_base + random.uniform(-0.001, 0.001), 7)
        lon = round(lon_base + random.uniform(-0.001, 0.001), 7)
        
        ont_qty = 1 # Estándar de fibra
        deco_qty = random.choices([0, 1, 2, 3], weights=[15, 55, 20, 10])[0]
        repeater_qty = random.choices([0, 1, 2], weights=[40, 45, 15])[0]
        asesor = random.choice(ASESORES)
        
        t_venta = current_date + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
        t_bo_eval = min(t_venta + timedelta(hours=random.randint(1, 4)), PERIOD_END)
        outcome = sale_outcomes[order_counter - 1]
        
        if outcome == 'direct_approved':
            # 65% Aprobado Directo
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Aprobado", "Motivo_Rechazo": "", 
                "Fecha_Programada": min(t_bo_eval + timedelta(days=2), PERIOD_END).strftime("%Y-%m-%d"),
                "Fecha_Real_Instalacion": min(t_bo_eval + timedelta(days=2), PERIOD_END).strftime("%Y-%m-%d"),
                "Estado_Final_Orden": "Instalado"
            })
            
            desp_code = f"DESP/{dispatch_counter:05d}"
            dispatch_counter += 1
            almacen_events.append({
                "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                "Tecnico": random.choice(TECNICOS),
                "Series_ONT": f"ONT-{dispatch_counter:06d}",
                    "Series_Decodificadores": ", ".join([f"DEC-{dispatch_counter:06d}-{index:02d}" for index in range(1, deco_qty + 1)]),
                    "Series_Repetidores": ", ".join([f"REP-{dispatch_counter:06d}-{index:02d}" for index in range(1, repeater_qty + 1)]),
                "Fecha_Despacho": min(t_bo_eval + timedelta(days=1), PERIOD_END).strftime("%Y-%m-%d"),
                "Estado_Almacen": "Entregado a Técnico"
            })
            
        elif outcome == 'returned':
            # 20% Devuelto a Corrección
            motivo = random.choice(['Dirección Incorrecta / Incompleta', 'Teléfono de Contacto Erróneo', 'Mala Oferta / Error en Precios'])
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Devuelto a Corrección", "Motivo_Rechazo": motivo, "Fecha_Programada": "",
                "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "En Proceso"
            })
            
            recuperado = correction_recovery_outcomes[correction_counter]
            correction_counter += 1
            t_corregido = min(t_bo_eval + timedelta(hours=random.randint(2, 24)), PERIOD_END)
            t_bo_eval2 = min(t_corregido + timedelta(hours=random.randint(1, 3)), PERIOD_END)
            
            if recuperado:
                bo_events.append({
                    "Orden": ord_code, "Intento": 2, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                    "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                    "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                    "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                    "Fecha_Registro": t_corregido.strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha_Evaluacion_BO": t_bo_eval2.strftime("%Y-%m-%d %H:%M:%S"),
                    "Estado_BO": "Aprobado (Recuperado)", "Motivo_Rechazo": "",
                    "Fecha_Programada": min(t_bo_eval2 + timedelta(days=2), PERIOD_END).strftime("%Y-%m-%d"),
                    "Fecha_Real_Instalacion": min(t_bo_eval2 + timedelta(days=2), PERIOD_END).strftime("%Y-%m-%d"),
                    "Estado_Final_Orden": "Instalado (Recuperado)"
                })
                
                desp_code = f"DESP/{dispatch_counter:05d}"
                dispatch_counter += 1
                almacen_events.append({
                    "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                    "Tecnico": random.choice(TECNICOS),
                    "Series_ONT": f"ONT-{dispatch_counter:06d}",
                        "Series_Decodificadores": ", ".join([f"DEC-{dispatch_counter:06d}-{index:02d}" for index in range(1, deco_qty + 1)]),
                        "Series_Repetidores": ", ".join([f"REP-{dispatch_counter:06d}-{index:02d}" for index in range(1, repeater_qty + 1)]),
                    "Fecha_Despacho": min(t_bo_eval2 + timedelta(days=1), PERIOD_END).strftime("%Y-%m-%d"),
                    "Estado_Almacen": "Entregado a Técnico"
                })
            else:
                bo_events.append({
                    "Orden": ord_code, "Intento": 2, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                    "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                    "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                    "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                    "Fecha_Registro": t_corregido.strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha_Evaluacion_BO": t_bo_eval2.strftime("%Y-%m-%d %H:%M:%S"),
                    "Estado_BO": "Rechazado Definitivo", "Motivo_Rechazo": "No Subsano Corrección / Cliente Desistió",
                    "Fecha_Programada": "", "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "Cancelado/Rechazado"
                })
        else:
            # 15% Rechazo Directo
            motivo = random.choice(['Falta de Cobertura Técnica', 'Exceso de Equipos Solicitados'])
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Rechazado Definitivo", "Motivo_Rechazo": motivo, "Fecha_Programada": "",
                "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "Rechazado"
            })
            
        order_counter += 1

# Guardar archivos CSV en UTF-8 con BOM (utf-8-sig)
with open("historial_backoffice_eventos_3years.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=bo_events[0].keys())
    writer.writeheader()
    writer.writerows(bo_events)

with open("almacen_despachos_3years.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=almacen_events[0].keys())
    writer.writeheader()
    writer.writerows(almacen_events)

print("¡Dataset actualizado con éxito para analítica!")
print(f" - Registros de Back Office: {len(bo_events)}")
print(f" - Registros de Almacén: {len(almacen_events)}")