# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    for order in env['teloconnect.backoffice'].search([]):
        if not order.history_event_ids:
            order._log_history_event(
                'baseline',
                ['state', 'rejection_reason'],
                user_name='Migración de estado actual',
            )