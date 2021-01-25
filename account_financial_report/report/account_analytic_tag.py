# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountAnalyticTagReport(models.TransientModel):
    _name = "report_account_analytic_tag"
    _inherit = 'account_financial_report_abstract'

    name = fields.Char("Name")
    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_range_name = fields.Char("Date range name")
    date_from = fields.Date()
    date_to = fields.Date()
    based_on = fields.Selection([('analytictags', 'Account analytic Tags'),
                                 ('analyticaccount', 'Analytic Account'),
                                 ],
                                string='Based On',
                                required=True,
                                default='analytictags')
    group_by_period = fields.Selection([('ym', 'YEAR-MONTH'),
                                        ('yq', 'YEAR-QUARTER'),
                                        ('yqm', 'YEAR-QUARTER-MONTH')],
                                       string='Group By')
    analytic_tags_ids = fields.One2many(
        comodel_name='report_account_analytic_tag',
        inverse_name='report_id'
    )
    analytic_account_ids = fields.One2many(
        comodel_name='report_account_analytic_account',
        inverse_name='report_id'
    )


class AccountAnalyticTags(models.TransientModel):
    _name = 'report_account_analytic_tag'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_account_analytic_tag',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    account_analytic_tag_id = fields.Many2one(
        'account.analytic.tag',
        index=True
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        index=True
    )
    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used to keep link with real object
    #partner_id = fields.Many2one(
    #    'res.partner',
    #    index=True
    #)

    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    account_code = fields.Char()
    account_name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    balance = fields.Float(digits=(16, 2))


class AccountAnalyticAccount(models.TransientModel):
    _name = 'report_account_analytic_account'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_account_analytic_tag',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    account_analytic_tag_id = fields.Many2one(
        'account.analytic.tag',
        index=True
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        index=True
    )
    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used to keep link with real object
    #partner_id = fields.Many2one(
    #    'res.partner',
    #    index=True
    #)

    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    account_code = fields.Char()
    account_name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    balance = fields.Float(digits=(16, 2))


class AccountTagReportCompute(models.TransientModel):
    _inherit = 'report_account_tag_report'

    @api.multi
    def print_report(self, report_type='qweb-pdf', report_sub_type=False):
        self.ensure_one()
        context = dict(self.env.context)
        if report_type == 'xlsx':
            action = self._get_default_xlsx()
        elif report_type == 'fillpdf':
            action = self._get_default_fillpdf()
        elif report_type == 'csv':
            action = self._get_default_csv()
        elif report_type == 'xml':
            action = self._get_default_xml()
        else:
            action = self._get_default_qweb()
        if action:
            return action.with_context(context).report_action(self)
        else:
            return self._get_default_qweb().with_context(context).report_action(self)

    def _get_html(self):
        context = dict(self.env.context)
        rcontext = context.get('rcontext') and context['rcontext'] or {}
        report = self.browse(context.get('active_id'))
        result = {}
        #_logger.info("REPORT %s:%s" % (context, report))
        if report:
            rcontext['o'] = report
            if context.get('based_on') and context['based_on'] == 'vattaxtags':
                result['html'] = self.env.ref(
                    'account_financial_report.report_vat_report_vies_vies').render(
                        rcontext)
            elif context.get('based_on') and context['based_on'] == 'tax':
                result['html'] = self.env.ref(
                    'account_financial_report.report_vat_report_base_tax_tax').render(
                        rcontext)
            else:
                result['html'] = self.env.ref(
                    'account_financial_report.report_vat_report').render(
                        rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        if self._context.get('based_on') and not given_context.get('based_on'):
            given_context['based_on'] = self._context['based_on']
        #_logger.info("CONTEXT %s:%s" % (self._context, given_context))
        if given_context:
            return self.with_context(given_context)._get_html()
        else:
            return self._get_html()

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute report data
        if self.based_on == 'analytictags' or self._context.get('on_analytictags'):
            self._inject_analityctags_values()
            #if self.group_by_period in ['ym', 'yq', 'yqm']:
            #    self._inject_account_accounttags_values()
        elif self.based_on == 'analyticaccount' or self._context.get('on_analyticaccount'):
            self._inject_analitycaccounts_values()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

        def _inject_empty_analityctags_values(self):
            query_inject_analityctags = """
WITH
    accountanalytictags AS
        (SELECT tag.id AS tag_id,
                coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code,
                tag.name AS tag_name,
            FROM
                account_analytic_tag AS tag
            WHERE tag.id is not null AND tag.use_account_reports = TRUE
            ORDER BY code, tag.name
        )
INSERT INTO
    report_account_report_tag
    (
    report_id,
    create_uid,
    create_date,
    account_tag_id,
    code,
    name
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.tag_id,
    tag.code,
    tag.tag_name
FROM
    accountanalytictags tag
"""
            query_inject_analityctags_params = (self.company_id.id, self.id, self.env.uid)
            _logger.info("SQL %s" % (query_inject_analityctags % query_inject_analityctags_params))
            self.env.cr.execute(query_inject_analityctags, query_inject_analityctags_params)

    def _inject_analityctags_values(self, coef=1.0):
        """Inject report values for report_account_analytic_tag."""

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY tag.id, tag.code, tag.name, account.id, account.code, account.name, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY tag.id, tag.code, tag.name, account.id, account.code, account.name, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY tag.id, tag.code, tag.name, account.id, account.code, account.name, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY tag.id, tag.code, tag.name, account.id, account.code, account.name"
            save = ""
            include = ""

        query_inject_accounttags = """
WITH
    accountanalytictags AS
        (SELECT coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code, tag.name,
                account.code AS account_code, account.name AS account_name,
                tag.id AS tag_id, account.id AS account_id,
""" + periods_include + """
                coalesce(sum(moveline.tax_base_amount*moveline.tax_sign), 0.00) AS net,
                coalesce(sum(moveline.balance), 0.00) AS tax,
                coalesce(sum(moveline.debit), 0.00) AS debit,
                coalesce(sum(moveline.credit), 0.00) AS credit,
                coalesce(sum(moveline.tax_base*moveline.tax_sign), 0.00) AS base
            FROM
                account_analytic_tag AS tag
                INNER JOIN account_analytic_tag_account_move_line_rel AS analytictag
                    ON tag.id = analytictag.account_analytic_tag_id
                INNER JOIN account_move_line AS moveline
                    ON moveline.id = analytictag.account_move_line_id
                INNER JOIN account_move AS move
                    ON move.id = moveline.move_id
                INNER JOIN account_account AS account
                    ON account.id = moveline.account_id
            WHERE tag.id is not null AND tag.use_account_reports = TRUE
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + periods + """
            ORDER BY code, tag.name, account.code, account.name
        )
UPDATE
    report_account_report_tag
    SET (
        report_account_report_tag
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    account_code,
    account_name,
    account_tag_id,
    code,
    name,
""" + save + """
    net, tax, debit, credit, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.account_id,
    tag.account_code,
    tag.account_name,
    tag.tag_id,
    tag.code,
    tag.name,
""" + include + """
    abs(tag.net)*""" + "%f," % coef + """
    abs(tag.tax)*""" + "%f," % coef + """
    abs(tag.debit)*""" + "%f," % coef + """
    abs(tag.credit)*""" + "%f," % coef + """
    abs(tag.base)*""" + "%f" % coef + """
FROM
    accountanalytictags tag
"""

        query_inject_accounttags_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_accounttags % query_inject_accounttags_params))
        self.env.cr.execute(query_inject_accounttags, query_inject_accounttags_params)

    def _inject_analitycaccounts_values(self):
        """Inject report values for report_account_analytic_tag."""

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY analytic.id, analytic.code, analytic.name, account.id, account.code, account.name, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY analytic.id, analytic.code, analytic.name, account.id, account.code, account.name, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY analytic.id, analytic.code, analytic.name, account.id, account.code, account.name, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY analytic.id, analytic.code, analytic.name, account.id, account.code, account.name"
            save = ""
            include = ""

        query_inject_accounttags = """
WITH
    accountanalytic AS
        (SELECT analytic.code AS code, analytic.name,
                account.code AS account_code, account.name AS account_name,
                analytic.id AS analytic_id, account.id AS account_id,
""" + periods_include + """
                coalesce(sum(moveline.tax_base_amount*moveline.tax_sign), 0.00) AS net,
                coalesce(sum(moveline.balance), 0.00) AS tax,
                coalesce(sum(moveline.debit), 0.00) AS debit,
                coalesce(sum(moveline.credit), 0.00) AS credit,
                coalesce(sum(moveline.tax_base*moveline.tax_sign), 0.00) AS base
            FROM
                account_analytic_account AS analytic
                INNER JOIN account_move_line AS moveline
                    ON moveline.analytic_account_id = analytic.id
                INNER JOIN account_move AS move
                    ON move.id = moveline.move_id
                INNER JOIN account_account AS account
                    ON account.id = moveline.account_id
            WHERE tag.id is not null
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + periods + """
            ORDER BY analytic.code, analytic.name, account.code, account.name
        )
INSERT INTO
    report_account_analytic_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    account_code,
    account_name,
    analytic_account_id,
    code,
    name,
""" + save + """
    net, tax, debit, credit, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.account_id,
    tag.account_code,
    tag.account_name,
    tag.analytic_id,
    tag.code,
    tag.name,
""" + include + """
    abs(tag.net)*""" + "%f," % coef + """
    abs(tag.tax)*""" + "%f," % coef + """
    abs(tag.debit)*""" + "%f," % coef + """
    abs(tag.credit)*""" + "%f," % coef + """
    abs(tag.base)*""" + "%f" % coef + """
FROM
    accountanalytic tag
"""

        query_inject_accounttags_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_accounttags % query_inject_accounttags_params))
        self.env.cr.execute(query_inject_accounttags, query_inject_accounttags_params)
