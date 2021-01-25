# © 2011 Guewen Baconnier (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.account.models import account as account


class AccountAccount(models.Model):
    _inherit = 'account.account'

    centralized = fields.Boolean(
        'Centralized',
        help="If flagged, no details will be displayed in "
             "the General Ledger report (the webkit one only), "
             "only centralized amounts per period.")
    account_group_id = fields.Many2one('account.group', related="group_id.parent_id")
    section_group_id = fields.Many2one('account.group', compute="_compute_section_group_id")


    @api.multi
    @api.depends('group_id')
    def _compute_section_group_id(self):
        for group in self:
            group.section_group_id = False
            if group.group_id.parent_id:
                group.section_group_id = group.group_id.parent_id.parent_id

    @api.onchange('code')
    def onchange_code(self):
        AccountGroup = self.env['account.group']

        group = False
        code_prefix = self.code

        # find group with longest matching prefix
        while code_prefix:
            matching_group = AccountGroup.search([('code_prefix', '=', code_prefix), ('company_id', '=', self.company_id.id)], limit=1)
            if matching_group:
                group = matching_group
                break
            code_prefix = code_prefix[:-1]
        if self.code and not group:
            raise UserError(_('I can\'t find a category for this account.'))
        self.group_id = group
        if self.code and self.group_id and len(self.code.strip()) != self.group_id.max_counter:
            raise UserError(_('Number of digits characters in the code is not allowed.'))
        if group and group.properties_user_type_id:
            self.user_type_id = group.properties_user_type_id
            self.reconcile = group.properties_reconcile


account.AccountAccount.onchange_code = AccountAccount.onchange_code


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    pdf_field_net = fields.Char("PDF Field for net", oldname="pdf_field")
    pdf_field_tax = fields.Char("PDF Field for tax")
    pdf_field_balance = fields.Char("PDF Field for balance")
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
    #tax_type_deal = fields.Selection(
    #    [('auto', _('Automatic discovery')),
    #     ('standard', _('Product direct selling')),
    #     ('service', _('Service direct selling')),
    #     ('ptriangles', _('Product triangles deals')),
    #     ('striangles', _('Service triangles deals'))],
    #    string="Type deal",
    #    help="* The 'Automatic discovery' is used when do not have special tax for other types of the 'Type deal'.\n"
    #         "* The 'Product direct selling' is used when this tax is configured for standard deal only with products.\n"
    #         "* The 'Service direct selling' is used when this tax is configured for standard deal only with services.\n"
    #         "* The 'Product triangles deals' is used when this tax is configured for triangles deal only with products.\n"
    #         "* The 'Service triangles deals' is used when this tax is configured for triangles deal only with services.\n")

    @api.onchange('type_tax_use')
    def onchange_type_tax_use(self):
        if self.children_tax_ids:
            for line in self.children_tax_ids:
                line.parent_type_tax_use = self.type_tax_use


class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'
    _order = 'code, name asc'

    code = fields.Char(string='Reference', index=True, track_visibility='onchange')
    display_name = fields.Char(compute='_compute_display_name')
    use_account_reports = fields.Boolean('Merge with account tags', help="If checked The amount in this tag is added to account tags amount.")

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for tag in self:
            name = tag.name
            if tag.code:
                name = '[%s] %s' % (tag.code, name)
            result.append((tag.id, name))
        return result

    @api.multi
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for tag in self:
            name = tag.name
            if tag.code:
                name = '[%s] %s' % (tag.code, name)
            tag.display_name = name
