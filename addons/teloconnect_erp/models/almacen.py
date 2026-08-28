# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TeloConnectInventoryDispatch(models.Model):
    _name = 'teloconnect.almacen'
    _description = 'Gestion de Almacen'
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
        comodel_name='teloconnect.backoffice',
        string='Orden de Back Office',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    client_name = fields.Char(
        related='backoffice_id.client_name',
        string='Cliente',
        store=True,
        readonly=True
    )
    installation_address = fields.Text(
        related='backoffice_id.installation_address',
        string='Dirección de Instalación',
        readonly=True
    )

    required_decos = fields.Integer(
        related='backoffice_id.deco_qty',
        string='Decos Requeridos',
        readonly=True
    )
    required_repeaters = fields.Integer(
        related='backoffice_id.repeater_qty',
        string='Repetidores Requeridos',
        readonly=True
    )

    deco_series = fields.Text(
        string='Series / MAC Address Decodificadores',
        help='Ingrese cada número de serie o MAC separado por comas o saltos de línea.',
        tracking=True
    )
    repeater_series = fields.Text(
        string='Series / MAC Address Repetidores Wi-Fi',
        help='Ingrese cada número de serie o MAC separado por comas o saltos de línea.',
        tracking=True
    )

    technician_id = fields.Many2one(
        comodel_name='res.users',
        string='Técnico / Cuadrilla Asignada',
        tracking=True
    )
    technician_notes = fields.Text(
        string='Observaciones de Despacho'
    )

    state = fields.Selection(
        selection=[
            ('pendiente_asig', 'Pendiente Asignación'),
            ('equipos_asignados', 'Equipos Asignados'),
            ('despachado', 'Despachado'),
            ('entregado_tecnico', 'Entregado a Técnico'),
        ],
        string='Estado Almacén',
        default='pendiente_asig',
        required=True,
        index=True,
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.inventory.dispatch') or _('Nuevo')
        return super(TeloConnectInventoryDispatch, self).create(vals_list)

    def action_assign_equipment(self):
        for rec in self:
            if rec.required_decos > 0:
                if not rec.deco_series:
                    raise ValidationError(_('Debe registrar las series / MAC Address de los Decodificadores.'))
                series_list = [s.strip() for s in rec.deco_series.replace('\n', ',').split(',') if s.strip()]
                if len(series_list) != rec.required_decos:
                    raise ValidationError(_(
                        'Se requieren %(req)d serie(s) de Decodificador(es), pero se ingresaron %(count)d.',
                        req=rec.required_decos,
                        count=len(series_list)
                    ))

            if rec.required_repeaters > 0:
                if not rec.repeater_series:
                    raise ValidationError(_('Debe registrar las series / MAC Address de los Repetidores Wi-Fi.'))
                series_rep_list = [s.strip() for s in rec.repeater_series.replace('\n', ',').split(',') if s.strip()]
                if len(series_rep_list) != rec.required_repeaters:
                    raise ValidationError(_(
                        'Se requieren %(req)d serie(s) de Repetidor(es), pero se ingresaron %(count)d.',
                        req=rec.required_repeaters,
                        count=len(series_rep_list)
                    ))

            rec.write({'state': 'equipos_asignados'})

    def action_dispatch(self):
        for rec in self:
            if rec.state != 'equipos_asignados':
                raise ValidationError(_('Primero debe asignar los equipos antes de despachar.'))
            if not rec.technician_id:
                raise ValidationError(_('Debe asignar un técnico o cuadrilla para realizar el despacho.'))
            rec.write({'state': 'despachado'})

    def action_mark_delivered(self):
        for rec in self:
            if rec.state != 'despachado':
                raise ValidationError(_('La orden debe estar en estado Despachado.'))
            rec.write({'state': 'entregado_tecnico'})