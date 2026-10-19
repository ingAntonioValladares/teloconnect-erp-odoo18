# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TeloConnectAlmacen(models.Model):
    _name = 'teloconnect.almacen'
    _description = 'Despacho de Almacén y Logística'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    _history_tracked_fields = {
        'technician_id', 'dispatch_date', 'ont_series', 'deco_series',
        'repeater_series',
    }

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

    def _get_series_values(self, values=None):
        values = values or {}
        result = {}
        for field_name in ('ont_series', 'deco_series', 'repeater_series'):
            raw_value = values.get(field_name, self[field_name])
            result[field_name] = [
                item.strip()
                for item in (raw_value or '').replace('\n', ',').split(',')
                if item.strip()
            ]
        return result

    def _validate_series_values(self, series_values, validate_quantities):
        specifications = [
            ('ont_series', self.ont_qty_required, 'Router ONT', 'ONT-'),
            ('deco_series', self.deco_qty_required, 'Decodificador', 'DEC-'),
            ('repeater_series', self.repeater_qty_required, 'Repetidor', 'REP-'),
        ]
        identifiers = []
        for field_name, required_qty, equipment_label, prefix in specifications:
            values = series_values[field_name]
            if validate_quantities and len(values) != required_qty:
                raise ValidationError(
                    _("Error de Cantidad: %(equipment)s requiere %(required)d identificadores y se ingresaron %(actual)d.") % {
                        'equipment': equipment_label,
                        'required': required_qty,
                        'actual': len(values),
                    }
                )
            invalid_values = [
                value for value in values
                if not value.upper().startswith(prefix)
                or not value[len(prefix):].strip()
            ]
            if invalid_values:
                raise ValidationError(
                    _("Cada identificador de %(equipment)s debe comenzar con %(prefix)s y contener un valor después del prefijo. Valor inválido: %(value)s") % {
                        'equipment': equipment_label,
                        'prefix': prefix,
                        'value': invalid_values[0],
                    }
                )
            identifiers.extend(values)

        normalized = [value.casefold() for value in identifiers]
        if len(normalized) != len(set(normalized)):
            raise ValidationError(_("No se puede asignar la misma serie o MAC a más de un equipo."))
        return identifiers

    def _check_series_not_used_elsewhere(self, identifiers):
        self.env.cr.execute(
            'LOCK TABLE teloconnect_almacen IN SHARE ROW EXCLUSIVE MODE'
        )
        other_dispatches = self.search([('id', '!=', self.id)])
        used_identifiers = {}
        for dispatch in other_dispatches:
            dispatch_series = dispatch._get_series_values()
            for field_name in ('ont_series', 'deco_series', 'repeater_series'):
                for identifier in dispatch_series[field_name]:
                    used_identifiers.setdefault(identifier.casefold(), dispatch)

        for identifier in identifiers:
            existing_dispatch = used_identifiers.get(identifier.casefold())
            if existing_dispatch:
                raise ValidationError(
                    _("El identificador %(identifier)s ya está asignado al despacho %(dispatch)s.") % {
                        'identifier': identifier,
                        'dispatch': existing_dispatch.name,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda item: item.state == 'entregado_tecnico'):
            identifiers = record._validate_series_values(
                record._get_series_values(), validate_quantities=True
            )
            record._check_series_not_used_elsewhere(identifiers)
        for record, vals in zip(records, vals_list):
            record.backoffice_id._log_history_event(
                'warehouse_created', vals.keys()
            )
        return records

    def write(self, vals):
        series_fields = {'ont_series', 'deco_series', 'repeater_series'}
        changed_series_fields = series_fields.intersection(vals)
        should_validate = bool(changed_series_fields) or vals.get('state') == 'entregado_tecnico'
        watched_fields = self._history_tracked_fields.intersection(vals)
        previous = {
            record.id: {
                field_name: record[field_name] for field_name in watched_fields
            }
            for record in self
        }
        previous_states = {record.id: record.state for record in self}
        if should_validate:
            for record in self:
                series_values = record._get_series_values(vals)
                validate_quantities = (
                    vals.get('state', record.state) == 'entregado_tecnico'
                )
                identifiers = record._validate_series_values(
                    series_values, validate_quantities=validate_quantities
                )
                if not validate_quantities:
                    identifiers = [
                        identifier
                        for field_name in changed_series_fields
                        for identifier in series_values[field_name]
                    ]
                record._check_series_not_used_elsewhere(identifiers)
        result = super().write(vals)
        for record in self:
            changed_fields = [
                field_name for field_name, old_value in previous[record.id].items()
                if old_value != record[field_name]
            ]
            if previous_states[record.id] != record.state:
                record.backoffice_id._log_history_event(
                    'warehouse_state', ['state'] + changed_fields
                )
            elif changed_fields:
                record.backoffice_id._log_history_event(
                    'warehouse_update', changed_fields
                )
        return result

    def action_assign_equipment(self):
        for record in self:
            series_values = record._get_series_values()
            identifiers = record._validate_series_values(
                series_values, validate_quantities=True
            )

            if not record.technician_id:
                raise ValidationError(_("Debe asignar un Técnico o Cuadrilla antes de procesar el despacho."))

            record.state = 'entregado_tecnico'