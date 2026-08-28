import csv
import random
from datetime import datetime, timedelta

# Fijar semilla para reproducibilidad opcional
random.seed(42)

# Listas base de nombres y apellidos
NOMBRES = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Lucia", "Pedro", "Elena", "Diego", "Sofia", 
           "Manuel", "Carmen", "Rosa", "Jose", "Javier", "Patricia", "Fiorella", "Christian", "Katia", "Fernando"]
APELLIDOS = ["Gomez", "Perez", "Rodriguez", "Lopez", "Garcia", "Martinez", "Sanchez", "Torres", 
             "Flores", "Diaz", "Vargas", "Rojas", "Vasquez", "Castro", "Romero", "Mendoza"]

# Distribución geográfica en Lambayeque
UBICACIONES = {
    'Chiclayo': ['Chiclayo', 'La Victoria', 'José Leonardo Ortiz', 'Pimentel', 'Monsefú', 'Reque', 'Santa Rosa', 'Eten', 'Puerto Eten', 'Pomalca', 'Pátapo'],
    'Lambayeque': ['Lambayeque', 'Mochumí', 'Túcume', 'Íllimo', 'Pacora', 'Jayanca', 'Olmos', 'Motupe'],
    'Ferreñafe': ['Ferreñafe', 'Pueblo Nuevo', 'Manuel Antonio Mesones Muro', 'Pitipo']
}

TIPOS_VIA = ['Av.', 'Ca.', 'Jr.', 'Pje.']
NOMBRES_VIAS = ['Balta', 'Bolognesi', 'Grau', 'Salaverry', 'Luis Gonzales', 'Pedro Cieza', 'Arequipa', 'Tacna', 'Sáenz Peña', 'Chinchaysuyo', 'Unión', 'Los Incas', 'Sican', 'Huamachuco']
URBANIZACIONES = ['Urb. Santa Victoria', 'Urb. Patios del Norte', 'Urb. Los Parques', 'Urb. La Primavera', 'Urb. San Eduardo', 'Urb. San Juan', 'Urb. Federico Villarreal', 'Urb. Las Brisas']
ASENTAMIENTOS = ['A.H. Primero de Mayo', 'A.H. Cruz del Médano', 'A.H. UPIS Belén', 'A.H. San Antonio', 'A.H. Diego Ferré', 'A.H. Nuevo San Lorenzo', 'A.H. Urrunaga']

TECNICOS = [
    'Cuadrilla Chiclayo Centro - C-01',
    'Cuadrilla La Victoria / JLO - C-02',
    'Cuadrilla Pimentel / Costa - C-03',
    'Cuadrilla Lambayeque Norte - C-04',
    'Cuadrilla Ferreñafe - C-05'
]

ASESORES = [
    'Asesor - Carlos Ruiz',
    'Asesor - Maria Mendoza',
    'Asesor - Jorge Silva',
    'Asesor - Ana Paredes',
    'Asesor - Luis Delgado',
    'Asesor - Sofia Castro'
]

def generar_direccion():
    if random.random() < 0.60:
        return f"{random.choice(TIPOS_VIA)} {random.choice(NOMBRES_VIAS)} Nro. {random.randint(100, 2400)}"
    else:
        sector = random.choice(URBANIZACIONES) if random.random() < 0.5 else random.choice(ASENTAMIENTOS)
        mz = chr(random.randint(65, 77))
        lt = random.randint(1, 30)
        return f"{sector} Mz. {mz} Lte. {lt}"

# Periodo de 3 años de simulación
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2026, 8, 1)

bo_events = []
almacen_events = []

order_counter = 1
dispatch_counter = 1
current_date = START_DATE

print("Procesando simulación histórica de 3 años (2023 - 2026)...")

while current_date <= END_DATE:
    daily_sales = random.randint(8, 20)
    for _ in range(daily_sales):
        ord_code = f"ORD-{order_counter:06d}"
        client_name = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        client_dni = str(random.randint(10000000, 79999999))
        client_age = random.randint(18, 75)
        client_phone = f"9{random.randint(10000000, 99999999)}"
        
        province = random.choices(['Chiclayo', 'Lambayeque', 'Ferreñafe'], weights=[70, 20, 10])[0]
        district = random.choice(UBICACIONES[province])
        address = f"{generar_direccion()}, {district}"
        
        deco_qty = random.choices([0, 1, 2, 3], weights=[15, 55, 20, 10])[0]
        repeater_qty = random.choices([0, 1, 2], weights=[40, 45, 15])[0]
        asesor = random.choice(ASESORES)
        
        # Fecha de creación por Asesor
        t_venta = current_date + timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
        
        # Evaluación inicial de Back Office
        t_bo_eval = t_venta + timedelta(hours=random.randint(1, 4))
        
        # Ciclo de vida probabilístico
        rand_val = random.random()
        
        if rand_val < 0.65:
            # Venta Limpia Directa (65%)
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Asesor": asesor, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Aprobado", "Motivo_Rechazo": "", 
                "Fecha_Programada": (t_bo_eval + timedelta(days=2)).strftime("%Y-%m-%d"),
                "Fecha_Real_Instalacion": (t_bo_eval + timedelta(days=2)).strftime("%Y-%m-%d"),
                "Estado_Final_Orden": "Instalado"
            })
            
            # Almacén
            desp_code = f"DESP-{dispatch_counter:06d}"
            dispatch_counter += 1
            almacen_events.append({
                "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                "Tecnico": random.choice(TECNICOS),
                "Decos_Series": ", ".join([f"DEC-{random.randint(100000, 999999)}" for _ in range(deco_qty)]),
                "Repetidores_Series": ", ".join([f"REP-{random.randint(100000, 999999)}" for _ in range(repeater_qty)]),
                "Fecha_Despacho": (t_bo_eval + timedelta(days=1)).strftime("%Y-%m-%d"),
                "Estado_Almacen": "Entregado a Tecnico"
            })
            
        elif rand_val < 0.85:
            # Flujo con Corrección / Devolución a Asesor (20%)
            motivo = random.choice(['Dirección Incorrecta / Incompleta', 'Teléfono de Contacto Erróneo', 'Mala Oferta / Error en Precios'])
            
            # Evento 1: BO Devuelve a Corrección
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Asesor": asesor, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Devuelto a Correccion", "Motivo_Rechazo": motivo, "Fecha_Programada": "",
                "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "En Proceso"
            })
            
            # Evento 2: Asesor Subrana / Corrige
            recuperado = random.random() < 0.75 # 75% se logra recuperar
            t_corregido = t_bo_eval + timedelta(hours=random.randint(2, 24))
            t_bo_eval2 = t_corregido + timedelta(hours=random.randint(1, 3))
            
            if recuperado:
                bo_events.append({
                    "Orden": ord_code, "Intento": 2, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                    "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                    "Direccion": address, "Asesor": asesor, "Decos": deco_qty, "Repetidores": repeater_qty,
                    "Fecha_Registro": t_corregido.strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha_Evaluacion_BO": t_bo_eval2.strftime("%Y-%m-%d %H:%M:%S"),
                    "Estado_BO": "Aprobado (Recuperado)", "Motivo_Rechazo": "",
                    "Fecha_Programada": (t_bo_eval2 + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "Fecha_Real_Instalacion": (t_bo_eval2 + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "Estado_Final_Orden": "Instalado (Recuperado)"
                })
                
                desp_code = f"DESP-{dispatch_counter:06d}"
                dispatch_counter += 1
                almacen_events.append({
                    "Despacho": desp_code, "Orden": ord_code, "Cliente": client_name, "Distrito": district,
                    "Tecnico": random.choice(TECNICOS),
                    "Decos_Series": ", ".join([f"DEC-{random.randint(100000, 999999)}" for _ in range(deco_qty)]),
                    "Repetidores_Series": ", ".join([f"REP-{random.randint(100000, 999999)}" for _ in range(repeater_qty)]),
                    "Fecha_Despacho": (t_bo_eval2 + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "Estado_Almacen": "Entregado a Tecnico"
                })
            else:
                bo_events.append({
                    "Orden": ord_code, "Intento": 2, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                    "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                    "Direccion": address, "Asesor": asesor, "Decos": deco_qty, "Repetidores": repeater_qty,
                    "Fecha_Registro": t_corregido.strftime("%Y-%m-%d %H:%M:%S"),
                    "Fecha_Evaluacion_BO": t_bo_eval2.strftime("%Y-%m-%d %H:%M:%S"),
                    "Estado_BO": "Rechazado Definitivo", "Motivo_Rechazo": "No Subsano Correccion / Cliente Desistio",
                    "Fecha_Programada": "", "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "Cancelado/Rechazado"
                })
                
        else:
            # Rechazo Definitivo Directo (15%)
            motivo = random.choice(['Falta de Cobertura Técnica', 'Exceso de Equipos Solicitados'])
            bo_events.append({
                "Orden": ord_code, "Intento": 1, "Cliente": client_name, "DNI": client_dni, "Edad": client_age,
                "Telefono": client_phone, "Departamento": "Lambayeque", "Provincia": province, "Distrito": district,
                "Direccion": address, "Asesor": asesor, "Decos": deco_qty, "Repetidores": repeater_qty,
                "Fecha_Registro": t_venta.strftime("%Y-%m-%d %H:%M:%S"),
                "Fecha_Evaluacion_BO": t_bo_eval.strftime("%Y-%m-%d %H:%M:%S"),
                "Estado_BO": "Rechazado Definitivo", "Motivo_Rechazo": motivo, "Fecha_Programada": "",
                "Fecha_Real_Instalacion": "", "Estado_Final_Orden": "Rechazado"
            })
            
        order_counter += 1
    current_date += timedelta(days=1)

# Guardar los archivos CSV
with open("historial_backoffice_eventos_3years.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=bo_events[0].keys())
    writer.writeheader()
    writer.writerows(bo_events)

with open("almacen_despachos_3years.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=almacen_events[0].keys())
    writer.writeheader()
    writer.writerows(almacen_events)

print("¡Dataset generado exitosamente en archivos CSV!")
print(f" - Registros de BackOffice: {len(bo_events)}")
print(f" - Registros de Almacén: {len(almacen_events)}")