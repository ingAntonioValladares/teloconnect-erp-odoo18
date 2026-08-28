# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TeloConnectBackOffice(models.Model):
    _name = 'teloconnect.backoffice'
    _description = 'Orden de Back Office'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Orden de Back Office', required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    
    # Datos del Cliente
    client_name = fields.Char(string='Nombre del Cliente', required=True, tracking=True)
    client_dni = fields.Char(string='DNI', size=8, tracking=True)
    client_age = fields.Integer(string='Edad')
    client_phone = fields.Char(string='Teléfono de Contacto', tracking=True)
    
    # Ubicación Geográfica (Lambayeque)
    department = fields.Char(string='Departamento', default='Lambayeque', readonly=True)
    province = fields.Selection([
        ('chiclayo', 'Chiclayo'),
        ('lambayeque', 'Lambayeque'),
        ('ferrenafe', 'Ferreñafe')
    ], string='Provincia', required=True, default='chiclayo', tracking=True)
    district = fields.Char(string='Distrito', required=True, tracking=True)
    installation_address = fields.Text(string='Dirección Completa', required=True)
    
    # Datos Comerciales
    advisor_id = fields.Char(string='Asesor Comercial', tracking=True)
    
    # Requerimientos de Equipos
    deco_qty = fields.Integer(string='Cantidad de Decos', default=0, tracking=True)
    repeater_qty = fields.Integer(string='Cantidad de Repetidores', default=0, tracking=True)
    
    # Fechas de Control y Trazabilidad
    sale_date = fields.Datetime(string='Fecha de Venta', default=fields.Datetime.now, required=True)
    scheduled_install_date = fields.Date(string='Fecha Programada Instalación')
    actual_install_date = fields.Date(string='Fecha Real Instalación')
    
    # Estados y Motivos de Rechazo / Corrección
    status = fields.Selection([
        ('en_validacion', 'En Validación BO'),
        ('en_correcion', 'Devuelto para Corrección'),
        ('aprobado', 'Aprobado / Pendiente Instalación'),
        ('instalado', 'Instalado Exitosamente'),
        ('reprogramado', 'Reprogramado'),
        ('rechazado', 'Rechazado por BO'),
        ('cancelado', 'Cancelado por Cliente')
    ], string='Estado Comercial', default='en_validacion', required=True, tracking=True)

    rejection_reason = fields.Selection([
        ('mala_oferta', 'Mala Oferta / Error en Precios'),
        ('sin_cobertura', 'Falta de Cobertura Técnica'),
        ('exceso_equipos', 'Exceso de Equipos Solicitados'),
        ('direccion_erronea', 'Dirección Incorrecta / Incompleta'),
        ('contacto_invalido', 'Teléfono de Contacto Erróneo')
    ], string='Motivo de Rechazo', tracking=True)