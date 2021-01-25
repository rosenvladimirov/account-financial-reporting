# © 2018 Forest and Biomass Romania SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountGroup(models.Model):
    _inherit = 'account.group'

    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True, translate=True)
    complete_code_prefix = fields.Char('Complete Code Name', compute='_compute_complete_code_prefix', store=True)
    group_child_ids = fields.One2many(
        comodel_name='account.group',
        inverse_name='parent_id',
        string='Child Groups')
    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        store=True)
    account_ids = fields.One2many(
        comodel_name='account.account',
        inverse_name='group_id',
        string="Accounts")
    compute_account_ids = fields.Many2many(
        'account.account',
        compute='_compute_group_accounts',
        string="Accounts", store=True)
    display_on_report = fields.Boolean('Show on report')
    max_counter = fields.Integer("Number of digits")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('account.group'))
    properties_user_type_id = fields.Many2one('account.account.type', string='Type',
                                                help="Account Type is used for information purpose, "
                                                     "to generate country-specific legal reports, "
                                                     "and set the rules to close a fiscal year "
                                                     "and generate opening entries.")
    properties_reconcile = fields.Boolean(string='Allow Reconciliation', default=False,
                                            help="Check this box if this account allows invoices & "
                                                 "payments matching of journal items.")

    @api.multi
    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for group in self:
            if not group.parent_id:
                group.level = 0
            else:
                group.level = group.parent_id.level + 1

    @api.multi
    @api.depends('code_prefix', 'account_ids', 'account_ids.code',
                 'group_child_ids', 'group_child_ids.account_ids.code')
    def _compute_group_accounts(self):
        account_obj = self.env['account.account']
        accounts = account_obj.search([])
        for group in self:
            prefix = group.code_prefix if group.code_prefix else group.name
            gr_acc = accounts.filtered(
                lambda a: a.code.startswith(prefix)).ids
            group.compute_account_ids = [(6, 0, gr_acc)]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        lang = self.env.user.lang or 'en'
        if lang != 'en':
            for group in self.with_context(lang='en'):
                if group.parent_id:
                    group.complete_name = '%s / %s' % (
                    group.parent_id.complete_name, group.name and group.name.strip() or '')
                else:
                    group.complete_name = group.name and group.name.strip() or False
        for group in self.with_context(lang=lang):
            if group.parent_id:
                group.complete_name = '%s / %s' % (group.parent_id.complete_name, group.name and group.name.strip() or '')
            else:
                group.complete_name = group.name and group.name.strip() or False

    @api.depends('name', 'parent_id.complete_code_prefix')
    def _compute_complete_code_prefix(self):
        for group in self:
            if group.parent_id and group.parent_id.complete_code_prefix:
                group.complete_code_prefix = '%s-%s' % (group.parent_id.complete_code_prefix and group.parent_id.complete_code_prefix or '', group.code_prefix and group.code_prefix.strip() or '')
            else:
                group.complete_code_prefix = group.code_prefix and group.code_prefix.strip() or ''

    @api.onchange('properties_user_type_id')
    def _onchange_properties_user_type_id(self):
        if self.properties_user_type_id:
            accounts = self.env['account.account'].search([('group_id', '=', self.id), ('user_type_id', '=', False)])
            if accounts:
                accounts.write({'user_type_id': self.properties_user_type_id.id})

    @api.onchange('properties_reconcile')
    def _onchage_properties_reconcile(self):
        if self.properties_reconcile:
            accounts = self.env['account.account'].search([('group_id', '=', self.id), ('user_type_id', '=', False)])
            if accounts:
                accounts.write({'reconcile': self.properties_reconcile})
