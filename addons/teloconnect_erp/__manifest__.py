{
    'name': 'TeloConnect ERP',
    'version': '18.0.1.0.0',
    'category': 'Operations',
    'summary': 'Módulo de Back Office y Almacén para TeloConnect',
    'depends': ['base', 'mail', 'stock'],
    'data': [
    'security/security_groups.xml',
    'security/ir.model.access.csv',
    'security/ir_sequence_data.xml',  # <-- Verifica que la ruta coincida
    'views/backoffice_views.xml',
    'views/almacen_views.xml',
    ],
    'application': True,  # <-- ¡ESTO ES VITAL PARA QUE APAREZCA COMO APLICACIÓN PRINCIPAL!
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}