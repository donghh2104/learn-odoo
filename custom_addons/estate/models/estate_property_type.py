# -*- coding: utf-8 -*-

from odoo import models, fields


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Loại bất động sản'
    _order = 'sequence, name'

    # === SQL Constraints ===
    _sql_constraints = [
        ('unique_type_name',
         'UNIQUE(name)',
         'Tên loại bất động sản phải duy nhất.'),
    ]

    name = fields.Char(string='Tên loại', required=True)
    sequence = fields.Integer(string='Thứ tự', default=10)

    property_ids = fields.One2many(
        'estate.property',
        'property_type_id',
        string='Danh sách BĐS',
    )
