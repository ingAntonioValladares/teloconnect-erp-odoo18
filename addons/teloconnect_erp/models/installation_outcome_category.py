# -*- coding: utf-8 -*-
from odoo import fields, models


class TeloConnectInstallationOutcomeCategory(models.Model):
    _name = 'teloconnect.installation.outcome.category'
    _description = 'Categorías de Resultado de Instalación'
    _order = 'sequence, name'

    name = fields.Char(string='Categoría', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
