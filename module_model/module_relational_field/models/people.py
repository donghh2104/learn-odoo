from odoo import models, fields, api
from odoo.exceptions import ValidationError


class People(models.Model):
    _name = 'people'
    _description = 'People'

    name = fields.Char(string='Name')
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')

    # One2many field
    # house_ids = fields.One2many('house', 'people_id', string='House')

    @api.constrains('age')
    def _check_age(self):
        for record in self:
            if record.age < 0:
                raise ValidationError("Tuổi không được là số âm!")