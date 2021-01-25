# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

# from lxml import etree, html
from datetime import datetime, timedelta

import babel
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models, tools, _
import copy
import functools
from werkzeug import urls
from odoo.tools import pycompat

# from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class CustomerOutstandingStatement(models.AbstractModel):
    """Model of Customer Outstanding Statement"""

    _name = 'report.customer_outstanding_statement.statement'

    amount_due = fields.Char()

    def _format_date_to_partner_lang(self, str_date, partner_id):
        lang_code = self.env['res.partner'].browse(partner_id).lang
        lang = self.env['res.lang']._lang_get(lang_code)
        date = datetime.strptime(str_date, DEFAULT_SERVER_DATE_FORMAT).date()
        return date.strftime(lang.date_format)

    def _display_lines_sql_q1(self, partners, date_end, account_type):
        return """
            SELECT m.name as move_id, m.id as move_move_id, l.partner_id, l.date, l.name,
                            l.ref, l.blocked, l.currency_id, l.company_id,
            CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                THEN avg(l.amount_currency)
                ELSE avg(l.debit)
            END as debit,
            CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                THEN avg(l.amount_currency * (-1))
                ELSE avg(l.credit)
            END as credit,
            CASE WHEN l.balance > 0.0
                THEN l.balance - sum(coalesce(pd.amount, 0.0))
                ELSE l.balance + sum(coalesce(pc.amount, 0.0))
            END AS open_amount,
            CASE WHEN l.balance > 0.0
                THEN l.amount_currency - sum(coalesce(pd.amount_currency, 0.0))
                ELSE l.amount_currency + sum(coalesce(pc.amount_currency, 0.0))
            END AS open_amount_currency,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM account_move_line l
            JOIN account_account_type at ON (at.id = l.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= '%s'
            ) as pd ON pd.debit_move_id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= '%s'
            ) as pc ON pc.credit_move_id = l.id
            WHERE l.partner_id IN (%s) AND at.type = '%s'
                                AND (
                                  (pd.id IS NOT NULL AND
                                      pd.max_date <= '%s') OR
                                  (pc.id IS NOT NULL AND
                                      pc.max_date <= '%s') OR
                                  (pd.id IS NULL AND pc.id IS NULL)
                                ) AND l.date <= '%s'
            GROUP BY l.partner_id, m.name, m.id, l.date, l.date_maturity, l.name,
                                l.ref, l.blocked, l.currency_id,
                                l.balance, l.amount_currency, l.company_id
        """ % (date_end, date_end, partners, account_type, date_end,
               date_end, date_end)

    def _display_lines_sql_q2(self):
        return """
            SELECT Q1.partner_id, Q1.currency_id, Q1.move_id, Q1.move_move_id,
            Q1.date, Q1.date_maturity, Q1.debit, Q1.credit,
            Q1.name, Q1.ref, Q1.blocked, Q1.company_id,
            CASE WHEN Q1.currency_id is not null
                    THEN open_amount_currency
                    ELSE open_amount
            END as open_amount
            FROM Q1
        """

    def _display_lines_sql_q3(self, company_id):
        return """
            SELECT Q2.partner_id, Q2.move_id, Q2.move_move_id, Q2.date, Q2.date_maturity,
            Q2.name, Q2.ref, Q2.debit, Q2.credit,
            Q2.debit-Q2.credit AS amount, blocked,
            COALESCE(Q2.currency_id, c.currency_id) AS currency_id,
            Q2.open_amount
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %s
        """ % company_id

    def _get_account_display_lines(self, company_id, partner_ids, date_end,
                                   account_type):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = ', '.join([str(i) for i in partner_ids])
        date_end = datetime.strptime(
            date_end, DEFAULT_SERVER_DATE_FORMAT).date()
        # pylint: disable=E8103
        self.env.cr.execute("""
        WITH Q1 AS (%s), Q2 AS (%s), Q3 AS (%s)
        SELECT partner_id, currency_id, move_id, move_move_id, date, date_maturity, debit,
                            credit, amount, open_amount, name, ref, blocked
        FROM Q3
        ORDER BY date, date_maturity, move_id""" % (
            self._display_lines_sql_q1(partners, date_end, account_type),
            self._display_lines_sql_q2(),
            self._display_lines_sql_q3(company_id)))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        return res

    def _show_buckets_sql_q1(self, partners, date_end, account_type):
        return """
            SELECT l.partner_id, l.currency_id, l.company_id, l.move_id,
            CASE WHEN l.balance > 0.0
                THEN l.balance - sum(coalesce(pd.amount, 0.0))
                ELSE l.balance + sum(coalesce(pc.amount, 0.0))
            END AS open_due,
            CASE WHEN l.balance > 0.0
                THEN l.amount_currency - sum(coalesce(pd.amount_currency, 0.0))
                ELSE l.amount_currency + sum(coalesce(pc.amount_currency, 0.0))
            END AS open_due_currency,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM account_move_line l
            JOIN account_account_type at ON (at.id = l.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= '%s'
            ) as pd ON pd.debit_move_id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= '%s'
            ) as pc ON pc.credit_move_id = l.id
            WHERE l.partner_id IN (%s) AND at.type = '%s'
                                AND (
                                  (pd.id IS NOT NULL AND
                                      pd.max_date <= '%s') OR
                                  (pc.id IS NOT NULL AND
                                      pc.max_date <= '%s') OR
                                  (pd.id IS NULL AND pc.id IS NULL)
                                ) AND l.date <= '%s' AND not l.blocked
            GROUP BY l.partner_id, l.currency_id, l.date, l.date_maturity,
                                l.amount_currency, l.balance, l.move_id,
                                l.company_id, l.id
        """ % (date_end, date_end, partners, account_type, date_end,
               date_end, date_end)

    def _show_buckets_sql_q2(self, date_end, minus_30, minus_60, minus_90,
                             minus_120):
        return """
            SELECT partner_id, currency_id, date_maturity, open_due,
                            open_due_currency, move_id, company_id,
            CASE
                WHEN '%s' <= date_maturity AND currency_id is null
                                THEN open_due
                WHEN '%s' <= date_maturity AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as current,
            CASE
                WHEN '%s' < date_maturity AND date_maturity < '%s'
                                AND currency_id is null THEN open_due
                WHEN '%s' < date_maturity AND date_maturity < '%s'
                                AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as b_1_30,
            CASE
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is null THEN open_due
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as b_30_60,
            CASE
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is null THEN open_due
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as b_60_90,
            CASE
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is null THEN open_due
                WHEN '%s' < date_maturity AND date_maturity <= '%s'
                                AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as b_90_120,
            CASE
                WHEN date_maturity <= '%s' AND currency_id is null
                                THEN open_due
                WHEN date_maturity <= '%s' AND currency_id is not null
                                THEN open_due_currency
                ELSE 0.0
            END as b_over_120
            FROM Q1
            GROUP BY partner_id, currency_id, date_maturity, open_due,
                                open_due_currency, move_id, company_id
        """ % (date_end, date_end, minus_30, date_end, minus_30, date_end,
               minus_60, minus_30, minus_60, minus_30, minus_90, minus_60,
               minus_90, minus_60, minus_120, minus_90, minus_120, minus_90,
               minus_120, minus_120)

    def _show_buckets_sql_q3(self, company_id):
        return """
            SELECT Q2.partner_id, current, b_1_30, b_30_60, b_60_90, b_90_120,
                                b_over_120,
            COALESCE(Q2.currency_id, c.currency_id) AS currency_id
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %s
        """ % company_id

    def _show_buckets_sql_q4(self):
        return """
            SELECT partner_id, currency_id, sum(current) as current,
                                sum(b_1_30) as b_1_30,
                                sum(b_30_60) as b_30_60,
                                sum(b_60_90) as b_60_90,
                                sum(b_90_120) as b_90_120,
                                sum(b_over_120) as b_over_120
            FROM Q3
            GROUP BY partner_id, currency_id
        """

    def _get_bucket_dates(self, date_end):
        return {
            'date_end': date_end,
            'minus_30': date_end - timedelta(days=30),
            'minus_60': date_end - timedelta(days=60),
            'minus_90': date_end - timedelta(days=90),
            'minus_120': date_end - timedelta(days=120),
        }

    def _get_account_show_buckets(self, company_id, partner_ids, date_end,
                                  account_type):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = ', '.join([str(i) for i in partner_ids])
        date_end = datetime.strptime(
            date_end, DEFAULT_SERVER_DATE_FORMAT).date()
        full_dates = self._get_bucket_dates(date_end)
        # pylint: disable=E8103
        self.env.cr.execute("""
        WITH Q1 AS (%s), Q2 AS (%s), Q3 AS (%s), Q4 AS (%s)
        SELECT partner_id, currency_id, current, b_1_30, b_30_60, b_60_90,
                            b_90_120, b_over_120,
                            current+b_1_30+b_30_60+b_60_90+b_90_120+b_over_120
                            AS balance
        FROM Q4
        GROUP BY partner_id, currency_id, current, b_1_30, b_30_60, b_60_90,
        b_90_120, b_over_120""" % (
            self._show_buckets_sql_q1(partners, date_end, account_type),
            self._show_buckets_sql_q2(
                full_dates['date_end'],
                full_dates['minus_30'],
                full_dates['minus_60'],
                full_dates['minus_90'],
                full_dates['minus_120']),
            self._show_buckets_sql_q3(company_id),
            self._show_buckets_sql_q4()))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        return res

    @api.multi
    def get_report_values(self, docids, data):
        def format_date(env, date, pattern=False):
            if not date:
                return ''
            try:
                return tools.format_date(env, date, date_format=pattern)
            except babel.core.UnknownLocaleError:
                return date

        def format_tz(env, dt, tz=False, format=False):
            record_user_timestamp = env.user.sudo().with_context(tz=tz or env.user.sudo().tz or 'UTC')
            timestamp = datetime.datetime.strptime(dt, tools.DEFAULT_SERVER_DATETIME_FORMAT)

            ts = fields.Datetime.context_timestamp(record_user_timestamp, timestamp)

            # Babel allows to format datetime in a specific language without change locale
            # So month 1 = January in English, and janvier in French
            # Be aware that the default value for format is 'medium', instead of 'short'
            #     medium:  Jan 5, 2016, 10:20:31 PM |   5 janv. 2016 22:20:31
            #     short:   1/5/16, 10:20 PM         |   5/01/16 22:20
            if env.context.get('use_babel'):
                # Formatting available here : http://babel.pocoo.org/en/latest/dates.html#date-fields
                from babel.dates import format_datetime
                return format_datetime(ts, format or 'medium', locale=env.context.get("lang") or 'en_US')

            if format:
                return pycompat.text_type(ts.strftime(format))
            else:
                lang = env.context.get("lang")
                langs = env['res.lang']
                if lang:
                    langs = env['res.lang'].search([("code", "=", lang)])
                format_date = langs.date_format or '%B-%d-%Y'
                format_time = langs.time_format or '%I-%M %p'

                fdate = pycompat.text_type(ts.strftime(format_date))
                ftime = pycompat.text_type(ts.strftime(format_time))
                return u"%s %s%s" % (fdate, ftime, (u' (%s)' % tz) if tz else u'')

        def format_amount(env, amount, currency):
            fmt = "%.{0}f".format(currency.decimal_places)
            lang = env['res.lang']._lang_get(env.context.get('lang') or 'en_US')

            formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True) \
                .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

            pre = post = u''
            if currency.position == 'before':
                pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
            else:
                post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

            return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

        def complete_msg(msg, locals_dict):
            company_currency = False
            format_amount = False
            variables = {}
            lang = locals_dict.get('Partner') and locals_dict['Partner'].lang or 'en_US'
            variables['lang'] = lang

            if locals_dict.get('Show_Buckets'):
                variables['Show_Buckets'] = locals_dict['Show_Buckets']
            if locals_dict.get('Show_Lines'):
                variables['Show_Lines'] = locals_dict['Show_Lines']
            if locals_dict.get('Date_end'):
                variables['Date_end'] = locals_dict['Date_end']
            if locals_dict.get('Date'):
                variables['Date'] = locals_dict['Date']

            if locals_dict.get('Partner'):
                variables['Partner'] = locals_dict['Partner']
                del locals_dict['Partner']

            if locals_dict.get('Company_Currency'):
                company_currency = locals_dict['Company_Currency']
                variables['company_currency'] = locals_dict['Company_Currency']
                del locals_dict['Company_Currency']

            if locals_dict.get('format_amount'):
                format_amount = locals_dict['format_amount']
                variables['format_amount'] = locals_dict['format_amount']
                del locals_dict['format_amount']

            if locals_dict.get('Amount_Due'):
                currencies = {}
                for k, v in locals_dict['Amount_Due'].items():
                    if company_currency and format_amount:
                        if locals_dict.get('Currencies') and locals_dict['Currencies'][k]:
                            v = format_amount(v, locals_dict['Currencies'][k])
                        else:
                            v = format_amount(v, company_currency)
                    currencies.update({k: {'amount': v}})
                if currencies:
                    locals_dict['Amount_Due'] = ", ".join(["%s" % v.get('amount', 0.0) for k, v in currencies.items()])
            variables['object'] = locals_dict

            # msg = self.env['ir.qweb'].render(etree.fromstring("<t name='customer_outstanding_statement.complete_msg'><div>" + msg + "</div></t>"), values=locals_dict)
            # msg = safe_eval("<template>" + msg + "</template>", locals_dict=locals_dict)
            # try to load the template
            try:
                mako_env = mako_safe_template_env if locals_dict.get('safe') else mako_template_env
                template = mako_env.from_string(tools.ustr(msg))
            except Exception:
                _logger.info("Failed to load template %r", msg, exc_info=True)
                return msg
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
                raise UserError(_("Failed to render template %r using values %r")% (template, variables))
            if render_result == u"False":
                render_result = u""
            return render_result

        company_id = data['company_id']
        partner_ids = data['partner_ids']
        date_end = data['date_end']
        account_type = data['account_type']
        today = fields.Date.today()
        use_detailed = data['use_detailed']
        use_invoice_detail = data['use_invoice_detail']
        use_partner_selection = data['use_partner_selection']
        use_sale_detail = data['use_sale_detail']
        use_picking_detail = data['use_picking_detail']
        use_product_properties = data['use_product_properties']
        static_template_id = data['static_template_id']
        static_note = data['static_note']
        product_prop_static_id = data['product_prop_static_id']
        print_properties = data['print_properties']
        print_sets = data['print_sets']
        print_lots = data['print_lots']
        show_lines = data['show_lines']
        use_digital_sign = data['use_digital_sign']
        issue_user_id = data['issue_user_id']

        buckets_to_display = {}
        lines_to_display, amount_due = {}, {}
        currency_to_display = {}
        today_display, date_end_display = {}, {}

        any_invoice = False
        any_sale = False
        any_picking = False
        lines = self._get_account_display_lines(
            company_id, partner_ids, date_end, account_type)

        for partner_id in partner_ids:
            lines_to_display[partner_id], amount_due[partner_id] = {}, {}
            currency_to_display[partner_id] = {}
            today_display[partner_id] = self._format_date_to_partner_lang(
                today, partner_id)
            date_end_display[partner_id] = self._format_date_to_partner_lang(
                date_end, partner_id)
            for line in lines[partner_id]:
                line['invoice_id'] = self.env['account.invoice']
                line['sale_order_id'] = self.env['sale.order']
                line['stock_picking_id'] = self.env['stock.picking']
                currency = self.env['res.currency'].browse(line['currency_id'])
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    currency_to_display[partner_id][currency] = currency
                    amount_due[partner_id][currency] = 0.0
                if not line['blocked']:
                    amount_due[partner_id][currency] += line['open_amount']
                line['balance'] = amount_due[partner_id][currency]
                line['date'] = self._format_date_to_partner_lang(
                    line['date'], partner_id)
                line['date_maturity'] = self._format_date_to_partner_lang(
                    line['date_maturity'], partner_id)
                move_line = self.env['account.move'].browse([line['move_move_id']])
                # _logger.info("MOVE %s" % move_line)
                line['invoice_id'] = move_line.line_ids and move_line.with_context(lang=self.env['res.partner'].browse(partner_id).lang).line_ids[0].invoice_id or False
                # if line['invoice_id']:
                #     _logger.info('INVOICE-MOVE %s:%s' % (move_line, line['invoice_id']))
                if line['invoice_id']:
                    any_invoice = True
                    if len(line['invoice_id'].picking_ids.ids) > 0:
                        any_picking = True
                        line['stock_picking_id'] |= line['invoice_id'].picking_ids
                    for inv_line in line['invoice_id'].invoice_line_ids:
                        sale_lines = inv_line.mapped('sale_line_ids')
                        for sale_line in sale_lines:
                            line['sale_order_id'] |= sale_line.order_id
                            any_sale = True
                lines_to_display[partner_id][currency].append(line)
                #_logger.info("LINE %s" % line)

        if data['show_aging_buckets']:
            buckets = self._get_account_show_buckets(
                company_id, partner_ids, date_end, account_type)
            for partner_id in partner_ids:
                buckets_to_display[partner_id] = {}
                for line in buckets[partner_id]:
                    currency = self.env['res.currency'].browse(
                        line['currency_id'])
                    if currency not in buckets_to_display[partner_id]:
                        buckets_to_display[partner_id][currency] = []
                    buckets_to_display[partner_id][currency] = line

        if use_invoice_detail and not any_invoice:
            use_invoice_detail = False
        if use_sale_detail and not any_sale:
            use_sale_detail = False
        if use_picking_detail and not any_picking:
            use_picking_detail = False
        product_prop_static = self.env['product.properties.static'].browse([product_prop_static_id])
        print_properties = self.env['product.properties.print.wizard'].browse(print_properties)
        user_print = self.env['hr.employee'].browse(issue_user_id)
        # _logger.info("PROPERTIES %s:%s:%s:%s" % (data, product_prop_static, print_properties, static_template_id))
        return {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'Amount_Due': amount_due,
            'Lines': lines_to_display,
            'Buckets': buckets_to_display,
            'Currencies': currency_to_display,
            'Show_Buckets': data['show_aging_buckets'],
            'Show_Lines': show_lines,
            'Filter_non_due_partners': data['filter_non_due_partners'],
            'Date_end': date_end_display,
            'Company_Currency': self.env.user.company_id.currency_id,
            'Date': today_display,
            'date_end_report': date_end,
            'account_type': account_type,
            'use_detailed': use_detailed,
            'use_invoice_detail': use_invoice_detail,
            'use_partner_selection': use_partner_selection,
            'use_sale_detail': use_sale_detail,
            'use_product_properties': use_product_properties,
            'use_picking_detail': use_picking_detail,
            'static_template_id': static_template_id,
            'static_note': static_note,
            'product_prop_static': product_prop_static,
            'print_properties': print_properties,
            'print_sets': print_sets,
            'print_lots': print_lots,
            'has_hscode': False,
            'use_digital_sign': use_digital_sign,
            'user_print_sign': user_print.user_id,
            'user_print': user_print,
            'compute_msg': complete_msg,
            'format_date': lambda date, format=False, context=self._context: format_date(self.env, date, format),
            'format_tz': lambda dt, tz=False, format=False, context=self._context: format_tz(self.env, dt, tz, format),
            'format_amount': lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
            # 'to_html': self.env['ir.qweb.field.html'].value_to_html,
        }
