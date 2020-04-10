# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class OpenItemsReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * OpenItemsReport
    ** OpenItemsReportAccount
    *** OpenItemsReportPartner
    **** OpenItemsReportMoveLine
    """

    _name = 'report_open_items'
    _inherit = 'account_financial_report_abstract'

    # Filters fields, used for data computation
    name = fields.Char('Name', default=lambda self: 'Open Items - %s-%s' % (
    self.company_id.name, self.company_id.currency_id.name))
    date_at = fields.Date()

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_range_name = fields.Char("Date range name")
    fy_date_from = fields.Date()
    date_from = fields.Date()
    date_to = fields.Date()

    only_posted_moves = fields.Boolean()
    hide_account_at_0 = fields.Boolean()
    show_all_ob = fields.Boolean()
    without_vat = fields.Boolean()
    foreign_currency = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')
    accounts_only = fields.Char('Type of report')

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_open_items_account',
        inverse_name='report_id'
    )
    # Data fields, used to browse report data
    total_ids = fields.One2many(
        comodel_name='report_open_items_total',
        inverse_name='report_id'
    )


class OpenItemsReportTotal(models.TransientModel):
    _name = 'report_open_items_total'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_open_items',
        ondelete='cascade',
        index=True
    )
    report_account_id = fields.Many2one(
        comodel_name='report_open_items_account',
        ondelete='cascade',
        index=True
    )

    company_id = fields.Many2one(comodel_name='res.company', related='report_id.company_id')
    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    currency_id = fields.Many2one('res.currency')
    final_amount_residual = fields.Float(digits=(16, 2))
    final_amount_total_due = fields.Float(digits=(16, 2))
    final_amount_residual_currency = fields.Float(digits=(16, 2))
    final_amount_total_due_currency = fields.Float(digits=(16, 2))


class OpenItemsReportAccount(models.TransientModel):
    _name = 'report_open_items_account'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_open_items',
        ondelete='cascade',
        index=True
    )

    company_id = fields.Many2one(comodel_name='res.company')

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    currency_id = fields.Many2one('res.currency')
    final_amount_residual = fields.Float(digits=(16, 2))
    final_amount_total_due = fields.Float(digits=(16, 2))
    final_amount_residual_currency = fields.Float(digits=(16, 2))
    final_amount_total_due_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_open_items_partner',
        inverse_name='report_account_id'
    )


class OpenItemsReportPartner(models.TransientModel):
    _name = 'report_open_items_partner'
    _inherit = 'account_financial_report_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_open_items_account',
        ondelete='cascade',
        index=True
    )

    # Company data fields, used to keep link with real object
    company_id = fields.Many2one(comodel_name='res.company')

    # Data fields, used to keep link with real object
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )

    # Data for initial balance
    partner_move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        compute="_compute_partner_move_line_ids"
    )
    opening_debit = fields.Float(string="Opening debit", compute='_compute_debit_credit',
                                 help="Opening debit value for this account.")
    opening_credit = fields.Float(string="Opening credit", compute='_compute_debit_credit',
                                  help="Opening credit value for this account.")
    opening_bal = fields.Float(string="Fiscal Year balance", compute='_compute_debit_credit',
                               help="Opening balance value for this account.")
    fy_debit = fields.Float(string="Fiscal Year debit", compute='_compute_debit_credit',
                            help="Movement debit value for this account.")
    fy_credit = fields.Float(string="Fiscal Year credit", compute='_compute_debit_credit',
                             help="Movement credit value for this account.")
    fy_bal = fields.Float(string="Fiscal Year balance", compute='_compute_debit_credit',
                          help="FY balance value for this account.")
    fy_credit_note = fields.Float(string="Fiscal Year Credit notes", compute='_compute_debit_credit',
                                  help="FY credit notes amount for this account.")
    fy_vat = fields.Float(string="Fiscal Year VAT", compute='_compute_debit_credit',
                          help="FY VAT amount for this account.")

    date_from = fields.Date("Begin FY")
    date_to = fields.Date()

    # Data fields, used for report display
    name = fields.Char()
    currency_id = fields.Many2one('res.currency')
    final_amount_residual = fields.Float(digits=(16, 2))
    final_amount_total_due = fields.Float(digits=(16, 2))
    final_amount_residual_currency = fields.Float(digits=(16, 2))
    final_amount_total_due_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_open_items_move_line',
        inverse_name='report_partner_id'
    )

    @api.depends('partner_id')
    def _compute_partner_move_line_ids(self):
        for record in self:
            partner_move_line_ids = record.env['account.move.line'].search([('partner_id', '=', record.partner_id.id)])
            if partner_move_line_ids:
                record.partner_move_line_ids = [(6, 0, [x.id for x in partner_move_line_ids])]

    @api.depends('company_id.account_opening_move_id', 'partner_move_line_ids')
    def _compute_debit_credit(self):
        for record in self:
            account_ids = [x.account_id.id for x in record.report_account_id]
            opening_debit = opening_credit = fy_debit = fy_credit = opening_balance = fy_balance = fy_credit_note = fy_vat_debit = fy_vat_credit = fy_vat_balance = 0.0
            account_ids = [x.account_id.id for x in record.report_account_id]
            if any(x.id for x in record.report_account_id if x.report_id.show_all_ob):
                lines = record.partner_move_line_ids.filtered(lambda r: r.account_id.id in account_ids)
            else:
                lines = record.partner_move_line_ids

            for line in lines.filtered(lambda r: r.move_id.state == 'posted'):
                if record.company_id.account_opening_move_id and line.move_id == record.company_id.account_opening_move_id:
                    if line.debit:
                        opening_debit += line.debit
                    elif line.credit:
                        opening_credit += line.credit
                    opening_balance += line.balance
                if line.account_id.id in account_ids and record.date_from <= line.date <= fields.Date.today():
                    if line.debit:
                        fy_debit += line.debit
                    elif line.credit:
                        fy_credit += line.credit
                    fy_balance += line.balance
            record.fy_debit = fy_debit
            record.fy_credit = fy_credit

            # second calculate credit notes
            for line in record.partner_move_line_ids.filtered(lambda r: r.move_id.state == 'posted' and r.invoice_id and r.tax_sign < 0):
                if line.debit:
                    fy_credit_note += line.debit
                elif line.credit:
                    fy_credit_note -= line.credit
            record.fy_credit_note = fy_credit_note

            # next calculate VAT
            if any(x.id for x in record.report_account_id if x.report_id.without_vat):
                for line in record.partner_move_line_ids.filtered(lambda r: r.move_id.state == 'posted' and r.tax_line_id):
                    if (record.report_account_id.account_id.user_type_id.type == 'receivable'
                        and line.move_id.journal_id.type == "sale") \
                            or (record.report_account_id.account_id.user_type_id.type == 'payable'
                                and line.move_id.journal_id.type == "purchase"):
                        if line.debit:
                            fy_vat_debit += line.debit
                        elif line.credit:
                            fy_vat_credit += line.credit
                        fy_vat_balance = line.balance

            if record.report_account_id.account_id.user_type_id.type == 'receivable':
                record.opening_bal = opening_debit
                record.fy_vat = fy_vat_credit
                record.fy_bal = record.fy_debit - record.fy_credit_note - record.fy_vat
            elif record.report_account_id.account_id.user_type_id.type == 'payable':
                record.opening_bal = opening_credit
                record.fy_vat = fy_vat_debit
                record.fy_bal = fy_credit - record.fy_credit_note - record.fy_vat
            else:
                record.opening_debit = opening_debit
                record.opening_credit = opening_credit
                record.opening_bal = opening_balance
                record.fy_vat = fy_vat_balance
                record.fy_bal = fy_balance - record.fy_credit_note - record.fy_vat

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_open_items_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_open_items_partner"."name"
        """


class OpenItemsReportMoveLine(models.TransientModel):
    _name = 'report_open_items_move_line'
    _inherit = 'account_financial_report_abstract'

    report_partner_id = fields.Many2one(
        comodel_name='report_open_items_partner',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    move_line_id = fields.Many2one('account.move.line')

    # Data fields, used for report display
    date = fields.Date()
    date_due = fields.Date()
    entry = fields.Char()
    journal = fields.Char()
    account = fields.Char()
    partner = fields.Char()
    label = fields.Char()
    amount_total_due = fields.Float(digits=(16, 2))
    amount_residual = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one('res.currency')
    amount_total_due_currency = fields.Float(digits=(16, 2))
    amount_residual_currency = fields.Float(digits=(16, 2))


class OpenItemsReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_open_items'

    @api.multi
    def print_report(self, report_type='qweb-pdf', report_sub_type=False):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_open_items_xlsx'
        else:
            report_name = 'account_financial_report.' \
                          'report_open_items_qweb'
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1).report_action(self)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report.report_open_items').render(
                rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        #_logger.info("DATES %s=>%s:%s:%s" % (self.fy_date_from, self.date_at, self.date_from, self.date_to))
        # Compute report data
        self._inject_account_values()
        self._inject_partner_values()
        self._inject_account_total_values()
        self._inject_line_values()
        self._inject_line_values(only_empty_partner_line=True)
        self._clean_partners_and_accounts()
        self._compute_partners_and_accounts_cumul()
        if self.hide_account_at_0:
            self._clean_partners_and_accounts(
                only_delete_account_balance_at_0=True
            )
        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    def _inject_account_values(self):
        """Inject report values for report_open_items_account."""
        if self.date_from and self.date_to:
            query_inject_account = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                a.user_type_id,
                c.id as currency_id
            FROM
                account_account a
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date >= %s AND ml.date <= %s
            LEFT JOIN
                res_currency c ON a.currency_id = c.id
            """
        else:
            query_inject_account = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                a.user_type_id,
                c.id as currency_id
            FROM
                account_account a
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
            LEFT JOIN
                res_currency c ON a.currency_id = c.id
            """
        if self.filter_partner_ids:
            query_inject_account += """
INNER JOIN
    res_partner p ON ml.partner_id = p.id
"""
        if self.only_posted_moves:
            query_inject_account += """
INNER JOIN
    account_move m ON ml.move_id = m.id AND m.state = 'posted'
"""
        query_inject_account += """
WHERE
    a.company_id = %s
AND a.reconcile IS true
"""
        if self.filter_account_ids:
            query_inject_account += """
AND
    a.id IN %s
"""
        if self.filter_partner_ids:
            query_inject_account += """
AND
    p.id IN %s
"""
        query_inject_account += """
GROUP BY
    a.id, c.id
)
INSERT INTO
    report_open_items_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    currency_id,
    code,
    name,
    company_id
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    a.id AS account_id,
    a.currency_id,
    a.code,
    a.name,
    %s AS company_id
FROM
    accounts a
        """
        if self.date_from and self.date_to:
            query_inject_account_params = (
                self.date_from,
                self.date_to,
                self.company_id.id,
            )
        else:
            query_inject_account_params = (
                self.date_at,
                self.company_id.id,
            )
        if self.filter_account_ids:
            query_inject_account_params += (
                tuple(self.filter_account_ids.ids),
            )
        if self.filter_partner_ids:
            query_inject_account_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_account_params += (
            self.id,
            self.env.uid,
            self.company_id.id,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)
        #_logger.info("SQL %s:%s:%s" % (query_inject_account, self.account_ids.mapped("id"), self.account_ids.mapped("account_id")))

    def _inject_account_total_values(self):
        """Inject report values for report_open_items_total."""
        query_inject_total = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                c.id as currency_id
            FROM
                report_open_items_account a
            LEFT JOIN
                res_currency c ON a.currency_id = c.id
            """
        query_inject_total += """
WHERE
    a.report_id = %s AND a.company_id = %s
"""
        if self.filter_account_ids:
            query_inject_total += """
AND
    a.account_id IN %s
"""
        query_inject_total += """
GROUP BY
    a.id, c.id
)
INSERT INTO
    report_open_items_total
    (
    report_id,
    create_uid,
    create_date,
    report_account_id,
    currency_id,
    code,
    name
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    a.id,
    a.currency_id,
    a.code,
    a.name
FROM
    accounts a
        """

        query_inject_account_params = (
            self.id,
            self.company_id.id,
        )
        if self.filter_account_ids:
            query_inject_account_params += (
                tuple(self.filter_account_ids.ids),
            )
        query_inject_account_params += (
            self.id,
            self.env.uid,
        )
        self.env.cr.execute(query_inject_total, query_inject_account_params)
        #_logger.info("SQL %s:%s" % (query_inject_total, self.total_ids.mapped("report_account_id")))

    def _inject_partner_values(self):
        """ Inject report values for report_open_items_partner. """
        # pylint: disable=sql-injection
        if self.date_from and self.date_to:
            query_inject_partner = """
WITH
    accounts_partners AS
        (
            SELECT
                ra.id AS report_account_id,
                a.id AS account_id,
                at.include_initial_balance AS include_initial_balance,
                p.id AS partner_id,
                COALESCE(
                    CASE
                        WHEN
                            NULLIF(p.name, '') IS NOT NULL
                            AND NULLIF(p.ref, '') IS NOT NULL
                        THEN p.name || ' (' || p.ref || ')'
                        ELSE p.name
                    END,
                    '""" + _('No partner allocated') + """'
    ) AS partner_name
FROM
    report_open_items_account ra
INNER JOIN
    account_account a ON ra.account_id = a.id
INNER JOIN
    account_account_type at ON a.user_type_id = at.id
INNER JOIN
    account_move_line ml ON a.id = ml.account_id AND ml.date >= %s AND ml.date <= %s
"""
        else:
            query_inject_partner = """
WITH
accounts_partners AS
(
    SELECT
        ra.id AS report_account_id,
        a.id AS account_id,
        at.include_initial_balance AS include_initial_balance,
        p.id AS partner_id,
        COALESCE(
            CASE
                WHEN
                    NULLIF(p.name, '') IS NOT NULL
                    AND NULLIF(p.ref, '') IS NOT NULL
                THEN p.name || ' (' || p.ref || ')'
                ELSE p.name
            END,
            '""" + _('No partner allocated') + """'
    ) AS partner_name
FROM
    report_open_items_account ra
INNER JOIN
    account_account a ON ra.account_id = a.id
INNER JOIN
    account_account_type at ON a.user_type_id = at.id
INNER JOIN
    account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
"""
        if self.only_posted_moves:
            query_inject_partner += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        query_inject_partner += """
            LEFT JOIN
                res_partner p ON ml.partner_id = p.id
            WHERE
                ra.report_id = %s
                        """
        if self.filter_partner_ids:
            query_inject_partner += """
            AND
                p.id IN %s
            """
        query_inject_partner += """
            GROUP BY
                ra.id,
                a.id,
                p.id,
                at.include_initial_balance
        )
INSERT INTO
    report_open_items_partner
    (
    report_account_id,
    date_from,
    date_to,
    company_id,
    create_uid,
    create_date,
    partner_id,
    name
    )
SELECT
    ap.report_account_id,
    %s AS date_from,
    %s AS date_to,
    %s AS company_id,
    %s AS create_uid,
    NOW() AS create_date,
    ap.partner_id,
    ap.partner_name
FROM
    accounts_partners ap
"""
        if self.date_from and self.date_to:
            query_inject_partner_params = (
                self.date_from,
                self.date_to,
                self.id,
                self.fy_date_from,
                self.date_to,
                self.company_id.id
            )
        else:
            query_inject_partner_params = (
                self.date_at,
                self.id,
                self.fy_date_from,
                self.date_at,
                self.company_id.id
            )
        if self.filter_partner_ids:
            query_inject_partner_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_partner_params += (
            self.env.uid,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def _get_line_sub_query_move_lines(self,
                                       only_empty_partner_line=False,
                                       positive_balance=True):
        """ Return subquery used to compute sum amounts on lines """
        sub_query = """
            SELECT
                ml.id,
                ml.balance,
                SUM(
                    CASE
                        WHEN ml_past.id IS NOT NULL
                        THEN pr.amount
                        ELSE NULL
                    END
                ) AS partial_amount,
                ml.amount_currency,
                SUM(
                    CASE
                        WHEN ml_past.id IS NOT NULL
                        THEN pr.amount_currency
                        ELSE NULL
                    END
                ) AS partial_amount_currency,
                ml.currency_id
            FROM
                report_open_items_partner rp
            INNER JOIN
                report_open_items_account ra
                    ON rp.report_account_id = ra.id
            INNER JOIN
                account_move_line ml
                    ON ra.account_id = ml.account_id
        """
        if not only_empty_partner_line:
            sub_query += """
                    AND rp.partner_id = ml.partner_id
            """
        elif only_empty_partner_line:
            sub_query += """
                    AND ml.partner_id IS NULL
            """
        if not positive_balance:
            if self.date_from and self.date_to:
                sub_query += """
LEFT JOIN
    account_partial_reconcile pr
        ON ml.balance < 0 AND pr.credit_move_id = ml.id
LEFT JOIN
    account_move_line ml_future
        ON ml.balance < 0 AND pr.debit_move_id = ml_future.id
        AND ml_future.date > %s
LEFT JOIN
    account_move_line ml_past
        ON ml.balance < 0 AND pr.debit_move_id = ml_past.id
        AND ml_past.date >= %s AND ml_past.date <= %s
"""
            else:
                sub_query += """
LEFT JOIN
    account_partial_reconcile pr
        ON ml.balance < 0 AND pr.credit_move_id = ml.id
LEFT JOIN
    account_move_line ml_future
        ON ml.balance < 0 AND pr.debit_move_id = ml_future.id
        AND ml_future.date > %s
LEFT JOIN
    account_move_line ml_past
        ON ml.balance < 0 AND pr.debit_move_id = ml_past.id
        AND ml_past.date <= %s
"""
        else:
            if self.date_from and self.date_to:
                sub_query += """
LEFT JOIN
    account_partial_reconcile pr
        ON ml.balance > 0 AND pr.debit_move_id = ml.id
LEFT JOIN
    account_move_line ml_future
        ON ml.balance > 0 AND pr.credit_move_id = ml_future.id
        AND ml_future.date > %s
LEFT JOIN
    account_move_line ml_past
        ON ml.balance > 0 AND pr.credit_move_id = ml_past.id
        AND ml_past.date >= %s
        AND ml_past.date <= %s
"""
            else:
                sub_query += """
LEFT JOIN
    account_partial_reconcile pr
        ON ml.balance > 0 AND pr.debit_move_id = ml.id
LEFT JOIN
    account_move_line ml_future
        ON ml.balance > 0 AND pr.credit_move_id = ml_future.id
        AND ml_future.date > %s
LEFT JOIN
    account_move_line ml_past
        ON ml.balance > 0 AND pr.credit_move_id = ml_past.id
        AND ml_past.date <= %s
"""
        sub_query += """
            WHERE
                ra.report_id = %s
            GROUP BY
                ml.id,
                ml.balance,
                ml.amount_currency
            HAVING
                (
                    ml.full_reconcile_id IS NULL
                    OR MAX(ml_future.id) IS NOT NULL
                )
        """
        return sub_query

    def _inject_line_values(self, only_empty_partner_line=False):
        """ Inject report values for report_open_items_move_line.

        The "only_empty_partner_line" value is used
        to compute data without partner.
        """
        query_inject_move_line = """
WITH
    move_lines_amount AS
        (
        """
        query_inject_move_line += self._get_line_sub_query_move_lines(
            only_empty_partner_line=only_empty_partner_line,
            positive_balance=True
        )
        query_inject_move_line += """
            UNION
        """
        query_inject_move_line += self._get_line_sub_query_move_lines(
            only_empty_partner_line=only_empty_partner_line,
            positive_balance=False
        )
        query_inject_move_line += """
        ),
    move_lines AS
        (
            SELECT
                id,
                CASE
                    WHEN SUM(partial_amount) > 0
                    THEN
                        CASE
                            WHEN balance > 0
                            THEN balance - SUM(partial_amount)
                            ELSE balance + SUM(partial_amount)
                        END
                    ELSE balance
                END AS amount_residual,
                CASE
                    WHEN SUM(partial_amount_currency) > 0
                    THEN
                        CASE
                            WHEN amount_currency > 0
                            THEN amount_currency - SUM(partial_amount_currency)
                            ELSE amount_currency + SUM(partial_amount_currency)
                        END
                    ELSE amount_currency
                END AS amount_residual_currency,
                currency_id
            FROM
                move_lines_amount
            GROUP BY
                id,
                balance,
                amount_currency,
                currency_id
        )
INSERT INTO
    report_open_items_move_line
    (
    report_partner_id,
    create_uid,
    create_date,
    move_line_id,
    date,
    date_due,
    entry,
    journal,
    account,
    partner,
    label,
    amount_total_due,
    amount_residual,
    currency_id,
    amount_total_due_currency,
    amount_residual_currency
    )
SELECT
    rp.id AS report_partner_id,
    %s AS create_uid,
    NOW() AS create_date,
    ml.id AS move_line_id,
    ml.date,
    ml.date_maturity,
    m.name AS entry,
    j.code AS journal,
    a.code AS account,
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
    CASE
        WHEN
            NULLIF(p.name, '') IS NOT NULL
            AND NULLIF(p.ref, '') IS NOT NULL
        THEN p.name || ' (' || p.ref || ')'
        ELSE p.name
    END AS partner,
            """
        elif only_empty_partner_line:
            query_inject_move_line += """
    '""" + _('No partner allocated') + """' AS partner,
            """
        query_inject_move_line += """
    CONCAT_WS(' - ', NULLIF(ml.ref, ''), NULLIF(ml.name, '')) AS label,
    ml.balance,
    ml2.amount_residual,
    c.id AS currency_id,
    ml.amount_currency,
    ml2.amount_residual_currency
FROM
    report_open_items_partner rp
INNER JOIN
    report_open_items_account ra ON rp.report_account_id = ra.id
INNER JOIN
    account_move_line ml ON ra.account_id = ml.account_id
INNER JOIN
    move_lines ml2
        ON ml.id = ml2.id
        AND ml2.amount_residual IS NOT NULL
        AND ml2.amount_residual != 0
INNER JOIN
    account_move m ON ml.move_id = m.id
INNER JOIN
    account_journal j ON ml.journal_id = j.id
INNER JOIN
    account_account a ON ml.account_id = a.id
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
INNER JOIN
    res_partner p
        ON ml.partner_id = p.id AND rp.partner_id = p.id
            """
        if self.date_from and self.date_to:
            query_inject_move_line += """
LEFT JOIN
    account_full_reconcile fr ON ml.full_reconcile_id = fr.id
LEFT JOIN
    res_currency c ON ml2.currency_id = c.id
WHERE
    ra.report_id = %s
AND
    ml.date >= %s
AND
    ml.date <= %s
"""
        else:
            query_inject_move_line += """
LEFT JOIN
    account_full_reconcile fr ON ml.full_reconcile_id = fr.id
LEFT JOIN
    res_currency c ON ml2.currency_id = c.id
WHERE
    ra.report_id = %s
AND
    ml.date <= %s
"""
        if self.only_posted_moves:
            query_inject_move_line += """
AND
    m.state = 'posted'
        """
        if only_empty_partner_line:
            query_inject_move_line += """
AND
    ml.partner_id IS NULL
AND
    rp.partner_id IS NULL
        """
        if not only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, p.name, ml.date, ml.id
            """
        elif only_empty_partner_line:
            query_inject_move_line += """
ORDER BY
    a.code, ml.date, ml.id
            """
        if self.date_from and self.date_to:
            self.env.cr.execute(
                query_inject_move_line,
                (self.date_to,
                 self.date_from,
                 self.date_to,
                 self.id,
                 self.date_to,
                 self.date_from,
                 self.date_to,
                 self.id,
                 self.env.uid,
                 self.id,
                 self.date_from,
                 self.date_to,)
            )
        else:
            self.env.cr.execute(
                query_inject_move_line,
                (self.date_at,
                 self.date_at,
                 self.id,
                 self.date_at,
                 self.date_at,
                 self.id,
                 self.env.uid,
                 self.id,
                 self.date_at,)
            )

    def _compute_partners_and_accounts_cumul(self):
        """ Compute cumulative amount for
        report_open_items_partner and report_open_items_account.
        """
        self._compute_partner_cumul()
        self._compute_account_cumul()
        self._compute_account_cumul_total()

    def _compute_partner_cumul(self):
        where_condition_partner_by_account = """
WHERE
    id IN
        (
            SELECT
                rp.id
            FROM
                report_open_items_account ra
            INNER JOIN
                report_open_items_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        )"""
        query_computer_partner_residual_cumul = """
UPDATE
    report_open_items_partner
SET
    final_amount_residual =
        (
            SELECT
                SUM(rml.amount_residual) AS final_amount_residual
            FROM
                report_open_items_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_partner.id
        )
""" + where_condition_partner_by_account
        params_compute_partners_residual_cumul = (self.id,)
        self.env.cr.execute(query_computer_partner_residual_cumul,
                            params_compute_partners_residual_cumul)

        query_compute_partners_due_cumul = """
UPDATE
    report_open_items_partner
SET
    final_amount_total_due =
        (
            SELECT
                SUM(rml.amount_total_due) AS final_amount_total_due
            FROM
                report_open_items_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_partner.id
        )
""" + where_condition_partner_by_account
        params_compute_partner_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_due_cumul,
                            params_compute_partner_due_cumul)

        # Manage currency in partner
        where_condition_partner_by_account_cur = """
WHERE
    id IN
        (
            SELECT
                rp.id
            FROM
                report_open_items_account ra
            INNER JOIN
                report_open_items_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s AND ra.currency_id IS NOT NULL
        )
        """
        query_compute_partners_cur_id_cumul = """
UPDATE
    report_open_items_partner
SET
    currency_id =
        (
            SELECT
                MAX(currency_id) as currency_id
            FROM
                report_open_items_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_id_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_id_cumul,
                            params_compute_partners_cur_id_cumul)

        query_compute_partners_cur_residual_cumul = """
UPDATE
    report_open_items_partner
SET
    final_amount_residual_currency =
        (
            SELECT
                SUM(rml.amount_residual_currency)
                    AS final_amount_residual_currency
            FROM
                report_open_items_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_residual_cumul,
                            params_compute_partners_cur_residual_cumul)

        query_compute_partners_cur_due_cumul = """
UPDATE
    report_open_items_partner
SET
    final_amount_total_due_currency =
        (
            SELECT
                SUM(rml.amount_total_due_currency)
                    AS  final_amount_total_due_currency
            FROM
                report_open_items_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_due_cumul,
                            params_compute_partners_cur_due_cumul)

    def _compute_account_cumul(self):
        query_compute_accounts_residual_cumul = """
UPDATE
    report_open_items_account
SET
    final_amount_residual =
        (
            SELECT
                SUM(rp.final_amount_residual) AS final_amount_residual
            FROM
                report_open_items_partner rp
            WHERE
                rp.report_account_id = report_open_items_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_residual_cumul,
                            params_compute_accounts_residual_cumul)
        #_logger.info("SQL final_amount_residual %s:%s:%s" % (query_compute_accounts_residual_cumul, self.account_ids.mapped("id"), self.account_ids.mapped("final_amount_residual")))

        query_compute_accounts_cur_residual_cumul = """
UPDATE
    report_open_items_account
SET
    final_amount_residual_currency =
        (
            SELECT
                SUM(rp.final_amount_residual_currency)
                    AS final_amount_residual_currency
            FROM
                report_open_items_partner rp
            WHERE
                rp.report_account_id = report_open_items_account.id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_cur_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_residual_cumul,
                            params_compute_accounts_cur_residual_cumul)
        #_logger.info("SQL final_amount_residual %s:%s:%s" % (query_compute_accounts_cur_residual_cumul, self.account_ids.mapped("id"), self.account_ids.mapped("final_amount_residual_currency")))

        query_compute_accounts_due_cumul = """
UPDATE
    report_open_items_account
SET
    final_amount_total_due =
        (
            SELECT
                SUM(rp.final_amount_total_due) AS final_amount_total_due
            FROM
                report_open_items_partner rp
            WHERE
                rp.report_account_id = report_open_items_account.id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_due_cumul,
                            params_compute_accounts_due_cumul)
        #_logger.info("SQL final_amount_residual %s:%s:%s" % (query_compute_accounts_due_cumul, self.account_ids.mapped("id"), self.account_ids.mapped("final_amount_total_due")))

        query_compute_accounts_cur_due_cumul = """
UPDATE
    report_open_items_account
SET
    final_amount_total_due_currency =
        (
            SELECT
                SUM(rp.final_amount_total_due_currency)
                    AS final_amount_total_due_currency
            FROM
                report_open_items_partner rp
            WHERE
                rp.report_account_id = report_open_items_account.id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_cur_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_due_cumul,
                            params_compute_accounts_cur_due_cumul)
        #_logger.info("SQL final_amount_residual %s:%s:%s" % (query_compute_accounts_cur_due_cumul, self.account_ids.mapped("id"), self.account_ids.mapped("final_amount_total_due_currency")))

    def _compute_account_cumul_total(self):
        query_compute_accounts_residual_cumul = """
UPDATE
    report_open_items_total
SET
    final_amount_residual =
        (
            SELECT
                SUM(ra.final_amount_residual) AS final_amount_residual
            FROM
                report_open_items_account ra
            WHERE ra.id = report_open_items_total.report_account_id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_residual_cumul,
                            params_compute_accounts_residual_cumul)
        #_logger.info("SQL final_amount_residual %s:%s:%s" % (query_compute_accounts_residual_cumul, self.total_ids.mapped("report_account_id"), self.total_ids.mapped("final_amount_residual")))

        query_compute_accounts_cur_residual_cumul = """
UPDATE
    report_open_items_total
SET
    final_amount_residual_currency =
        (
            SELECT
                SUM(ra.final_amount_residual_currency)
                    AS final_amount_residual_currency
            FROM
                report_open_items_account ra
            WHERE ra.id = report_open_items_total.report_account_id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_cur_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_residual_cumul,
                            params_compute_accounts_cur_residual_cumul)
        #_logger.info("SQL final_amount_residual_currency %s:%s" % (query_compute_accounts_cur_residual_cumul, self.total_ids.mapped("final_amount_residual_currency")))

        query_compute_accounts_due_cumul = """
UPDATE
    report_open_items_total
SET
    final_amount_total_due =
        (
            SELECT
                SUM(ra.final_amount_total_due) AS final_amount_total_due
            FROM
                report_open_items_account ra
            WHERE ra.id = report_open_items_total.report_account_id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_due_cumul,
                            params_compute_accounts_due_cumul)
        #_logger.info("SQL final_amount_total_due %s:%s" % (query_compute_accounts_due_cumul, self.total_ids.mapped("final_amount_total_due")))

        query_compute_accounts_cur_due_cumul = """
UPDATE
    report_open_items_total
SET
    final_amount_total_due_currency =
        (
            SELECT
                SUM(ra.final_amount_total_due_currency)
                    AS final_amount_total_due_currency
            FROM
                report_open_items_account ra
            WHERE ra.id = report_open_items_total.report_account_id
        )
WHERE
    report_id = %s
        """
        params_compute_accounts_cur_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_due_cumul,
                            params_compute_accounts_cur_due_cumul)
        #_logger.info("SQL final_amount_total_due %s:%s" % (query_compute_accounts_cur_due_cumul, self.total_ids.mapped("final_amount_total_due_currency")))

    def _clean_partners_and_accounts(self,
                                     only_delete_account_balance_at_0=False):
        """ Delete empty data for
        report_open_items_partner and report_open_items_account.

        The "only_delete_account_balance_at_0" value is used
        to delete also the data with cumulative amounts at 0.
        """
        query_clean_partners = """
DELETE FROM
    report_open_items_partner
WHERE
    id IN
        (
            SELECT
                DISTINCT rp.id
            FROM
                report_open_items_account ra
            INNER JOIN
                report_open_items_partner rp
                    ON ra.id = rp.report_account_id
            LEFT JOIN
                report_open_items_move_line rml
                    ON rp.id = rml.report_partner_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_partners += """
            AND rml.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_partners += """
            AND (
                rp.final_amount_residual IS NULL
                OR rp.final_amount_residual = 0
                )
            """
        query_clean_partners += """
        )
        """
        params_clean_partners = (self.id,)
        self.env.cr.execute(query_clean_partners, params_clean_partners)
        query_clean_accounts = """
DELETE FROM
    report_open_items_account
WHERE
    id IN
        (
            SELECT
                DISTINCT ra.id
            FROM
                report_open_items_account ra
            LEFT JOIN
                report_open_items_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND rp.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND (
                ra.final_amount_residual IS NULL
                OR ra.final_amount_residual = 0
                )
            """
        query_clean_accounts += """
        )
        """
        params_clean_accounts = (self.id,)
        self.env.cr.execute(query_clean_accounts, params_clean_accounts)

#        query_clean_totals = """
#DELETE FROM
#    report_open_items_total
#WHERE
#    id IN
#        (
#            SELECT
#                DISTINCT rt.id
#            FROM
#                report_open_items_total rt
#            WHERE
#                rt.report_id = %s
#        """
#        if only_delete_account_balance_at_0:
#            query_clean_totals += """
#            AND (
#                rt.final_amount_residual IS NULL
#                OR rt.final_amount_residual = 0
#                )
#            """
#        query_clean_totals += """
#        )
#        """
#        params_clean_totals = (self.id,)
#        self.env.cr.execute(query_clean_totals, params_clean_totals)
