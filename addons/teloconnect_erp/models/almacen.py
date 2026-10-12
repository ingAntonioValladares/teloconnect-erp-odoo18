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
    
    backoffice_id = fields.Many2one(
        'teloconnect.backoffice', 
        string='Orden de Back Office', 
        required=True, 
        ondelete='cascade',
        tracking=True
    )
    
    # Campos espejo
    client_name = fields.Char(related='backoffice_id.client_name', string='Cliente', readonly=True)
    district = fields.Char(related='backoffice_id.district', string='Distrito', readonly=True)
    installation_address = fields.Char(related='backoffice_id.installation_address', string='Dirección', readonly=True)
    deco_qty_required = fields.Integer(related='backoffice_id.deco_qty', string='Decos Requeridos', readonly=True)
    repeater_qty_required = fields.Integer(related='backoffice_id.repeater_qty', string='Repetidores Requeridos', readonly=True)
    
    # Asignación Logística (Como Texto para evitar conflictos de llaves foráneas)
    technician_id = fields.Char(string='Técnico / Cuadrilla Asignada', tracking=True)
    dispatch_date = fields.Date(string='Fecha de Despacho', default=fields.Date.context_today)
    
    deco_series = fields.Text(string='Series / MAC Address Decodificadores')
    repeater_series = fields.Text(string='Series / MAC Address Repetidores Wi-Fi')
    
    state = fields.Selection([
        ('pendiente_asig', 'Pendiente Asignación'),
        ('equipos_asignados', 'Equipos Asignados'),
        ('despachado', 'Despachado'),
        ('entregado_tecnico', 'Entregado a Técnico')
    ], string='Estado Logístico', default='pendiente_asig', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.almacen') or 'Nuevo'
        return super().create(vals_list)

    def action_assign_equipment(self):
        for record in self:
            decos_list = [s.strip() for s in (record.deco_series or '').replace('\n', ',').split(',') if s.strip()]
            repeaters_list = [s.strip() for s in (record.repeater_series or '').replace('\n', ',').split(',') if s.strip()]

            if len(decos_list) != record.deco_qty_required:
                raise ValidationError(
                    _("Error de Cantidad: Se requieren %d series de Decodificadores y se han ingresado %d.") % 
                    (record.deco_qty_required, len(decos_list))
                )

            if len(repeaters_list) != record.repeater_qty_required:
                raise ValidationError(
                    _("Error de Cantidad: Se requieren %d series de Repetidores y se han ingresado %d.") % 
                    (record.repeater_qty_required, len(repeaters_list))
                )

            if not record.technician_id:
                raise ValidationError(_("Debe asignar un Técnico o Cuadrilla antes de procesar el despacho."))

            record.state = 'entregado_tecnico'