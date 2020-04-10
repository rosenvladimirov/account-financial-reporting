# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AbstractReport(models.AbstractModel):
    _name = 'account_financial_report_abstract'

    has_report_qweb = fields.Boolean(compute="_has_report_qweb")
    has_report_fillpdf = fields.Boolean(compute="_has_report_fillpdf")
    has_report_csv = fields.Boolean(compute="_has_report_csv")
    has_report_xml = fields.Boolean(compute="_has_report_xml")

    fillpdf = fields.Binary()

    def _has_report_qweb(self):
        self.has_report_qweb = self._get_default_qweb() != False

    def _has_report_fillpdf(self):
        self.has_report_fillpdf = self._get_default_fillpdf() != False

    def _has_report_csv(self, report_sub_type=False):
        self.has_report_csv = self._get_default_csv(report_sub_type=report_sub_type) != False

    def _has_report_xml(self):
        self.has_report_xml = self._get_default_xml() != False

    def _get_default_qweb(self):
        report_name = 'account_financial_report.report_vat_report_qweb'
        report_type = 'qweb'
        return self.env['ir.actions.report'].search(
                [('report_name', '=', report_name),
                 ('report_type', '=', report_type)], limit=1)

    def _get_default_xlsx(self):
        report_name = 'a_f_r.report_vat_report_xlsx'
        report_type = 'xlsx'
        return self.env['ir.actions.report'].search(
                [('report_name', '=', report_name),
                 ('report_type', '=', report_type)], limit=1)

    def _get_default_fillpdf(self):
        return False

    def _get_default_csv(self, report_sub_type=False):
        return False

    def _get_default_xml(self):
        return False

    def _transient_clean_rows_older_than(self, seconds):
        assert self._transient, \
            "Model %s is not transient, it cannot be vacuumed!" % self._name
        # Never delete rows used in last 5 minutes
        seconds = max(seconds, 300)
        query = """
DELETE FROM """ + self._table + """
WHERE COALESCE(
    write_date, create_date, (now() at time zone 'UTC'))::timestamp
    < ((now() at time zone 'UTC') - interval %s)
"""
        self.env.cr.execute(query, ("%s seconds" % seconds,))
