# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountTagReport(models.TransientModel):
    _name = "report_account_tag"
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
    fy_start_date = fields.Date()

    account_detail = fields.Boolean()
    show_movement = fields.Boolean()
    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', ondelete='restrict', domain="[('parent_id', '=', False)]")
    based_on = fields.Selection([('accounttags', 'Account Tags'),
                                 ('accountgroups', 'Account Groups'),
                                 ],
                                string='Based On',
                                required=True,
                                default='accounttags')
    group_by_period = fields.Selection([('ym', 'YEAR-MONTH'),
                                        ('yq', 'YEAR-QUARTER'),
                                        ('yqm', 'YEAR-QUARTER-MONTH')],
                                       string='Group By')
    pdf_field_balance = fields.Char()
    account_tags_ids = fields.One2many(
        comodel_name='report_account_report_tag',
        inverse_name='report_id'
    )
    account_group_ids = fields.One2many(
        comodel_name='report_account_report_tag_groups',
        inverse_name='report_id'
    )


class AccountReportTags(models.TransientModel):
    _name = 'report_account_report_tag'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_account_tag',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    account_tag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    account_group_id = fields.Many2one(
        'account.group',
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
    base = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    balance = fields.Float(digits=(16, 2))
    initial_debit = fields.Float(digits=(16, 2))
    initial_credit = fields.Float(digits=(16, 2))
    initial_balance = fields.Float(digits=(16, 2))


class AccountReportTagGroups(models.TransientModel):
    _name = 'report_account_report_tag_groups'
    _inherit = 'account_financial_report_abstract'
    _order = 'name ASC'

    #report_tax_id = fields.Many2one(
    #    comodel_name='report_vat_report_taxtag',
    #    ondelete='cascade',
    #    index=True
    #)
    #report_account_id = fields.Many2one(
    #    comodel_name='report_vat_report_account_taxtag',
    #    ondelete='cascade',
    #    index=True
    #)
    report_id = fields.Many2one(
        comodel_name='report_account_tag',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    account_tag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    account_group_id = fields.Many2one(
        'account.group',
        index=True
    )

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
    base = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    balance = fields.Float(digits=(16, 2))
    initial_debit = fields.Float(digits=(16, 2))
    initial_credit = fields.Float(digits=(16, 2))
    initial_balance = fields.Float(digits=(16, 2))


class AccountTagReportCompute(models.TransientModel):
    _inherit = 'report_account_tag'

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

    def _get_default_qweb(self):
        report_name = 'account_financial_report.report_account_tag_report_qweb'
        report_type = 'qweb'
        return self.env['ir.actions.report'].search(
                [('report_name', '=', report_name),
                 ('report_type', '=', report_type)], limit=1)

    def _get_default_xlsx(self):
        report_name = 'a_f_r.report_account_tag_report_xlsx'
        report_type = 'xlsx'
        return self.env['ir.actions.report'].search(
                [('report_name', '=', report_name),
                 ('report_type', '=', report_type)], limit=1)

    def _get_html(self):
        context = dict(self.env.context)
        rcontext = context.get('rcontext') and context['rcontext'] or {}
        report = self.browse(context.get('active_id'))
        result = {}
        #_logger.info("REPORT %s:%s" % (context, report))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref('account_financial_report.report_account_tag_report').render(rcontext)
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
        if self.based_on == 'accounttags' or self._context.get('on_accounttags'):
            self._inject_empty_accounttags_values()
            self._inject_initial_accounttags_values()
            self._inject_accounttags_values()
            self._inject_account_accounttags_values()
        elif self.based_on == 'accountgroups' or self._context.get('on_accountgroups'):
            self._inject_accountgroups_values()
            #self._inject_account_accountgroups_values()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

    def _inject_empty_accounttags_values(self):
        query_inject_accounttags = """
WITH
    accounttags AS
        (SELECT tag.id AS tag_id,
                coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code,
                tag.name AS tag_name,
                account.id AS account_id,
                account.code AS account_code,
                account.name AS account_name
            FROM
                account_account_tag AS tag
            INNER JOIN account_account_account_tag AS accounttag
                ON tag.id = accounttag.account_account_tag_id
            INNER JOIN account_account AS account
                ON account.id = accounttag.account_account_id
            WHERE tag.id is not null
            ORDER BY code, tag.name, account.code, account.name
        )
INSERT INTO
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
    name
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
    tag.tag_name
FROM
    accounttags tag
"""
        query_inject_accounttags_params = (self.company_id.id, self.id, self.env.uid)
        # _logger.info("SQL %s" % (query_inject_accounttags % query_inject_accounttags_params))
        self.env.cr.execute(query_inject_accounttags, query_inject_accounttags_params)

    def _inject_initial_accounttags_values(self, parent_id=False, coef=1.0):
        query_inject_accounttags = """
WITH
    accounttags AS
        (SELECT tag.id AS tag_id,
                coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code,
                tag.name AS tag_name,
                account.id AS account_id,
                account.code AS account_code,
                account.name AS account_name,
                coalesce(sum(moveline.balance), 0.00) AS balance,
                coalesce(sum(moveline.debit), 0.00) AS debit,
                coalesce(sum(moveline.credit), 0.00) AS credit,
            FROM
                account_account_tag AS tag
                INNER JOIN account_account_account_tag AS accounttag
                    ON tag.id = accounttag.account_account_tag_id
                INNER JOIN account_account AS account
                    ON account.id = accounttag.account_account_id
                INNER JOIN account_move_line AS moveline
                    ON moveline.account_id = account.id
                INNER JOIN account_move AS move
                    ON move.id = moveline.move_id
            WHERE tag.id is not null
                AND move.company_id = %s
                AND move.date < %s
                AND move.state = 'posted'
            GROUP BY tag.id, tag.code, tag.name, account.id, account.code, account.name
            ORDER BY code, tag.name, account.code, account.name
        )
UPDATE
    report_account_report_tag
    SET (
    report_id,
    create_uid,
    create_date,
    account_id,
    account_code,
    account_name,
    account_tag_id,
    code,
    name,
    initial_balance, initial_debit, initial_credit
    ) = (
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.account_id,
    tag.account_code,
    tag.account_name,
    tag.tag_id,
    tag.code,
    tag.tag_name,
    abs(tag.balance)*""" + "%f," % coef + """
    abs(tag.debit)*""" + "%f," % coef + """
    abs(tag.credit)*""" + "%f," % coef + """
    )
FROM
    accounttags tag
WHERE
    report_account_report_tag.report_id = %s AND report_account_report_tag.account_id = tag.account_id AND report_account_report_tag.account_tag_id = tag.tag_id
"""

        query_inject_accounttags_params = (self.company_id.id, self.fy_start_date, self.id, self.env.uid, self.id)
        _logger.info("SQL %s" % (query_inject_accounttags % query_inject_accounttags_params))
        self.env.cr.execute(query_inject_accounttags, query_inject_accounttags_params)

    def _inject_accounttags_values(self, parent_id=False, coef=1.0):
        """Inject report values for report_account_report_tag."""
        if not parent_id:
            parent = self.parent_id and "AND tag.parent_id = %d " % self.parent_id.id or ""
        else:
            parent = parent_id and "AND tag.parent_id = %d " % parent_id.id or ""

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
    accounttags AS
        (SELECT tag.id AS tag_id, coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code, tag.name AS tag_name,
                account.id AS account_id, account.code AS account_code, account.name AS account_name,
""" + periods_include + """
                coalesce(sum(moveline.tax_base_amount*moveline.tax_sign), 0.00) AS net,
                coalesce(sum(moveline.balance), 0.00) AS balance,
                coalesce(sum(moveline.debit), 0.00) AS debit,
                coalesce(sum(moveline.credit), 0.00) AS credit,
                coalesce(sum(moveline.tax_base*moveline.tax_sign), 0.00) AS base
            FROM
                account_account_tag AS tag
                INNER JOIN account_account_account_tag AS accounttag
                    ON tag.id = accounttag.account_account_tag_id
                INNER JOIN account_account AS account
                    ON account.id = accounttag.account_account_id
                INNER JOIN account_move_line AS moveline
                    ON moveline.account_id = account.id
                INNER JOIN account_move AS move
                    ON move.id = moveline.move_id
            WHERE tag.id is not null
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + parent + periods + """
            ORDER BY code, tag.name, account.code, account.name
        )
UPDATE
    report_account_report_tag
    SET
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
    net, balance, debit, credit, base
    ) = (
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.account_id,
    tag.account_code,
    tag.account_name,
    tag.tag_id,
    tag.code,
    tag.tag_name,
""" + include + """
    abs(tag.net)*""" + "%f," % coef + """
    abs(tag.balance)*""" + "%f," % coef + """
    abs(tag.debit)*""" + "%f," % coef + """
    abs(tag.credit)*""" + "%f," % coef + """
    abs(tag.base)*""" + "%f" % coef + """
    )
FROM
    accounttags tag
WHERE report_account_report_tag.report_id = %s AND report_account_report_tag.account_id = tag.account_id AND report_account_report_tag.account_tag_id = tag.tag_id
"""

        query_inject_accounttags_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_accounttags % query_inject_accounttags_params))
        self.env.cr.execute(query_inject_accounttags, query_inject_accounttags_params)

    def _inject_account_accounttags_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax_vat = """
WITH
    account_tags AS
        (
            SELECT
                ' ' AS tag_code, tag.name AS tag_name,
                tag.account_tag_id AS account_tag_id,
                coalesce(sum(tag.net), 0.00) AS net,
                coalesce(sum(tag.balance), 0.00) AS balance,
                coalesce(sum(tag.debit), 0.00) AS debit,
                coalesce(sum(tag.credit), 0.00) AS credit,
                coalesce(sum(tag.initial_balance), 0.00) AS initial_balance,
                coalesce(sum(tag.initial_debit), 0.00) AS initial_debit,
                coalesce(sum(tag.initial_credit), 0.00) AS initial_credit,
                coalesce(sum(tag.base), 0.00) AS base
            FROM
                report_account_report_tag AS tag
            WHERE tag.account_tag_id is not null AND tag.report_id = %s
            GROUP BY tag.account_tag_id, tag.name
            ORDER BY tag.name
        )
INSERT INTO
    report_account_report_tag_groups
    (
    account_tag_id,
    report_id,
    create_uid,
    create_date,
    name,
    net,
    balance,
    debit,
    credit,
    initial_balance,
    initial_debit,
    initial_credit,
    base
    )
SELECT
    tt.account_tag_id,
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.tag_name,
    abs(tt.net),
    abs(tt.balance),
    abs(tt.debit),
    abs(tt.credit),
    abs(tt.initial_balance),
    abs(tt.initial_debit),
    abs(tt.initial_credit),
    abs(tt.base)
FROM
    account_tags tt
        """
        query_inject_tax_params = (self.id, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_tax_vat % query_inject_tax_params))
        self.env.cr.execute(query_inject_tax_vat, query_inject_tax_params)

    def _inject_accountgroups_values(self):
        """Inject report values for report_vat_report_taxtags."""
        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY taxgroup.id, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY taxgroup.id, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY taxgroup.id, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY taxgroup.id"
            save = ""
            include = ""
        query_inject_accountgroups = """
WITH
    accountgroups AS
        (SELECT accountgroup.id, coalesce(accountgroup.code_prefix, '') AS code, accountgroup.name,
""" + periods_include + """
                coalesce(sum(moveline.tax_base_amount*moveline.tax_sign), 0.00) AS net,
                coalesce(sum(moveline.balance), 0.00) AS balance,
                coalesce(sum(moveline.tax_base*moveline.tax_sign), 0.00) AS base
            FROM
                account_group AS accountgroup
                INNER JOIN account_account AS account
                    ON account.group_id = accountgroup.id
                INNER JOIN account_move_line AS moveline
                    ON moveline.account_id = account.id
                INNER JOIN account_move AS move
                    ON move.id = moveline.move_id
            WHERE accountgroup.id is not null
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + periods + """
            ORDER BY code, accountgroup.name
        )
INSERT INTO
    report_account_report_tag
    (
    report_id,
    create_uid,
    create_date,
    account_group_id,
    code,
    name,
""" + save + """
    net, balance, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    groups.id,
    groups.code,
    groups.name,
""" + include + """
    abs(groups.net),
    abs(groups.balance),
    abs(groups.base)
FROM
    taxgroups groups
"""
        query_inject_accountgroups_params = (self.company_id.id, self.date_from,
                                         self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_accountgroups,
                            query_inject_accountgroups_params)
