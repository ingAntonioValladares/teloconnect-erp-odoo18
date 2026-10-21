# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TeloConnectBackOffice(models.Model):
    _name = 'teloconnect.backoffice'
    _description = 'Órdenes de Back Office'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

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
    installation_result = fields.Selection([
        ('installed', 'Instalación realizada'),
        ('not_installed', 'Instalación no realizada'),
        ('rescheduled', 'Visita reprogramada'),
    ], string='Resultado de Instalación', tracking=True)
    installation_category_id = fields.Many2one(
        'teloconnect.installation.outcome.category',
        string='Categoría del Resultado',
        tracking=True,
        ondelete='restrict',
    )
    installation_note = fields.Text(
        string='Observación de Back Office', tracking=True
    )
    rescheduled_install_date = fields.Date(
        string='Fecha Reprogramada por el Técnico',
        tracking=True,
        help='Ingrese la fecha informada por el técnico; no hay sincronización automática con el sistema externo.',
    )
    
    # --- Estados Comerciales y Validación ---
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validation', 'En Validación BO'),
        ('en_correcion', 'Devuelto para Corrección'),
        ('approved', 'Aprobado / Pendiente Instalación'),
        ('rescheduled', 'Visita Reprogramada'),
        ('not_installed', 'Instalación No Realizada'),
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
    dispatch_ids = fields.One2many(
        'teloconnect.almacen', 'backoffice_id', string='Despachos de Almacén'
    )
    history_event_ids = fields.One2many(
        'teloconnect.backoffice.event', 'backoffice_id', string='Historial de la Orden'
    )
    warehouse_delivered = fields.Boolean(compute='_compute_warehouse_delivered')

    _history_tracked_fields = {
        'client_name', 'client_dni', 'client_age', 'client_phone', 'department',
        'province', 'district', 'installation_address', 'latitude', 'longitude',
        'ont_qty', 'deco_qty', 'repeater_qty', 'rejection_reason',
        'actual_install_date',
        'installation_result', 'installation_category_id', 'installation_note',
        'rescheduled_install_date',
    }

    @api.depends('dispatch_ids.state')
    def _compute_warehouse_delivered(self):
        for rec in self:
            rec.warehouse_delivered = any(
                dispatch.state == 'entregado_tecnico' for dispatch in rec.dispatch_ids
            )

    def _log_history_event(self, event_type, changed_fields=None, user_name=None):
        self.ensure_one()
        event_model = self.env['teloconnect.backoffice.event'].sudo()
        dispatch = self.dispatch_ids.sorted('id')[:1]
        event_label = dict(event_model._fields['event_type'].selection).get(
            event_type, event_type
        )
        sequence = event_model.search_count([('backoffice_id', '=', self.id)]) + 1
        labels = [
            self._fields[field_name].string if field_name in self._fields else field_name
            for field_name in (changed_fields or [])
        ]
        event_model.create({
            'name': '%s - %03d - %s' % (self.name, sequence, event_label),
            'backoffice_id': self.id,
            'order_name': self.name,
            'event_type': event_type,
            'event_date': fields.Datetime.now(),
            'user_name': user_name or self.env.user.display_name,
            'commercial_state': self.state,
            'warehouse_state': dispatch.state if dispatch else False,
            'dispatch_name': dispatch.name if dispatch else False,
            'technician_id': dispatch.technician_id if dispatch else False,
            'dispatch_date': dispatch.dispatch_date if dispatch else False,
            'rejection_reason': self.rejection_reason,
            'actual_install_date': self.actual_install_date,
            'installation_result': self.installation_result,
            'installation_category': self.installation_category_id.name,
            'installation_note': self.installation_note,
            'rescheduled_install_date': self.rescheduled_install_date,
            'changed_fields': ', '.join(labels),
            'client_name': self.client_name,
            'client_dni': self.client_dni,
            'client_age': self.client_age,
            'client_phone': self.client_phone,
            'department': self.department,
            'province': self.province,
            'district': self.district,
            'installation_address': self.installation_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'ont_qty': self.ont_qty,
            'deco_qty': self.deco_qty,
            'repeater_qty': self.repeater_qty,
            'ont_series': dispatch.ont_series if dispatch else False,
            'deco_series': dispatch.deco_series if dispatch else False,
            'repeater_series': dispatch.repeater_series if dispatch else False,
        })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('client_dni'):
                raise ValidationError("El DNI del cliente es obligatorio.")
            if vals.get('name', _('New')) == _('New') or vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.backoffice') or 'BO/00001'
        records = super(TeloConnectBackOffice, self).create(vals_list)
        for record, vals in zip(records, vals_list):
            record._log_history_event('created', vals.keys())
        return records

    def write(self, vals):
        if 'client_dni' in vals and not vals['client_dni']:
            raise ValidationError("El DNI del cliente es obligatorio.")
        watched_fields = self._history_tracked_fields.intersection(vals)
        previous = {
            record.id: {
                field_name: record[field_name] for field_name in watched_fields
            }
            for record in self
        }
        previous_states = {record.id: record.state for record in self}
        result = super(TeloConnectBackOffice, self).write(vals)
        for record in self:
            changed_fields = [
                field_name for field_name, old_value in previous[record.id].items()
                if old_value != record[field_name]
            ]
            if previous_states[record.id] != record.state:
                record._log_history_event(
                    'commercial_state', ['state'] + changed_fields
                )
            elif changed_fields:
                record._log_history_event('data_update', changed_fields)
        return result

    @api.constrains('client_dni')
    def _check_client_dni(self):
        for rec in self:
            if rec.client_dni and not re.fullmatch(r'[0-9]{8}', rec.client_dni):
                raise ValidationError("El DNI del cliente debe contener exactamente 8 dígitos numéricos.")

    @api.constrains('state', 'rejection_reason')
    def _check_rejection_reason(self):
        for rec in self:
            if rec.state == 'rejected' and not rec.rejection_reason:
                raise ValidationError("Debe indicar el motivo de rechazo.")

    @api.constrains(
        'state', 'installation_result', 'installation_category_id',
        'installation_note', 'rescheduled_install_date', 'actual_install_date',
    )
    def _check_installation_result(self):
        for rec in self:
            if rec.state in ('rescheduled', 'not_installed') and not rec.installation_result:
                raise ValidationError("Seleccione el resultado de la visita técnica.")
            if rec.installation_result in ('rescheduled', 'not_installed'):
                if not rec.installation_category_id or not rec.installation_note:
                    raise ValidationError(
                        "Indique una categoría y la observación de Back Office."
                    )
            if rec.installation_result == 'rescheduled' and not rec.rescheduled_install_date:
                raise ValidationError(
                    "Para reprogramar, indique la nueva fecha acordada con el cliente."
                )
            if (
                rec.state == 'rescheduled'
                and rec.installation_result not in ('rescheduled', 'installed')
            ):
                raise ValidationError(
                    "El resultado debe corresponder a la visita reprogramada."
                )
            if (
                rec.state == 'not_installed'
                and rec.installation_result not in ('not_installed', 'installed')
            ):
                raise ValidationError(
                    "El resultado debe corresponder a la instalación no realizada."
                )
            if rec.state == 'installed' and rec.installation_result != 'installed':
                raise ValidationError(
                    "El resultado debe indicar que la instalación se realizó."
                )
            if rec.installation_result == 'installed' and rec.state not in (
                'approved', 'rescheduled', 'not_installed', 'installed'
            ):
                raise ValidationError(
                    "No se puede registrar una instalación realizada en este estado."
                )

    @api.constrains('latitude', 'longitude')
    def _check_coordinates_range(self):
        for rec in self:
            if rec.latitude and (rec.latitude < -90.0 or rec.latitude > 90.0):
                raise ValidationError('La latitud debe estar dentro del rango [-90.0, 90.0].')
            if rec.longitude and (rec.longitude < -180.0 or rec.longitude > 180.0):
                raise ValidationError('La longitud debe estar dentro del rango [-180.0, 180.0].')

    def action_validate(self):
        for rec in self:
            rec.state = 'validation'

    def action_approve(self):
        for rec in self:
            if rec.latitude == 0.0 or rec.longitude == 0.0:
                raise ValidationError("No se puede aprobar la orden sin validar las coordenadas GPS y el checklist.")
            
            dispatch = self.env['teloconnect.almacen'].search(
                [('backoffice_id', '=', rec.id)], limit=1
            )
            if not dispatch:
                self.env['teloconnect.almacen'].create({
                    'backoffice_id': rec.id,
                    'technician_id': 'Cuadrilla por Asignar',
                })
            rec.write({'state': 'approved', 'rejection_reason': False})

    def action_return_correction(self):
        for rec in self:
            rec.state = 'en_correcion'

    def action_reject(self):
        for rec in self:
            if rec.state != 'validation':
                raise ValidationError("La orden debe estar en validación antes de rechazarla.")
            if not rec.rejection_reason:
                raise ValidationError("Debe indicar el motivo de rechazo.")
            rec.state = 'rejected'

    def action_draft(self):
        for rec in self:
            rec.write({'state': 'draft', 'rejection_reason': False})

    def action_mark_installed(self):
        for rec in self:
            if rec.state not in ('approved', 'rescheduled', 'not_installed') or not rec.warehouse_delivered:
                raise ValidationError(
                    "Primero debe completar y entregar los equipos desde el módulo Almacén."
                )
            rec.write({
                'state': 'installed',
                'installation_result': 'installed',
                'actual_install_date': fields.Date.context_today(rec),
                'installation_category_id': False,
                'installation_note': False,
                'rescheduled_install_date': False,
            })

    def action_register_installation_result(self):
        for rec in self:
            if rec.state not in ('approved', 'rescheduled', 'not_installed') or not rec.warehouse_delivered:
                raise ValidationError(
                    "Solo se puede registrar el resultado cuando la orden está pendiente "
                    "de instalación y los equipos fueron entregados al técnico."
                )
            if not rec.installation_result:
                raise ValidationError("Seleccione el resultado de la visita técnica.")
            if rec.installation_result == 'installed':
                rec.write({
                    'state': 'installed',
                    'actual_install_date': fields.Date.context_today(rec),
                    'installation_category_id': False,
                    'installation_note': False,
                    'rescheduled_install_date': False,
                })
            elif rec.installation_result == 'rescheduled':
                if not rec.installation_category_id or not rec.installation_note:
                    raise ValidationError(
                        "Indique una categoría y la observación de Back Office."
                    )
                if not rec.rescheduled_install_date:
                    raise ValidationError(
                        "Indique la nueva fecha acordada con el cliente."
                    )
                rec.write({'state': 'rescheduled', 'actual_install_date': False})
            elif rec.installation_result == 'not_installed':
                if not rec.installation_category_id or not rec.installation_note:
                    raise ValidationError(
                        "Indique una categoría y la observación de Back Office."
                    )
                rec.write({
                    'state': 'not_installed',
                    'actual_install_date': False,
                    'rescheduled_install_date': False,
                })