# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestBackOfficeValidation(TransactionCase):

    def setUp(self):
        super(TestBackOfficeValidation, self).setUp()
        # Inicialización del entorno de pruebas
        self.BackOfficeModel = self.env['teloconnect.backoffice']

    def test_01_dni_invalid_length(self):
        """Validar que un DNI con longitud distinta a 8 dígitos arroje ValidationError"""
        with self.assertRaises(ValidationError):
            self.BackOfficeModel.create({
                'client_name': 'Cliente DNI Invalido',
                'client_dni': '12345',  # Menos de 8 dígitos
                'district': 'chiclayo',
                'installation_address': 'Calle Real 123',
                'latitude': -6.77137,
                'longitude': -79.84088,
            })

    def test_01b_dni_required(self):
        with self.assertRaises(ValidationError):
            self.BackOfficeModel.create({
                'client_name': 'Cliente Sin DNI',
                'district': 'chiclayo',
                'installation_address': 'Calle Real 123',
            })

    def test_02_coordinates_out_of_bounds(self):
        """Validar que latitud/longitud fuera del rango permitido arroje error"""
        with self.assertRaises(ValidationError):
            self.BackOfficeModel.create({
                'client_name': 'Cliente Coordenadas Erradas',
                'client_dni': '76543210',
                'district': 'chiclayo',
                'installation_address': 'Av. Balta 500',
                'latitude': 95.0,  # Latitud fuera de rango
                'longitude': -79.84088,
            })
            
    def test_03_approve_order_without_validation(self):
        """Validar que aprobar una orden sin coordenadas GPS válidas o checklist devuelva error"""
        with self.assertRaises(ValidationError):
            # Creamos una orden con datos incompletos o sin validación GPS/checklist requerida
            order = self.BackOfficeModel.create({
                'client_name': 'Cliente Sin Validar',
                'client_dni': '12345678',
                'district': 'chiclayo',
                'installation_address': 'Av. Grau 100',
                'latitude': 0.0,    # Coordenadas vacías o no válidas para aprobación
                'longitude': 0.0,
            })
            # Intentar ejecutar la acción de aprobación o cambiar el estado sin cumplir requisitos
            order.action_approve()  # Reemplaza 'action_approve' por el nombre real de tu método en el modelo si es distinto

    def test_04_approve_order_with_zero_longitude(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Longitud Cero',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'latitude': -6.77137,
            'longitude': 0.0,
        })
        with self.assertRaises(ValidationError):
            order.action_approve()

    def test_05_approval_creates_only_one_dispatch(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Una Orden',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'latitude': -6.77137,
            'longitude': -79.84088,
        })
        order.action_approve()
        order.action_approve()
        self.assertEqual(
            self.env['teloconnect.almacen'].search_count([('backoffice_id', '=', order.id)]),
            1,
        )

    def test_06_reject_requires_reason(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Sin Motivo',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
        })
        order.action_validate()
        with self.assertRaises(ValidationError):
            order.action_reject()

    def test_07_duplicate_equipment_series_rejected(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Series Duplicadas',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'ont_qty': 2,
            'deco_qty': 1,
        })
        dispatch = self.env['teloconnect.almacen'].create({
            'backoffice_id': order.id,
            'technician_id': 'Cuadrilla de Prueba',
            'ont_series': 'ONT-001, ont-001',
            'deco_series': 'DEC-001',
        })
        with self.assertRaises(ValidationError):
            dispatch.action_assign_equipment()

    def test_08_equipment_series_require_matching_prefix(self):
        cases = [
            ('ont_qty', 'ont_series', 'ROUTER-001'),
            ('deco_qty', 'deco_series', 'DECOD-001'),
            ('repeater_qty', 'repeater_series', 'WIFI-001'),
        ]
        for quantity_field, series_field, invalid_series in cases:
            order = self.BackOfficeModel.create({
                'client_name': 'Cliente Prefijo Inválido',
                'client_dni': '12345678',
                'district': 'chiclayo',
                'installation_address': 'Av. Grau 100',
                quantity_field: 1,
            })
            dispatch = self.env['teloconnect.almacen'].create({
                'backoffice_id': order.id,
                'technician_id': 'Cuadrilla de Prueba',
                series_field: invalid_series,
            })
            with self.assertRaises(ValidationError):
                dispatch.action_assign_equipment()

    def test_08_duplicate_equipment_series_across_dispatches_rejected(self):
        first_order = self.BackOfficeModel.create({
            'client_name': 'Primer Cliente Serie Global',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
        })
        first_dispatch = self.env['teloconnect.almacen'].create({
            'backoffice_id': first_order.id,
            'technician_id': 'Cuadrilla 1',
            'ont_series': 'ONT-GLOBAL-TEST',
        })
        first_dispatch.action_assign_equipment()

        second_order = self.BackOfficeModel.create({
            'client_name': 'Segundo Cliente Serie Global',
            'client_dni': '87654321',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 200',
        })
        second_dispatch = self.env['teloconnect.almacen'].create({
            'backoffice_id': second_order.id,
            'technician_id': 'Cuadrilla 2',
            'ont_series': 'ont-global-test',
        })
        with self.assertRaises(ValidationError):
            second_dispatch.action_assign_equipment()

    def test_08b_existing_duplicate_series_can_be_corrected(self):
        orders = self.BackOfficeModel.create([
            {
                'client_name': 'Cliente Serie Histórica 1',
                'client_dni': '11112222',
                'district': 'chiclayo',
                'installation_address': 'Av. Grau 100',
            },
            {
                'client_name': 'Cliente Serie Histórica 2',
                'client_dni': '33334444',
                'district': 'chiclayo',
                'installation_address': 'Av. Grau 200',
            },
        ])
        dispatches = self.env['teloconnect.almacen'].create([
            {
                'backoffice_id': orders[0].id,
                'technician_id': 'Cuadrilla 1',
                'ont_series': 'ONT-LEGACY-DUPLICATE',
            },
            {
                'backoffice_id': orders[1].id,
                'technician_id': 'Cuadrilla 2',
                'ont_series': 'ONT-LEGACY-DUPLICATE',
            },
        ])
        dispatches[0].write({'ont_series': 'ONT-CORRECTED-001'})
        self.assertEqual(dispatches[0].ont_series, 'ONT-CORRECTED-001')

    def test_09_correct_equipment_prefixes_are_accepted(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Prefijos Correctos',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'ont_qty': 1,
            'deco_qty': 1,
            'repeater_qty': 1,
        })
        dispatch = self.env['teloconnect.almacen'].create({
            'backoffice_id': order.id,
            'technician_id': 'Cuadrilla de Prueba',
            'ont_series': 'ONT-TEST-VALID-001',
            'deco_series': 'DEC-TEST-VALID-001',
            'repeater_series': 'REP-TEST-VALID-001',
        })
        dispatch.action_assign_equipment()
        self.assertEqual(dispatch.state, 'entregado_tecnico')

    def test_10_cannot_mark_installed_before_warehouse_delivery(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Pendiente de Almacén',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'latitude': -6.77137,
            'longitude': -79.84088,
        })
        order.action_approve()
        with self.assertRaises(ValidationError):
            order.action_mark_installed()

    def test_11_can_mark_installed_after_warehouse_delivery(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Equipos Entregados',
            'client_dni': '12345678',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 100',
            'latitude': -6.77137,
            'longitude': -79.84088,
        })
        order.action_approve()
        dispatch = order.dispatch_ids
        dispatch.write({'ont_series': 'ONT-TEST-001'})
        dispatch.action_assign_equipment()
        order.action_mark_installed()
        self.assertEqual(order.state, 'installed')
        self.assertFalse(order.actual_install_date)

    def test_12_full_order_lifecycle_is_logged_as_snapshots(self):
        order = self.BackOfficeModel.create({
            'client_name': 'Cliente Historial Completo',
            'client_dni': '55556666',
            'district': 'chiclayo',
            'installation_address': 'Av. Grau 300',
            'latitude': -6.77137,
            'longitude': -79.84088,
        })
        order.action_validate()
        order.action_return_correction()
        order.action_validate()
        order.write({'rejection_reason': 'sin_cobertura'})
        order.action_reject()
        order.action_draft()
        order.action_validate()
        order.action_approve()

        dispatch = order.dispatch_ids
        dispatch.write({'ont_series': 'ONT-HIST-001'})
        dispatch.action_assign_equipment()
        order.action_mark_installed()

        events = order.history_event_ids.sorted('id')
        commercial_states = events.filtered(
            lambda event: event.event_type == 'commercial_state'
        ).mapped('commercial_state')
        self.assertIn('en_correcion', commercial_states)
        self.assertIn('rejected', commercial_states)
        self.assertIn('approved', commercial_states)
        self.assertIn('installed', commercial_states)

        rejected_event = events.filtered(
            lambda event: event.commercial_state == 'rejected'
        )[-1]
        self.assertEqual(rejected_event.rejection_reason, 'sin_cobertura')

        approved_event = events.filtered(
            lambda event: event.event_type == 'commercial_state'
            and event.commercial_state == 'approved'
        )[-1]
        self.assertEqual(approved_event.warehouse_state, 'pendiente_asig')

        delivered_event = events.filtered(
            lambda event: event.warehouse_state == 'entregado_tecnico'
        )[-1]
        self.assertEqual(delivered_event.ont_series, 'ONT-HIST-001')

    def test_13_history_excludes_crm_and_operator_owned_dates(self):
        event_fields = self.env['teloconnect.backoffice.event']._fields
        for field_name in (
            'advisor_id', 'sale_date', 'scheduled_install_date', 'actual_install_date'
        ):
            self.assertNotIn(field_name, event_fields)