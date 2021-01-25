# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import ValidationError


class TAGReportWizard(models.TransientModel):
    _name = "account.tag.report.wizard"

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        required=False,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_range_name = fields.Char("Date range name")
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    fy_start_date = fields.Date(compute='_compute_fy_start_date')
    based_on = fields.Selection([('accounttags', 'Account Tags'),
                                 ('accountgroups', 'Account Groups')],
                                string='Based On',
                                required=True,
                                default='accounttags')
    group_by_period = fields.Selection([('ym', 'Year-Month'),
                                        ('yq', 'Year-Quarter'),
                                        ('yqm', 'Year-Quarter-Mount')],
                                       string='Group By')
    account_detail = fields.Boolean("Detail by account")
    show_movement = fields.Boolean("Show debit and credit")
    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', ondelete='restrict', domain="[('parent_id', '=', False)]")

    @api.depends('date_from')
    def _compute_fy_start_date(self):
        for wiz in self.filtered('date_from'):
            date = fields.Datetime.from_string(wiz.date_from)
            res = self.company_id.compute_fiscalyear_dates(date)
            wiz.fy_start_date = res['date_from']

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id and self.date_range_id.company_id and \
                self.date_range_id.company_id != self.company_id:
            self.date_range_id = False
        res = {'domain': {'date_range_id': [],
                          }
               }
        if not self.company_id:
            return res
        else:
            res['domain']['date_range_id'] += [
                '|', ('company_id', '=', self.company_id.id),
                ('company_id', '=', False)]
        return res

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end
        self.date_range_name = self.date_range_id.name

    @api.multi
    @api.constrains('company_id', 'date_range_id')
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if rec.company_id and rec.date_range_id.company_id and\
                    rec.company_id != rec.date_range_id.company_id:
                raise ValidationError(
                    _('The Company in the Vat Report Wizard and in '
                      'Date Range must be the same.'))

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref('account_financial_report.action_report_account_tag_report')
        curr_context = self._context
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if curr_context.get('add_context', False):
            context1.update(curr_context.get('add_context'))
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        context1.update({'based_on': self.based_on})
        model = self.env['report_account_tag']
        report = model.create(self._prepare_account_tag_report())
        report.compute_data_for_report()
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    #@api.multi
    #def button_export_fillpdf(self):
    #    self.ensure_one()
    #    report_type = 'fillpdf'
    #    return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_account_tag_report(self):
        self.ensure_one()
        return {
            'name': 'Account TAG Report for %s' % self.date_range_name,
            'company_id': self.company_id.id,
            'date_range_id': self.date_range_id.id,
            'date_range_name': self.date_range_name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'based_on': self.based_on,
            'group_by_period': self.group_by_period,
            'account_detail': self.account_detail,
            'show_movement': self.show_movement,
            'parent_id': self.parent_id.id,
            'fy_start_date': self.fy_start_date,
        }

    def _export(self, report_type):
        """Default export is PDF."""
        model = self.env['report_account_tag']
        report = model.create(self._prepare_account_tag_report())
        report.compute_data_for_report()
        return report.print_report(report_type)
