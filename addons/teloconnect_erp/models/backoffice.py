import json
import urllib.request
import urllib.parse
import ssl
# -*- coding: utf-8 -*-
import re
import unicodedata

def _normalize_name(text):
    if not text:
        return ''
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(text).strip().lower())
        if unicodedata.category(c) != 'Mn'
    )

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

CHICLAYO_DISTRICTS = [
    ('Chiclayo', 'Chiclayo'),
    ('Cayaltí', 'Cayaltí'),
    ('Chongoyape', 'Chongoyape'),
    ('Eten', 'Eten'),
    ('José Leonardo Ortiz', 'José Leonardo Ortiz'),
    ('La Victoria', 'La Victoria'),
    ('Lagunas', 'Lagunas'),
    ('Monsefú', 'Monsefú'),
    ('Nueva Arica', 'Nueva Arica'),
    ('Oyotún', 'Oyotún'),
    ('Picsi', 'Picsi'),
    ('Pimentel', 'Pimentel'),
    ('Pomalca', 'Pomalca'),
    ('Pucalá', 'Pucalá'),
    ('Puerto Eten', 'Puerto Eten'),
    ('Reque', 'Reque'),
    ('Santa Rosa', 'Santa Rosa'),
    ('Saña', 'Saña'),
    ('Tumán', 'Tumán'),
    ('Pátapo', 'Pátapo'),
]

LAMBAYEQUE_DISTRICTS = [
    ('Lambayeque', 'Lambayeque'),
    ('Chochope', 'Chochope'),
    ('Íllimo', 'Íllimo'),
    ('Jayanca', 'Jayanca'),
    ('Mochumí', 'Mochumí'),
    ('Mórrope', 'Mórrope'),
    ('Motupe', 'Motupe'),
    ('Olmos', 'Olmos'),
    ('Pacora', 'Pacora'),
    ('Salas', 'Salas'),
    ('San José', 'San José'),
    ('Túcume', 'Túcume'),
]

FERRENAFE_DISTRICTS = [
    ('Ferreñafe', 'Ferreñafe'),
    ('Cañaris', 'Cañaris'),
    ('Incahuasi', 'Incahuasi'),
    ('Manuel Antonio Mesones Muro', 'Manuel Antonio Mesones Muro'),
    ('Pitipo', 'Pitipo'),
    ('Pueblo Nuevo', 'Pueblo Nuevo'),
]

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
    district_chiclayo = fields.Selection(
        CHICLAYO_DISTRICTS,
        string='Distrito',
        compute='_compute_district_selection',
        inverse='_inverse_district_selection',
        store=False,
    )
    district_lambayeque = fields.Selection(
        LAMBAYEQUE_DISTRICTS,
        string='Distrito',
        compute='_compute_district_selection',
        inverse='_inverse_district_selection',
        store=False,
    )
    district_ferrenafe = fields.Selection(
        FERRENAFE_DISTRICTS,
        string='Distrito',
        compute='_compute_district_selection',
        inverse='_inverse_district_selection',
        store=False,
    )

    @api.onchange('province')
    def _onchange_province(self):
        if self.province == 'chiclayo':
            valid = [k for k, _ in CHICLAYO_DISTRICTS]
            if self.district not in valid:
                self.district = False
                self.district_chiclayo = False
            else:
                self.district_chiclayo = self.district
            self.district_lambayeque = False
            self.district_ferrenafe = False
        elif self.province == 'lambayeque':
            valid = [k for k, _ in LAMBAYEQUE_DISTRICTS]
            if self.district not in valid:
                self.district = False
                self.district_lambayeque = False
            else:
                self.district_lambayeque = self.district
            self.district_chiclayo = False
            self.district_ferrenafe = False
        elif self.province == 'ferrenafe':
            valid = [k for k, _ in FERRENAFE_DISTRICTS]
            if self.district not in valid:
                self.district = False
                self.district_ferrenafe = False
            else:
                self.district_ferrenafe = self.district
            self.district_chiclayo = False
            self.district_lambayeque = False

    @api.depends('district', 'province')
    def _compute_district_selection(self):
        for rec in self:
            dist_norm = _normalize_name(rec.district)
            rec.district_chiclayo = False
            rec.district_lambayeque = False
            rec.district_ferrenafe = False
            if rec.province == 'chiclayo' and dist_norm:
                match = next((k for k, _ in CHICLAYO_DISTRICTS if _normalize_name(k) == dist_norm), False)
                rec.district_chiclayo = match
            elif rec.province == 'lambayeque' and dist_norm:
                match = next((k for k, _ in LAMBAYEQUE_DISTRICTS if _normalize_name(k) == dist_norm), False)
                rec.district_lambayeque = match
            elif rec.province == 'ferrenafe' and dist_norm:
                match = next((k for k, _ in FERRENAFE_DISTRICTS if _normalize_name(k) == dist_norm), False)
                rec.district_ferrenafe = match

    def _inverse_district_selection(self):
        for rec in self:
            if rec.province == 'chiclayo' and rec.district_chiclayo:
                rec.district = rec.district_chiclayo
            elif rec.province == 'lambayeque' and rec.district_lambayeque:
                rec.district = rec.district_lambayeque
            elif rec.province == 'ferrenafe' and rec.district_ferrenafe:
                rec.district = rec.district_ferrenafe

    installation_address = fields.Text(string='Dirección Completa (Vía/Mz/Lte/Urb/A.H.)', required=True)
    
    # Coordenadas GPS para validación geográfica
    latitude = fields.Float(string='Latitud', digits=(10, 7), tracking=True)
    longitude = fields.Float(string='Longitud', digits=(10, 7), tracking=True)
    map_widget = fields.Char(string='Ubicación en Mapa', store=False)

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
            prov = vals.get('province', 'chiclayo')
            if not vals.get('district'):
                if prov == 'chiclayo' and vals.get('district_chiclayo'):
                    vals['district'] = vals['district_chiclayo']
                elif prov == 'lambayeque' and vals.get('district_lambayeque'):
                    vals['district'] = vals['district_lambayeque']
                elif prov == 'ferrenafe' and vals.get('district_ferrenafe'):
                    vals['district'] = vals['district_ferrenafe']
            if not vals.get('client_dni'):
                raise ValidationError("El DNI del cliente es obligatorio.")
            if vals.get('name', _('New')) == _('New') or vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('teloconnect.backoffice') or 'BO/00001'
        records = super(TeloConnectBackOffice, self).create(vals_list)
        for record, vals in zip(records, vals_list):
            record._log_history_event('created', vals.keys())
        return records

    def write(self, vals):
        prov = vals.get('province', self[:1].province if self else False)
        if not vals.get('district'):
            if (prov == 'chiclayo' or (not prov and any(r.province == 'chiclayo' for r in self))) and vals.get('district_chiclayo'):
                vals['district'] = vals['district_chiclayo']
            elif (prov == 'lambayeque' or (not prov and any(r.province == 'lambayeque' for r in self))) and vals.get('district_lambayeque'):
                vals['district'] = vals['district_lambayeque']
            elif (prov == 'ferrenafe' or (not prov and any(r.province == 'ferrenafe' for r in self))) and vals.get('district_ferrenafe'):
                vals['district'] = vals['district_ferrenafe']
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

    @api.model
    def search_dni_api(self, dni):
        """Consulta el DNI en la API y devuelve el nombre formateado."""
        dni = (dni or '').strip()
        if not dni or len(dni) != 8 or not dni.isdigit():
            return {
                'success': False,
                'error': 'El DNI debe contener exactamente 8 dígitos numéricos.'
            }

        # 1. Intentar con API de apis.net.pe
        token = self.env['ir.config_parameter'].sudo().get_param('teloconnect.dni_api_token', default='')
        url = 'https://api.apis.net.pe/v1/dni?numero=%s' % dni
        headers = {
            'User-Agent': 'TeloConnect-ERP/1.0 (Odoo 18)',
            'Accept': 'application/json',
        }
        if token:
            headers['Authorization'] = 'Bearer %s' % token.strip()

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    raw_nombre = data.get('nombre')
                    if not raw_nombre:
                        nombres = data.get('nombres', '')
                        paterno = data.get('apellidoPaterno', '')
                        materno = data.get('apellidoMaterno', '')
                        raw_nombre = ('%s %s %s' % (nombres, paterno, materno)).strip()

                    if raw_nombre:
                        formatted = ' '.join(part.capitalize() for part in raw_nombre.split())
                        return {
                            'success': True,
                            'name': formatted,
                            'dni': dni,
                        }
        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                return {'success': False, 'error': 'DNI %s no encontrado en el padrón.' % dni}
        except Exception:
            pass

        # 2. Fallback: buscar en la base de datos local / historial
        existing = self.search([('client_dni', '=', dni), ('client_name', '!=', False)], limit=1)
        if existing and existing.client_name:
            return {
                'success': True,
                'name': existing.client_name,
                'dni': dni,
                'source': 'history',
            }

        existing_evt = self.env['teloconnect.backoffice.event'].sudo().search(
            [('client_dni', '=', dni), ('client_name', '!=', False)], limit=1
        )
        if existing_evt and existing_evt.client_name:
            return {
                'success': True,
                'name': existing_evt.client_name,
                'dni': dni,
                'source': 'history',
            }

        return {
            'success': False,
            'error': 'No se pudo obtener información para el DNI %s (servicio temporalmente ocupado).' % dni
        }

    def action_search_dni(self):
        """Acción de botón Python para consultar DNI."""
        self.ensure_one()
        dni = (self.client_dni or '').strip()
        if not dni:
            raise ValidationError('Ingrese primero el número de DNI.')
        res = self.search_dni_api(dni)
        if res.get('success') and res.get('name'):
            self.client_name = res['name']
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'DNI Encontrado',
                    'message': 'Se completó el nombre: %s' % res['name'],
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise ValidationError(res.get('error') or ('No se encontró información para el DNI %s.' % dni))

    @api.onchange('client_dni')
    def _onchange_client_dni(self):
        """Auto-consulta si el usuario escribe 8 dígitos y client_name está vacío."""
        if self.client_dni and len(self.client_dni.strip()) == 8 and self.client_dni.strip().isdigit():
            if not self.client_name:
                res = self.search_dni_api(self.client_dni.strip())
                if res.get('success') and res.get('name'):
                    self.client_name = res['name']

    @api.model
    def reverse_geocode_api(self, lat, lng):
        """Obtiene la dirección física, provincia y distrito a partir de coordenadas GPS."""
        try:
            lat = float(lat)
            lng = float(lng)
            if lat == 0.0 and lng == 0.0:
                return {'success': False, 'error': 'Coordenadas en 0.0'}

            url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat=%s&lon=%s&zoom=18&addressdetails=1' % (lat, lng)
            req = urllib.request.Request(url, headers={'User-Agent': 'TeloConnect-ERP/1.0 (Odoo 18)'})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    addr = data.get('address', {})
                    
                    road = addr.get('road') or addr.get('pedestrian') or addr.get('street') or ''
                    num = addr.get('house_number') or addr.get('street_number')
                    city_block = addr.get('city_block') or addr.get('block')
                    allotment = addr.get('allotment') or addr.get('plot')
                    suburb = addr.get('neighbourhood') or addr.get('suburb') or addr.get('residential') or ''
                    city_candidate = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('municipality') or ''

                    # Mapeo de distritos conocidos
                    all_districts = {
                        'chiclayo': {_normalize_name(k): k for k, _ in CHICLAYO_DISTRICTS},
                        'lambayeque': {_normalize_name(k): k for k, _ in LAMBAYEQUE_DISTRICTS},
                        'ferrenafe': {_normalize_name(k): k for k, _ in FERRENAFE_DISTRICTS},
                    }

                    # Detectar provincia
                    prov_candidate = _normalize_name(addr.get('county') or addr.get('region') or '')
                    detected_province = False
                    if 'ferrenafe' in prov_candidate:
                        detected_province = 'ferrenafe'
                    elif 'lambayeque' in prov_candidate:
                        detected_province = 'lambayeque'
                    elif 'chiclayo' in prov_candidate:
                        detected_province = 'chiclayo'

                    # Detectar distrito
                    detected_district = False
                    for candidate in [city_candidate, suburb, addr.get('town'), addr.get('village'), addr.get('suburb')]:
                        norm_c = _normalize_name(candidate)
                        if not norm_c:
                            continue
                        provinces_to_check = [detected_province] if detected_province else ['chiclayo', 'lambayeque', 'ferrenafe']
                        for p in provinces_to_check:
                            if p and norm_c in all_districts[p]:
                                detected_district = all_districts[p][norm_c]
                                detected_province = p
                                break
                        if detected_district:
                            break

                    if detected_district and not detected_province:
                        for p, ddict in all_districts.items():
                            if _normalize_name(detected_district) in ddict:
                                detected_province = p
                                break

                    # Formatear dirección limpia
                    parts = []
                    if road:
                        if num:
                            num_str = str(num).strip()
                            parts.append('%s %s' % (road, num_str))
                        elif city_block:
                            if allotment:
                                parts.append('%s %s %s' % (road, city_block, allotment))
                            else:
                                parts.append('%s %s' % (road, city_block))
                        else:
                            parts.append(road)
                    elif city_block:
                        if allotment:
                            parts.append('%s %s' % (city_block, allotment))
                        else:
                            parts.append(city_block)
                    elif suburb:
                        parts.append(suburb)

                    if suburb and suburb not in str(parts):
                        parts.append(suburb)
                    if detected_district:
                        parts.append(detected_district)
                    elif city_candidate and city_candidate not in str(parts):
                        parts.append(city_candidate)

                    clean_address = ', '.join(parts) if parts else (data.get('display_name') or '')

                    return {
                        'success': True,
                        'address': clean_address,
                        'province': detected_province,
                        'district': detected_district,
                        'full': data.get('display_name', ''),
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': False, 'error': 'No se pudo obtener la dirección.'}

    @api.model
    def resolve_map_input(self, raw_input):
        """Procesa una entrada de mapa: puede ser un enlace de Google Maps,
        coordenadas (lat, lng) o una dirección de texto."""
        raw = (raw_input or '').strip()
        if not raw:
            return {'success': False, 'error': 'Entrada vacía.'}

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 1. Expandir enlaces cortos (maps.app.goo.gl o goo.gl)
        if 'goo.gl' in raw or 'maps.app' in raw:
            url_match = re.search(r'https?://[^\s]+', raw)
            if url_match:
                try:
                    req = urllib.request.Request(url_match.group(0), headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
                        raw = r.geturl()
                except Exception:
                    pass

        detected_address = None
        lat = None
        lng = None

        # 2. Extraer dirección/lugar de URL de Google Maps
        place_match = re.search(r'/(?:place|search)/([^/@?]+)', raw)
        if place_match:
            raw_place = urllib.parse.unquote_plus(place_match.group(1)).strip()
            clean = re.sub(r',?\s*\b\d{5}\b', '', raw_place)
            clean = re.sub(r',?\s*Per[úu]', '', clean, flags=re.IGNORECASE).strip(' ,')
            detected_address = clean
        elif 'q=' in raw:
            q_match = re.search(r'[?&]q=([^&]+)', raw)
            if q_match:
                val = urllib.parse.unquote_plus(q_match.group(1)).strip()
                if not re.match(r'^-?\d{1,2}\.\d+[,\s]+-?\d{1,3}\.\d+$', val):
                    clean = re.sub(r',?\s*\b\d{5}\b', '', val)
                    clean = re.sub(r',?\s*Per[úu]', '', clean, flags=re.IGNORECASE).strip(' ,')
                    detected_address = clean

        # 3. Extraer coordenadas si están presentes (@-6.7725,-79.838 o -6.7725, -79.838)
        coord_match = re.search(r'@?(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)', raw)
        if coord_match:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))

        # 4. Si no es URL ni solo coordenadas, es una dirección de texto
        if not detected_address and not raw.startswith('http'):
            cleaned = re.sub(r'\(?@?-?\d{1,2}\.\d+[,\s]+-?\d{1,3}\.\d+\)?', '', raw).strip(' ,()')
            if cleaned:
                detected_address = cleaned

        # 5. Si tenemos dirección pero no coordenadas, geocodificar con Nominatim
        if detected_address and (lat is None or lng is None):
            def _search(q):
                try:
                    url = 'https://nominatim.openstreetmap.org/search?q=%s&format=json&limit=1' % urllib.parse.quote(q)
                    req = urllib.request.Request(url, headers={'User-Agent': 'TeloConnect-ERP/1.0'})
                    with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
                        return json.loads(r.read().decode('utf-8'))
                except Exception:
                    return []

            query = detected_address if any(w in detected_address.lower() for w in ['chiclayo', 'lambayeque', 'ferrenafe']) else ('%s, Chiclayo' % detected_address)
            s_res = _search(query)
            if not s_res:
                sim = re.sub(r'\b(mz\.?|manzana|lote|lt\.?)\s*[a-zA-Z0-9_\-]+', '', detected_address, flags=re.IGNORECASE).strip(' ,')
                if sim:
                    s_res = _search('%s, Lambayeque' % sim)
            if s_res:
                lat = float(s_res[0]['lat'])
                lng = float(s_res[0]['lon'])

        # 6. Si tenemos coordenadas, llamar a reverse_geocode_api para obtener datos de provincia y distrito
        geo_data = {}
        if lat is not None and lng is not None:
            geo_data = self.reverse_geocode_api(lat, lng)

        final_address = detected_address or geo_data.get('address') or ''
        final_province = geo_data.get('province')
        final_district = geo_data.get('district')

        # 7. Priorizar distrito identificado en el texto de la dirección
        norm_addr = _normalize_name(final_address)
        sorted_districts = []
        for p, dlist in [('chiclayo', CHICLAYO_DISTRICTS), ('lambayeque', LAMBAYEQUE_DISTRICTS), ('ferrenafe', FERRENAFE_DISTRICTS)]:
            for orig_name, _ in dlist:
                sorted_districts.append((_normalize_name(orig_name), orig_name, p))
        sorted_districts.sort(key=lambda x: len(x[0]), reverse=True)

        for norm_k, orig_name, p in sorted_districts:
            if norm_k in norm_addr:
                final_district = orig_name
                final_province = p
                break

        return {
            'success': True,
            'address': final_address,
            'latitude': lat if lat is not None else 0.0,
            'longitude': lng if lng is not None else 0.0,
            'province': final_province,
            'district': final_district,
        }
