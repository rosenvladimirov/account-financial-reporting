# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import models, fields, api, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        help="If flagged, no details will be displayed in "
             "the General Ledger report (the webkit one only), "
             "only centralized amounts per period.")

class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    pdf_field_net = fields.Char("PDF Field for net", oldname="pdf_field")
    pdf_field_tax = fields.Char("PDF Field for tax")
    csv_field = fields.Integer("CSV Column for net/tax")
    xml_tag = fields.Char("XML Tag for net/tax")
    type_taxes = fields.Selection([
                            ('0', _('Tax base')),
                            ('2', _('Tax base (debit)')),
                            ('3', _('Tax base (credit)')),
                            ('1', _('Coupled tax')),
                            ('98', _('Boot Tax base and tax EU deals')),
                            ('99', _('Boot Tax base and tax')),
                            ])
    applicability = fields.Selection(selection_add=[('info', 'Informations')])
    type_info = fields.Selection([
                            ('period', 'Fiscal period'),
                            ('vat', 'Get partner VAT'),
                            ('name', 'Get partner name'),
                            ('vatcompany', 'Get company VAT'),
                            ('namecompany', 'Get company name'),
                            ('addresscompany', 'Get company address'),
                            ('movenumber', 'Get account move number'),
                            ('date', 'Get account move date'),
                            ('narration', 'Get account move narration'),
                            ('ref', 'Get account move ref')
                          ])


class AccountTax(models.Model):
    _inherit = 'account.tax'

    parent_type_tax_use = fields.Selection([('sale', 'Sales'), ('purchase', 'Purchases'), ('none', 'None')], string='Parent Tax Scope', required=True, default="none",
        help="Determines where the tax is selectable. Note : 'None' means a tax can't be used by itself, however it can still be used in a group.")
    tax_type_deal = fields.Selection(
        [('auto', _('Automatic discovery')),
         ('standard', _('Product direct selling')),
         ('service', _('Service direct selling')),
         ('ptriangles', _('Product triangles deals')),
         ('striangles', _('Service triangles deals'))],
        string="Type deal",
        help="* The 'Automatic discovery' is used when do not have special tax for other types of the 'Type deal'.\n"
             "* The 'Product direct selling' is used when this tax is configured for standard deal only with products.\n"
             "* The 'Service direct selling' is used when this tax is configured for standard deal only with services.\n"
             "* The 'Product triangles deals' is used when this tax is configured for triangles deal only with products.\n"
             "* The 'Service triangles deals' is used when this tax is configured for triangles deal only with services.\n")

    @api.onchange('type_tax_use')
    def onchange_type_tax_use(self):
        if self.children_tax_ids:
            for line in self.children_tax_ids:
                line.parent_type_tax_use = self.type_tax_use
