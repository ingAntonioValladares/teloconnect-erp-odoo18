# -*- coding: utf-8 -*-
{
    'name': 'TeloConnect ERP - Call Center & Logística',
    'version': '18.0.1.0.0',
    'category': 'Sales/Telecommunications',
    'summary': 'Gestión de Back Office y Almacén para distribuidor de servicios hogar de telecomunicaciones',
    'author': 'TeloConnect ERP Team',
    'website': 'https://www.teloconnect.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/backoffice_views.xml',
        'views/almacen_views.xml',
    ],
    'demo': [
        'demo/backoffice_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}