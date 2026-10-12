# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TeloConnectAlmacen(models.Model):
    _name = 'teloconnect.almacen'
    _description = 'Despacho de Almacén y Logística'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Código de Despacho', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('Nuevo')
    )
    
    # Enlace directo con la Orden Comercial
    backoffice_id = fields.Many2one(
        'teloconnect.backoffice', 
        string='Orden de Back Office', 
        required=True, 
        ondelete='cascade',
        tracking=True
    )
    
    # Campos espejo (relacionados) para trazabilidad directa
    client_name = fields.Char(related='backoffice_id.client_name', string='Cliente', readonly=True)
    district = fields.Char(related='backoffice_id.district', string='Distrito', readonly=True)
    installation_address = fields.Text(related='backoffice_id.installation_address', string='Dirección', readonly=True)
    
    ont_qty_required = fields.Integer(related='backoffice_id.ont_qty', string='ONTs Requeridos', readonly=True)
    deco_qty_required = fields.Integer(related='backoffice_id.deco_qty', string='Decos Requeridos', readonly=True)
    repeater_qty_required = fields.Integer(related='backoffice_id.repeater_qty', string='Repetidores Requeridos', readonly=True)
    
    # Asignación de Recursos Logísticos
    technician_id = fields.Char(string='Técnico / Cuadrilla Asignada', required=True, tracking=True)
    dispatch_date = fields.Date(string='Fecha de Despacho', default=fields.Date.context_today)
    
    # Control de Inventario Físico (Series / MAC Address)
    ont_series = fields.Text(string='Series / MAC Address Routers ONT', help='Ingrese las series separadas por comas.')
    deco_series = fields.Text(string='Series / MAC Address Decodificadores', help='Ingrese las series separadas por comas.')
    repeater_series = fields.Text(string='Series / MAC Address Repetidores Wi-Fi', help='Ingrese las series separadas por comas.')
    
    # Estado del Despacho
    state = fields.Selection([
        ('pendiente_asig', 'Pendiente Asignación'),
        ('equipos_asignados', 'Equipos Asignados'),
        ('despachado', 'Despachado'),
        ('entregado_tecnico', 'Entregado a Técnico')
    ], string='Estado Logístico', default='pendiente_asig', tracking=True)
  
    def action_assign_equipment(self):
        for record in self:
            onts_list = [s.strip() for s in (record.ont_series or '').replace('\n', ',').split(',') if s.strip()]
            decos_list = [s.strip() for s in (record.deco_series or '').replace('\n', ',').split(',') if s.strip()]
            repeaters_list = [s.strip() for s in (record.repeater_series or '').replace('\n', ',').split(',') if s.strip()]
  
            if len(onts_list) != record.ont_qty_required:
                raise ValidationError(
                    _("Error de Cantidad: Se requieren %d Routers ONT y se han ingresado %d.") % 
                    (record.ont_qty_required, len(onts_list))
                )

            if len(decos_list) != record.deco_qty_required:
                raise ValidationError(
                    _("Error de Cantidad: Se requieren %d Decodificadores y se han ingresado %d.") % 
                    (record.deco_qty_required, len(decos_list))
                )
  
            if len(repeaters_list) != record.repeater_qty_required:
                raise ValidationError(
                    _("Error de Cantidad: Se requieren %d Repetidores y se han ingresado %d.") % 
                    (record.repeater_qty_required, len(repeaters_list))
                )
  
            if not record.technician_id:
                raise ValidationError(_("Debe asignar un Técnico o Cuadrilla antes de procesar el despacho."))
  
            record.state = 'entregado_tecnico'