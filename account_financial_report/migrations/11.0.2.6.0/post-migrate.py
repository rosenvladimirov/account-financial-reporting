# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.api import Environment, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    for line in env['account.move.line'].search([('tax_sign', '=', 0)]):
        line.write({'tax_sign': line.invoice_id and line.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1 or 1})
