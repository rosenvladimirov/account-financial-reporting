# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Financial Reports',
    'version': '11.0.2.8.0',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'author': 'Rosen Vladimirov,'
              'dXFactory Ltd.,'
              'Camptocamp SA,'
              'initOS GmbH,'
              'redCOR AG,'
              'Eficent,'
              'Odoo Community Association (OCA)',
    "website": "https://odoo-community.org/",
    'depends': [
        'account',
        'account_invoicing',
        'date_range',
        'report_xml',
        'report_csv', # is not ported for 12.0
        'report_xlsx',
        'report_fillpdf',
        'account_tag_menu',
    ],
    'data': [
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/general_ledger_wizard_view.xml',
        'wizard/journal_ledger_wizard_view.xml',
        'wizard/open_items_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'wizard/vat_report_wizard_view.xml',
        'wizard/account_tag_report_wizard.xml',
        'views/menuitems.xml',
        'report/reports.xml',
        'report/templates/layouts.xml',
        'report/templates/aged_partner_balance.xml',
        'report/templates/general_ledger.xml',
        'report/templates/journal_ledger.xml',
        'report/templates/open_items.xml',
        'report/templates/trial_balance.xml',
        'report/templates/vat_report.xml',
        'report/templates/account_account_tag.xml',
        'views/account_view.xml',
        'views/analytic_account_views.xml',
        'views/report_template.xml',
        'views/report_general_ledger.xml',
        'views/report_journal_ledger.xml',
        'views/report_trial_balance.xml',
        'views/report_open_items.xml',
        'views/report_aged_partner_balance.xml',
        'views/report_vat_report.xml',
        'views/report_account_tag_report.xml',
    ],
    'qweb': [
        'static/src/xml/account_financial_reporting_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
