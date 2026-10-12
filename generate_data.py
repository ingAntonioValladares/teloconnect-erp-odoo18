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

# Coordenadas base aproximadas para rangos geográficos en Lambayeque
PROVINCIAS_GPS = {
    'Chiclayo': {'lat_base': -6.7714, 'lon_base': -79.8409, 'distritos': ['Chiclayo', 'La Victoria', 'José Leonardo Ortiz', 'Pimentel', 'Monsefú', 'Reque', 'Pomalca']},
    'Lambayeque': {'lat_base': -6.7031, 'lon_base': -79.9042, 'distritos': ['Lambayeque', 'Mochumí', 'Túcume', 'Íllimo', 'Pacora', 'Olmos']},
    'Ferreñafe': {'lat_base': -6.6372, 'lon_base': -79.7878, 'distritos': ['Ferreñafe', 'Pueblo Nuevo', 'Pitipo']}
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
END_DATE = datetime(2026, 8, 1)

bo_events = []
almacen_events = []

order_counter = 1
dispatch_counter = 1
current_date = START_DATE

print("Procesando simulación histórica de 3 años (2023 - 2026) con soporte ONT y GPS...")

while current_date <= END_DATE:
    daily_sales = random.randint(8, 20)
    for _ in range(daily_sales):
        ord_code = f"BO/{order_counter:05d}"
        client_name = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        client_dni = str(random.randint(10000000, 79999999))
        client_age = random.randint(18, 75)
        client_phone = f"9{random.randint(10000000, 99999999)}"
        
        province = random.choices(['Chiclayo', 'Lambayeque', 'Ferreñafe'], weights=[70, 20, 10])[0]
        district = random.choice(PROVINCIAS_GPS[province]['distritos'])
        address = f"{generar_direccion()}, {district}"
        
        # Generar coordenadas GPS con ligera variación realista
        lat = round(PROVINCIAS_GPS[province]['lat_base'] + random.uniform(-0.03, 0.03), 7)
        lon = round(PROVINCIAS_GPS[province]['lon_base'] + random.uniform(-0.03, 0.03), 7)
        
        ont_qty = 1 # Estándar de fibra
        deco_qty = random.choices([0, 1, 2, 3], weights=[15, 55, 20, 10])[0]
        repeater_qty = random.choices([0, 1, 2], weights=[40, 45, 15])[0]
        asesor = random.choice(ASESORES)
        
        t_venta = current_date + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
        t_bo_eval = t_venta + timedelta(hours=random.randint(1, 4))
        
        rand_val = random.random()
        
        if rand_val < 0.65:
            # 65% Aprobado Directo
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Aprobado", "Motivo_Rechazo": "", 
                "Fecha_Programada": (t_bo_eval + timedelta(days=2)).strftime("%Y-%m-%d"),
                "Fecha_Real_Instalacion": (t_bo_eval + timedelta(days=2)).strftime("%Y-%m-%d"),
                "Estado_Final_Orden": "Instalado"
            })
            
            desp_code = f"DESP/{dispatch_counter:05d}"
            dispatch_counter += 1
            almacen_events.append({
                "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                "Tecnico": random.choice(TECNICOS),
                "ONT_Series": f"ONT-{random.randint(100000, 999999)}",
                "Decos_Series": ", ".join([f"DEC-{random.randint(100000, 999999)}" for _ in range(deco_qty)]),
                "Repetidores_Series": ", ".join([f"REP-{random.randint(100000, 999999)}" for _ in range(repeater_qty)]),
                "Fecha_Despacho": (t_bo_eval + timedelta(days=1)).strftime("%Y-%m-%d"),
                "Estado_Almacen": "Entregado a Técnico"
            })
            
        elif rand_val < 0.85:
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
            
            recuperado = random.random() < 0.75 # 75% recupero
            t_corregido = t_bo_eval + timedelta(hours=random.randint(2, 24))
            t_bo_eval2 = t_corregido + timedelta(hours=random.randint(1, 3))
            
            if recuperado:
                bo_events.append({
                    "Orden": ord_code, "Intento": 2, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                    "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                    "Direccion": address, "Latitud": lat, "Longitud": lon, "Asesor": asesor, 
                    "ONTs": ont_qty, "Decos": deco_qty, "Repetidores": repeater_qty,
                    "Fecha_Registro": t_corregido.strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha_Evaluacion_BO": t_bo_eval2.strftime("%Y-%m-%d %H:%M:%S"),
                    "Estado_BO": "Aprobado (Recuperado)", "Motivo_Rechazo": "",
                    "Fecha_Programada": (t_bo_eval2 + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "Fecha_Real_Instalacion": (t_bo_eval2 + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "Estado_Final_Orden": "Instalado (Recuperado)"
                })
                
                desp_code = f"DESP/{dispatch_counter:05d}"
                dispatch_counter += 1
                almacen_events.append({
                    "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                    "Tecnico": random.choice(TECNICOS),
                    "ONT_Series": f"ONT-{random.randint(100000, 999999)}",
                    "Decos_Series": ", ".join([f"DEC-{random.randint(100000, 999999)}" for _ in range(deco_qty)]),
                    "Repetidores_Series": ", ".join([f"REP-{random.randint(100000, 999999)}" for _ in range(repeater_qty)]),
                    "Fecha_Despacho": (t_bo_eval2 + timedelta(days=1)).strftime("%Y-%m-%d"),
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
    current_date += timedelta(days=1)

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