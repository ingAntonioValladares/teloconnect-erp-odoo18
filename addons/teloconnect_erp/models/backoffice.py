# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TeloConnectBackoffice(models.Model):
    _name = 'teloconnect.backoffice'
    _description = 'Orden de Back Office'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Número de Orden', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: 'Nuevo'
    )
    client_name = fields.Char(string='Nombre del Cliente', required=True)
    installation_address = fields.Char(string='Dirección Completa', required=True)  # <-- Char
    district = fields.Char(string='Distrito', required=True)
    deco_qty = fields.Integer(string='Cantidad de Decos', default=2)
    repeater_qty = fields.Integer(string='Cantidad de Repetidores', default=0)
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validation', 'En Validación'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Estado', default='draft', tracking=True)

    rejection_reason = fields.Selection([
        ('bad_offer', 'Mala oferta'),
        ('excess_decos', 'Exceso de decos'),
        ('no_coverage', 'Incobertura'),
        ('bad_data', 'Datos erróneos')
    ], string='Motivo de Rechazo', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.backoffice') or 'Nuevo'
        return super().create(vals_list)

    def action_validate(self):
        for rec in self:
            rec.state = 'validation'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            if not rec.rejection_reason:
                raise ValidationError("Debe seleccionar obligatoriamente un motivo de rechazo antes de rechazar la orden.")
            rec.state = 'rejected'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'