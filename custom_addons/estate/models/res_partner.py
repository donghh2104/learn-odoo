# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_ids = fields.One2many(
        'estate.property',
        'buyer_id',
        string='BĐS đã mua',
    )
