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