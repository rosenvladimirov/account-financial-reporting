# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Partner Outstanding Statement',
    'version': '11.0.3.0.0',
    'category': 'Accounting & Finance',
    'summary': 'OCA Financial Reports',
    'author': "RosenVladimirov (BioPrint Ltd.), Eficent, Odoo Community Association (OCA)",
    'website': 'https://github.com/rosenvladimirov/account-financial-reporting',
    'license': 'AGPL-3',
    'depends': [
        'account_invoicing',
        'product_properties',
        'base_comment_template',
        'product_properties_comment_template',
        'web_widget_digitized_signature',
        'web_digitized_company_stamp',
        'product_properties_issue_user',
    ],
    'data': [
        'views/statement.xml',
        'wizard/customer_outstanding_statement_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
