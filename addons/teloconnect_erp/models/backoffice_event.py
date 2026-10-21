# -*- coding: utf-8 -*-
from odoo import fields, models


class TeloConnectBackOfficeEvent(models.Model):
    _name = 'teloconnect.backoffice.event'
    _description = 'Historial Analítico de Back Office'
    _order = 'event_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Evento', required=True, readonly=True, index=True)
    backoffice_id = fields.Many2one(
        'teloconnect.backoffice', string='Orden', readonly=True, index=True,
        ondelete='set null'
    )
    order_name = fields.Char(string='Código de Orden', readonly=True, index=True)
    event_type = fields.Selection([
        ('created', 'Orden Creada'),
        ('data_update', 'Datos Actualizados'),
        ('commercial_state', 'Cambio de Estado Comercial'),
        ('warehouse_created', 'Despacho Creado'),
        ('warehouse_update', 'Datos de Almacén Actualizados'),
        ('warehouse_state', 'Cambio de Estado Logístico'),
        ('baseline', 'Estado Existente al Activar Historial'),
    ], string='Tipo de Evento', required=True, readonly=True, index=True)
    event_date = fields.Datetime(string='Fecha del Evento', required=True, readonly=True, index=True)
    user_name = fields.Char(string='Usuario', readonly=True)
    changed_fields = fields.Char(string='Campos Modificados', readonly=True)
    commercial_state = fields.Selection([
        ('draft', 'Borrador'),
        ('validation', 'En Validación BO'),
        ('en_correcion', 'Devuelto para Corrección'),
        ('approved', 'Aprobado / Pendiente Instalación'),
        ('rescheduled', 'Visita Reprogramada'),
        ('not_installed', 'Instalación No Realizada'),
        ('installed', 'Instalado Exitosamente'),
        ('rejected', 'Rechazado por BO'),
    ], string='Estado Comercial', readonly=True, index=True)
    rejection_reason = fields.Selection([
        ('mala_oferta', 'Mala Oferta / Error en Precios'),
        ('sin_cobertura', 'Falta de Cobertura Técnica'),
        ('exceso_equipos', 'Exceso de Equipos Solicitados'),
        ('direccion_erronea', 'Dirección Incorrecta / Incompleta'),
        ('contacto_invalido', 'Teléfono de Contacto Erróneo'),
    ], string='Motivo de Rechazo', readonly=True)
    installation_result = fields.Selection([
        ('installed', 'Instalación realizada'),
        ('not_installed', 'Instalación no realizada'),
        ('rescheduled', 'Visita reprogramada'),
    ], string='Resultado de Instalación', readonly=True)
    installation_category = fields.Char(
        string='Categoría del Resultado', readonly=True
    )
    installation_note = fields.Text(
        string='Observación de Back Office', readonly=True
    )
    rescheduled_install_date = fields.Date(
        string='Fecha Reprogramada', readonly=True
    )
    actual_install_date = fields.Date(
        string='Fecha Real de Instalación', readonly=True
    )
    warehouse_state = fields.Selection([
        ('pendiente_asig', 'Pendiente Asignación'),
        ('equipos_asignados', 'Equipos Asignados'),
        ('despachado', 'Despachado'),
        ('entregado_tecnico', 'Entregado a Técnico'),
    ], string='Estado Logístico', readonly=True, index=True)
    dispatch_name = fields.Char(string='Código de Despacho', readonly=True)
    technician_id = fields.Char(string='Técnico / Cuadrilla', readonly=True)
    dispatch_date = fields.Date(string='Fecha de Despacho', readonly=True)
    client_name = fields.Char(string='Cliente', readonly=True, index=True)
    client_dni = fields.Char(string='DNI', readonly=True)
    client_age = fields.Integer(string='Edad', readonly=True)
    client_phone = fields.Char(string='Teléfono', readonly=True)
    department = fields.Char(string='Departamento', readonly=True)
    province = fields.Char(string='Provincia', readonly=True, index=True)
    district = fields.Char(string='Distrito', readonly=True, index=True)
    installation_address = fields.Text(string='Dirección de Instalación', readonly=True)
    latitude = fields.Float(string='Latitud', digits=(10, 7), readonly=True)
    longitude = fields.Float(string='Longitud', digits=(10, 7), readonly=True)
    ont_qty = fields.Integer(string='ONT Requeridos', readonly=True)
    deco_qty = fields.Integer(string='Decodificadores Requeridos', readonly=True)
    repeater_qty = fields.Integer(string='Repetidores Requeridos', readonly=True)
    ont_series = fields.Text(string='Series ONT', readonly=True)
    deco_series = fields.Text(string='Series Decodificadores', readonly=True)
    repeater_series = fields.Text(string='Series Repetidores', readonly=True)
