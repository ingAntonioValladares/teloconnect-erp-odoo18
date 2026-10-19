# -*- coding: utf-8 -*-


def migrate(cr, version):
    obsolete_columns = (
        'advisor_id',
        'sale_date',
        'scheduled_install_date',
        'actual_install_date',
    )
    for column in obsolete_columns:
        cr.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'teloconnect_backoffice_event' AND column_name = %s",
            (column,),
        )
        if cr.fetchone():
            cr.execute(
                'UPDATE teloconnect_backoffice_event SET %s = NULL' % column
            )