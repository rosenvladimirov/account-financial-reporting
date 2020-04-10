# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class VATReport(models.TransientModel):
    _name = "report_vat_report"
    _inherit = 'account_financial_report_abstract'
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * VATReport
    ** VATReportTaxTags
    *** VATReportTax
    """

    # Filters fields, used for data computation
    name = fields.Char("Name")
    company_id = fields.Many2one(comodel_name='res.company')
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_range_name = fields.Char("Date range name")
    date_from = fields.Date()
    date_to = fields.Date()
    based_on = fields.Selection([('taxtags', 'Tax Tags'),
                                 ('taxgroups', 'Tax Groups'),
                                 ('tax', 'Tax positions'),
                                 ('vattaxtags', 'Tax Tags with VAT number grouping')],
                                string='Based On',
                                required=True,
                                default='taxtags')
    group_by_period = fields.Selection([('ym', 'YEAR-MONTH'),
                                        ('yq', 'YEAR-QUARTER'),
                                        ('yqm', 'YEAR-QUARTER-MONTH')],
                                       string='Group By')
    tax_detail = fields.Boolean('Tax Detail')
    pdf_detail = fields.Boolean('Without PDF-Views', default=True)
    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', ondelete='restrict', domain="[('parent_id', '=', False)]")
    # Separate
    receivable_vat_only = fields.Boolean()
    payable_vat_only = fields.Boolean()

    # Data fields, used to browse report detail data
    taxtags_ids = fields.One2many(
        comodel_name='report_vat_report_taxtag',
        inverse_name='report_id'
    )
    tax_ids = fields.One2many(
        comodel_name='report_vat_report_tax',
        inverse_name='report_id'
    )
    tax_group_ids = fields.One2many(
        comodel_name='report_vat_report_groups',
        inverse_name='report_id'
    )
    accounttags_ids = fields.One2many(
        comodel_name='report_vat_report_account_taxtag',
        inverse_name='report_id'
    )


class VATReportTaxTags(models.TransientModel):
    _name = 'report_vat_report_taxtag'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_vat_report',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    taxtag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    taxgroup_id = fields.Many2one(
        'account.tax.group',
        index=True
    )
    # Data fields, used to keep link with real object
    tax_id = fields.Many2one(
        'account.tax',
        index=True
    )
    # Data fields, used to keep link with real object
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )

    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    pdf_field_net = fields.Char()
    pdf_field_tax = fields.Char()
    xml_tag = fields.Char()
    csv_field = fields.Integer()
    type_taxes = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    base = fields.Float(digits=(16, 2))
    #vat = fields.Char(string='TIN', help="Tax Identification Number. "
    #                                     "Fill it if the company is subjected to taxes. "
    #                                     "Used by the some of the legal statements.")
    # Data fields, used to browse report detail data
    tax_ids = fields.One2many(
        comodel_name='report_vat_report_tax',
        inverse_name='report_tax_id'
    )


class VATReportTax(models.TransientModel):
    _name = 'report_vat_report_tax'
    _inherit = 'account_financial_report_abstract'
    _order = 'name ASC'

    report_tax_id = fields.Many2one(
        comodel_name='report_vat_report_taxtag',
        ondelete='cascade',
        index=True
    )
    report_id = fields.Many2one(
        comodel_name='report_vat_report',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    taxtag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    # Data fields, used to keep link with real object
    tax_id = fields.Many2one(
        'account.tax',
        index=True
    )

    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    type_tax_use = fields.Char()
    parent_type_tax_use = fields.Char()
    code = fields.Char()
    name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    base = fields.Float(digits=(16, 2))


class VATReportTaxGroups(models.TransientModel):
    _name = 'report_vat_report_groups'
    _inherit = 'account_financial_report_abstract'
    _order = 'name ASC'

    report_tax_id = fields.Many2one(
        comodel_name='report_vat_report_taxtag',
        ondelete='cascade',
        index=True
    )
    report_account_id = fields.Many2one(
        comodel_name='report_vat_report_account_taxtag',
        ondelete='cascade',
        index=True
    )
    report_id = fields.Many2one(
        comodel_name='report_vat_report',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    taxtag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    # Data fields, used to keep link with real object
    tax_id = fields.Many2one(
        'account.tax',
        index=True
    )
    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    type_tax_use = fields.Char()
    parent_type_tax_use = fields.Char()
    code = fields.Char()
    name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    base = fields.Float(digits=(16, 2))


class VATReportAccountTaxTags(models.TransientModel):
    _name = 'report_vat_report_account_taxtag'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_vat_report',
        ondelete='cascade',
        index=True
    )
    # Data fields, used to keep link with real object
    taxtag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    taxgroup_id = fields.Many2one(
        'account.tax.group',
        index=True
    )
    # Data fields, used to keep link with real object
    tax_id = fields.Many2one(
        'account.tax',
        index=True
    )
    account_id = fields.Many2one(
        'account.account',
        index=True
    )
    # Data fields, used to keep link with real object
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )

    # Periods groups
    year = fields.Float()
    month = fields.Float()
    quarter = fields.Float()

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    pdf_field_net = fields.Char()
    pdf_field_tax = fields.Char()
    xml_tag = fields.Char()
    csv_field = fields.Integer()
    type_taxes = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))
    debit = fields.Float(digits=(16, 2))
    credit = fields.Float(digits=(16, 2))
    base = fields.Float(digits=(16, 2))
    bal = fields.Float(digits=(16, 2))

    #vat = fields.Char(string='TIN', help="Tax Identification Number. "
    #                                     "Fill it if the company is subjected to taxes. "
    #                                     "Used by the some of the legal statements.")
    # Data fields, used to browse report detail data
    tax_ids = fields.One2many(
        comodel_name='report_vat_report_tax',
        inverse_name='report_tax_id'
    )


class VATReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """
    _inherit = 'report_vat_report'

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
        if self.based_on == 'taxtags' or self._context.get('on_taxtags'):
            self._inject_taxtags_values()
            self._inject_tax_taxtags_values()
            if self.group_by_period in ['ym', 'yq', 'yqm']:
                self._inject_tax_taxtags_vat_values()
        elif self.based_on == 'taxgroups' or self._context.get('on_taxgroups'):
            self._inject_taxgroups_values()
            self._inject_tax_taxgroups_values()
        elif self.based_on == 'vattaxtags' or self._context.get('on_vattaxtags'):
            self._inject_taxtags_vat_values()
            #self._inject_taxtags_values()
            self._inject_tax_taxtags_vat_values()
            self._inject_taxtags_account_values()
        elif self.based_on == 'tax' or self._context.get('on_tax'):
            self._inject_taxtags_tax_id_values()
            # self._inject_tax_taxtags_values()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

    def _inject_taxtags_values(self, parent_id=False, user_type_ids=False, tag_ids=False, coef=1.0):
        """Inject report values for report_vat_report_taxtags."""
        if not parent_id:
            parent = self.parent_id and "AND tag.parent_id = %d " % self.parent_id.id or ""
        else:
            parent = parent_id and "AND tag.parent_id = %d " % parent_id.id or ""

        if self.receivable_vat_only:
            other_filters = "AND tax.type_tax_use = 'sale' OR tax.parent_type_tax_use = 'sale' "
        elif self.payable_vat_only:
            other_filters = "AND tax.type_tax_use = 'purchase' OR tax.parent_type_tax_use = 'purchase' "
        else:
            other_filters = ""

        if tag_ids and other_filters:
            other_filters += " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )
        elif tag_ids and not other_filters:
            other_filters = " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )

        if user_type_ids and other_filters:
            other_filters += "AND acc.user_type_id in %s " % (tuple(user_type_ids),)
        elif user_type_ids and not other_filters:
            other_filters = "AND acc.user_type_id in %s " % (tuple(user_type_ids),)

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY tag.id, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY tag.id, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY tag.id, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY tag.id"
            save = ""
            include = ""

        query_inject_taxtags = """
WITH
    taxtags AS
        (SELECT coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code, tag.name,
                tag.pdf_field_net, tag.pdf_field_tax, tag.csv_field, tag.xml_tag, tag.type_taxes,
                tag.id,
""" + periods_include + """ 
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.debit), 0.00) AS debit,
                coalesce(sum(movetax.credit), 0.00) AS credit,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base
            FROM
                account_account_tag AS tag
                INNER JOIN account_tax_account_tag AS taxtag
                    ON tag.id = taxtag.account_account_tag_id
                INNER JOIN account_tax AS tax
                    ON tax.id = taxtag.account_tax_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
                INNER JOIN account_account AS acc
                    ON movetax.account_id = acc.id
            WHERE tag.id is not null AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + parent + other_filters + periods + """
            ORDER BY code, tag.name
        )
INSERT INTO
    report_vat_report_taxtag
    (
    report_id,
    create_uid,
    create_date,
    taxtag_id,
    code,
    name,
    pdf_field_net,
    pdf_field_tax,
    csv_field,
    xml_tag,
    type_taxes,
""" + save + """
    net, tax, debit, credit, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.id,
    tag.code,
    tag.name,
    tag.pdf_field_net,
    tag.pdf_field_tax,
    tag.csv_field,
    tag.xml_tag,
    tag.type_taxes,
""" + include + """
    abs(tag.net)*""" + "%f," % coef + """
    abs(tag.tax)*""" + "%f," % coef + """
    abs(tag.debit)*""" + "%f," % coef + """
    abs(tag.credit)*""" + "%f," % coef + """
    abs(tag.base)*""" + "%f" % coef + """
FROM
    taxtags tag
"""

        query_inject_taxtags_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_taxtags % query_inject_taxtags_params))
        self.env.cr.execute(query_inject_taxtags, query_inject_taxtags_params)

    def _inject_taxgroups_values(self):
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
        query_inject_taxgroups = """
WITH
    taxgroups AS
        (SELECT coalesce(taxgroup.sequence, 0) AS code, taxgroup.name,
                taxgroup.id,
""" + periods_include + """
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base
            FROM
                account_tax_group AS taxgroup
                INNER JOIN account_tax AS tax
                    ON tax.tax_group_id = taxgroup.id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE taxgroup.id is not null AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                    AND move.date <= %s AND move.state = 'posted'
""" + periods + """
            ORDER BY code, taxgroup.name
        )
INSERT INTO
    report_vat_report_taxtag
    (
    report_id,
    create_uid,
    create_date,
    taxgroup_id,
    code,
    name,
""" + save + """
    net, tax, base
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
    abs(groups.tax),
    abs(groups.base)
FROM
    taxgroups groups
"""
        query_inject_taxgroups_params = (self.company_id.id, self.date_from,
                                         self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_taxgroups,
                            query_inject_taxgroups_params)

    def _inject_taxtags_tax_id_values(self):
        """Inject report values for report_vat_report_taxtags_vat."""
        if self.receivable_vat_only:
            other_filters = "AND tax.type_tax_use = 'sale' OR tax.parent_type_tax_use = 'sale' "
        elif self.payable_vat_only:
            other_filters = "AND tax.type_tax_use = 'purchase' OR tax.parent_type_tax_use = 'purchase' "
        else:
            other_filters = ""

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY tax.type_tax_use, tax.id, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY tax.type_tax_use, tax.id, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY tax.type_tax_use, tax.id, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY tax.type_tax_use, tax.id"
            save = ""
            include = ""

        query_inject_taxtags_vat = """
WITH
    taxtags AS
        (SELECT tax.name, tax.id AS tax_id, tax.type_tax_use,
""" + periods_include + """
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.debit), 0.00) AS debit,
                coalesce(sum(movetax.credit), 0.00) AS credit,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base
            FROM
                account_tax AS tax
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE movetax.tax_line_id is not null AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + other_filters + periods + """
            ORDER BY name
        )
INSERT INTO
    report_vat_report_tax
    (
    report_id,
    create_uid,
    create_date,
    tax_id,
    name,
    type_tax_use,
""" + save + """
    net, tax, debit, credit, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tax_id,
    tax.name,
    tax.type_tax_use,
""" + include + """
    CASE WHEN tax.type_tax_use == 'none' THEN tax.net ELSE abs(tax.net) END,
    CASE WHEN tax.type_tax_use == 'none' THEN tax.tax ELSE abs(tax.tax) END,
    CASE WHEN tax.type_tax_use == 'none' THEN tax.debit ELSE abs(tax.debit) END,
    CASE WHEN tax.type_tax_use == 'none' THEN tax.credit ELSE abs(tax.credit) END,
    CASE WHEN tax.type_tax_use == 'none' THEN tax.base ELSE abs(tax.base) END
FROM
    taxtags tax
"""
        query_inject_taxtags_vat_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_taxtags_vat % query_inject_taxtags_vat_params))
        self.env.cr.execute(query_inject_taxtags_vat, query_inject_taxtags_vat_params)

    def _inject_taxtags_vat_values(self, parent_ids=False,  tag_ids=False):
        """Inject report values for report_vat_report_taxtags_vat."""
        if parent_ids:
            parent_tuple = tuple([x.id for x in parent_ids])
            parent = self.parent_id and "AND tag.parent_id in %s " % (parent_tuple,) or ""
        else:
            parent = self.parent_id and "AND tag.parent_id = %d " % self.parent_id.id or ""
        if self.receivable_vat_only:
            other_filters = "AND tax.type_tax_use = 'sale' "
        elif self.payable_vat_only:
            other_filters = "AND tax.type_tax_use = 'purchase' "
        else:
            other_filters = ""

        if tag_ids and other_filters:
            other_filters += " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )
        elif tag_ids and not other_filters:
            other_filters = " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY tag.id, movetax.partner_id, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY tag.id, movetax.partner_id, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY tag.id, movetax.partner_id, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY tag.id, movetax.partner_id"
            save = ""
            include = ""
        query_inject_taxtags_vat = """
WITH
    taxtags AS
        (SELECT coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') AS code, tag.name,
                tag.xml_tag, tag.type_taxes,
                tag.id, movetax.partner_id,
""" + periods_include + """
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.debit), 0.00) AS debit,
                coalesce(sum(movetax.credit), 0.00) AS credit,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base
            FROM
                account_account_tag AS tag
                INNER JOIN account_tax_account_tag AS taxtag
                    ON tag.id = taxtag.account_account_tag_id
                INNER JOIN account_tax AS tax
                    ON tax.id = taxtag.account_tax_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE tag.id is not null
                AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                AND move.date <= %s AND move.state = 'posted'
""" + parent + other_filters + periods + """
            ORDER BY code, movetax.partner_id
        )
INSERT INTO
    report_vat_report_taxtag
    (
    report_id,
    create_uid,
    create_date,
    taxtag_id,
    code,
    name,
    xml_tag,
    partner_id,
""" + save + """
    net, tax, debit, credit, base
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.id,
    tag.code,
    tag.name,
    tag.xml_tag,
    tag.partner_id,
""" + include + """
    abs(tag.net),
    abs(tag.tax),
    abs(tag.debit),
    abs(tag.credit),
    abs(tag.base)
FROM
    taxtags tag
WHERE
    tag.partner_id is not null
"""
        query_inject_taxtags_vat_params = (self.company_id.id, self.date_from,
                                           self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_taxtags_vat, query_inject_taxtags_vat_params)
        # _logger.info("SQL %s" % (query_inject_taxtags % query_inject_taxtags_params))

    def _inject_tax_taxtags_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax = """
WITH
    taxtags_tax AS
        (
            SELECT
                ' ' AS code, tax.name, tag.id AS report_tax_id,
                tax.id,
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base
            FROM
                report_vat_report_taxtag AS tag
                INNER JOIN account_tax_account_tag AS taxtag
                    ON tag.taxtag_id = taxtag.account_account_tag_id
                INNER JOIN account_tax AS tax
                    ON tax.id = taxtag.account_tax_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE tag.id is not null AND movetax.tax_exigible
                AND tag.report_id = %s AND move.company_id = %s
                AND move.date >= %s AND move.date <= %s
                AND move.state = 'posted'
            GROUP BY tag.id, tax.id
            ORDER BY tax.name
        )
INSERT INTO
    report_vat_report_tax
    (
    report_tax_id,
    report_id,
    create_uid,
    create_date,
    tax_id,
    name,
    net,
    tax,
    base
    )
SELECT
    tt.report_tax_id,
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.id,
    tt.name,
    abs(tt.net),
    abs(tt.tax),
    abs(tt.base)
FROM
    taxtags_tax tt
        """
        query_inject_tax_params = (self.id, self.company_id.id, self.date_from,
                                   self.date_to, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_tax % query_inject_tax_params))
        self.env.cr.execute(query_inject_tax, query_inject_tax_params)

    def _inject_tax_taxtags_vat_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax_vat = """
WITH
    taxtags_tax AS
        (
            SELECT
                ' ' AS code, tag.name,
                tag.taxtag_id AS taxtag_id,
                coalesce(sum(tag.net), 0.00) AS net,
                coalesce(sum(tag.tax), 0.00) AS tax,
                coalesce(sum(tag.base), 0.00) AS base
            FROM
                report_vat_report_taxtag AS tag
            WHERE tag.id is not null AND tag.report_id = %s
            GROUP BY tag.taxtag_id, tag.name
            ORDER BY tag.name
        )
INSERT INTO
    report_vat_report_groups
    (
    taxtag_id,
    report_id,
    create_uid,
    create_date,
    name,
    net,
    tax,
    base
    )
SELECT
    tt.taxtag_id,
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.name,
    abs(tt.net),
    abs(tt.tax),
    abs(tt.base)
FROM
    taxtags_tax tt
        """
        query_inject_tax_params = (self.id, self.id, self.env.uid)
        _logger.info("SQL %s" % (query_inject_tax_vat % query_inject_tax_params))
        self.env.cr.execute(query_inject_tax_vat, query_inject_tax_params)

    def _inject_tax_taxgroups_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax = """
WITH
    taxtags_tax AS
        (
            SELECT
                ' ' AS code, tax.name,
                taxtag.id AS report_tax_id, tax.id,
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax
            FROM
                report_vat_report_taxtag AS taxtag
                INNER JOIN account_tax AS tax
                    ON tax.tax_group_id = taxtag.taxgroup_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE taxtag.id is not null AND movetax.tax_exigible
                AND taxtag.report_id = %s AND move.company_id = %s
                AND move.date >= %s AND move.date <= %s
                AND move.state = 'posted'
            GROUP BY taxtag.id, tax.id
            ORDER BY tax.name
        )
INSERT INTO
    report_vat_report_tax
    (
    report_tax_id,
    report_id,
    create_uid,
    create_date,
    tax_id,
    name,
    net,
    tax
    )
SELECT
    tt.report_tax_id,
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.id,
    tt.name,
    abs(tt.net),
    abs(tt.tax)
FROM
    taxtags_tax tt
        """
        query_inject_tax_params = (self.id, self.company_id.id, self.date_from,
                                   self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_tax, query_inject_tax_params)

    def _inject_taxtags_account_values(self, user_type_ids=False, contra_user_type_ids=False, parent_id=False, tag_ids=False, coef=1.0):
        """Inject report values for report_vat_report_account_taxtag."""
        if not parent_id:
            parent = self.parent_id and "AND tag.parent_id = %d" % self.parent_id.id or ""
        else:
            parent = parent_id and "AND tag.parent_id = %d" % parent_id.id or ""
        base_filters = "WHERE"
        if not user_type_ids:
            user_type_id = self.env.ref('account.data_account_type_revenue')
            user_type_ids = [user_type_id.id]
        if user_type_ids and len(user_type_ids) == 1:
            base_filters = "WHERE acc.user_type_id = %s AND" % user_type_ids[0]
        elif user_type_ids and len(user_type_ids) > 1:
            base_filters = "WHERE acc.user_type_id in %s AND" % (tuple(user_type_ids), )
        if self.receivable_vat_only:
            other_filters = " AND tax.type_tax_use = 'sale' "
        elif self.payable_vat_only:
            other_filters = " AND tax.type_tax_use = 'purchase' "
        else:
            other_filters = ""
        if tag_ids and other_filters:
            other_filters += " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )
        elif tag_ids and not other_filters:
            other_filters = " AND coalesce(regexp_replace(tag.code, '[^0-9\\.]+', '', 'g'), ' ') IN %s " % (tuple(tag_ids), )

        if contra_user_type_ids and len(contra_user_type_ids) == 1 and other_filters:
            other_filters += " AND acct.user_type_id = %s" % contra_user_type_ids[0]
        elif contra_user_type_ids and len(contra_user_type_ids) > 1 and other_filters:
            other_filters += " AND acct.user_type_id IN %s" % (tuple(contra_user_type_ids), )
        elif contra_user_type_ids and len(contra_user_type_ids) == 1 and not other_filters:
            other_filters = " AND acct.user_type_id = %s" % contra_user_type_ids[0]
        elif contra_user_type_ids and len(contra_user_type_ids) > 1 and not other_filters:
            other_filters = " AND acct.user_type_id IN %s" % (tuple(contra_user_type_ids),)

        if self.group_by_period == "ym":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods =  "GROUP BY movetax.account_id, year, month"
            save = "year, month,"
            include = "year, month,"
        elif self.group_by_period == "yq":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter,"
            periods = "GROUP BY movetax.account_id, year, quarter"
            save = "year, quarter,"
            include = "year, quarter,"
        elif self.group_by_period == "yqm":
            periods_include = "EXTRACT(YEAR FROM move.date::timestamp) AS year, EXTRACT(QUARTER FROM move.date::timestamp) AS quarter, EXTRACT(MONTH FROM move.date::timestamp) AS month,"
            periods = "GROUP BY movetax.account_id, year, quarter, month"
            save = "year, month, quarter,"
            include = "year, month, quarter,"
        else:
            periods_include = ""
            periods = "GROUP BY movetax.account_id"
            save = ""
            include = ""
        query_inject_taxtags_vat = """
WITH
    taxtags AS
        (SELECT movetax.account_id, 
""" + periods_include + """
                coalesce(sum(movetax.tax_base_amount*movetax.tax_sign), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax,
                coalesce(sum(movetax.debit), 0.00) AS debit,
                coalesce(sum(movetax.credit), 0.00) AS credit,
                coalesce(sum(movetax.tax_base*movetax.tax_sign), 0.00) AS base,
                coalesce(sum(movetax.debit-movetax.credit), 0.00) AS bal
            FROM account_move_line AS movetax
                    INNER JOIN account_move AS move
                        ON move.id = movetax.move_id
                    INNER JOIN account_account AS acc
                        ON movetax.account_id = acc.id
                    """ + base_filters  + """ movetax.move_id IN
                    (SELECT movetaxf.move_id
                        FROM
                            account_account_tag AS tag
                            INNER JOIN account_tax_account_tag AS taxtag
                                ON tag.id = taxtag.account_account_tag_id
                            INNER JOIN account_tax AS tax
                                ON tax.id = taxtag.account_tax_id
                            INNER JOIN account_move_line AS movetaxf
                                ON movetaxf.tax_line_id = tax.id
                            INNER JOIN account_move AS movef
                                ON movef.id = movetaxf.move_id
                            INNER JOIN account_account AS acct
                                ON movetaxf.account_id = acct.id
                        WHERE tag.id is not null
                            AND movetaxf.tax_exigible
                            AND movef.company_id = %s AND movef.date >= %s
                            AND movef.date <= %s AND movef.state = 'posted'
                            """ + parent + other_filters + """)
            """ + periods + """
            ORDER BY movetax.account_id)
INSERT INTO
    report_vat_report_account_taxtag
    (
    report_id,
    create_uid,
    create_date,
    account_id,
""" + save + """
    net, tax, debit, credit, base, bal
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.account_id,
""" + include + """
    abs(tag.net),
    abs(tag.tax),
    abs(tag.debit),
    abs(tag.credit),
    abs(tag.base),
    abs(tag.bal)
FROM
    taxtags tag
"""
        query_inject_tax_params = (self.company_id.id, self.date_from,
                                           self.date_to, self.id, self.env.uid)
        # _logger.info("SQL %s" % query_inject_taxtags_vat)
        _logger.info("SQL %s" % (query_inject_taxtags_vat % query_inject_tax_params))
        self.env.cr.execute(query_inject_taxtags_vat, query_inject_tax_params)
