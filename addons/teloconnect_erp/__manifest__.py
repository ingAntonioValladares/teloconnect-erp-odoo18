# -*- coding: utf-8 -*-
{
    'name': 'TeloConnect ERP',
    'version': '1.0',
    'summary': 'Gestion de Back Office y Almacen',
    'category': 'Services',
    'author': 'TeloConnect',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/backoffice_views.xml',
        'views/almacen_views.xml',
    ],
    'installable': True,
    'application': True,
}