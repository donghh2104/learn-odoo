# -*- coding: utf-8 -*-

from odoo import models, fields


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Nhãn bất động sản'
    _order = 'name'

    name = fields.Char(string='Tên nhãn', required=True)
    color = fields.Integer(string='Màu sắc')
