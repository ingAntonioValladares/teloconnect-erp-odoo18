# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TeloConnectBackOffice(models.Model):
    _name = 'teloconnect.backoffice'
    _description = 'Orden de Back Office'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Orden de Back Office', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('Nuevo')
    )
    
    # --- Datos del Cliente ---
    client_name = fields.Char(string='Nombre del Cliente', required=True, tracking=True)
    client_dni = fields.Char(string='DNI', size=8, tracking=True)
    client_age = fields.Integer(string='Edad')
    client_phone = fields.Char(string='Teléfono de Contacto', tracking=True)
    
    # --- Ubicación Geográfica (Región Lambayeque) ---
    department = fields.Char(string='Departamento', default='Lambayeque', readonly=True)
    province = fields.Selection([
        ('chiclayo', 'Chiclayo'),
        ('lambayeque', 'Lambayeque'),
        ('ferrenafe', 'Ferreñafe')
    ], string='Provincia', required=True, default='chiclayo', tracking=True)
    district = fields.Char(string='Distrito', required=True, tracking=True)
    installation_address = fields.Text(string='Dirección Completa (Vía/Mz/Lte/Urb/A.H.)', required=True)
    
    # Coordenadas GPS para validación geográfica
    latitude = fields.Float(string='Latitud', digits=(10, 7), tracking=True)
    longitude = fields.Float(string='Longitud', digits=(10, 7), tracking=True)

    # --- Datos Comerciales ---
    advisor_id = fields.Char(string='Asesor Comercial', tracking=True)
    
    # --- Requerimientos de Equipos (Triple Play) ---
    ont_qty = fields.Integer(string='Cantidad de Routers ONT', default=1, tracking=True)
    deco_qty = fields.Integer(string='Cantidad de Decos', default=0, tracking=True)
    repeater_qty = fields.Integer(string='Cantidad de Repetidores', default=0, tracking=True)
    
    # --- Fechas de Control y Trazabilidad ---
    sale_date = fields.Datetime(string='Fecha de Venta', default=fields.Datetime.now, required=True)
    scheduled_install_date = fields.Date(string='Fecha Programada Instalación')
    actual_install_date = fields.Date(string='Fecha Real Instalación')
    
    # --- Estados Comerciales y Validación (Alineados con vistas XML) ---
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validation', 'En Validación BO'),
        ('en_correcion', 'Devuelto para Corrección'),
        ('approved', 'Aprobado / Pendiente Instalación'),
        ('installed', 'Instalado Exitosamente'),
        ('rejected', 'Rechazado por BO')
    ], string='Estado Comercial', default='draft', required=True, tracking=True)

    rejection_reason = fields.Selection([
        ('mala_oferta', 'Mala Oferta / Error en Precios'),
        ('sin_cobertura', 'Falta de Cobertura Técnica'),
        ('exceso_equipos', 'Exceso de Equipos Solicitados'),
        ('direccion_erronea', 'Dirección Incorrecta / Incompleta'),
        ('contacto_invalido', 'Teléfono de Contacto Erróneo')
    ], string='Motivo de Rechazo', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') or vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.backoffice') or 'BO/00001'
        return super(TeloConnectBackOffice, self).create(vals_list)

    @api.constrains('client_dni')
    def _check_client_dni(self):
        for rec in self:
            if rec.client_dni and (not rec.client_dni.isdigit() or len(rec.client_dni) != 8):
                raise ValidationError("El DNI del cliente debe contener exactamente 8 dígitos numéricos.")

    def action_validate(self):
        for rec in self:
            rec.state = 'validation'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            self.env['teloconnect.almacen'].create({
                'backoffice_id': rec.id,
                'technician_id': 'Cuadrilla por Asignar',
            })

    def action_return_correction(self):
        for rec in self:
            rec.state = 'en_correcion'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'