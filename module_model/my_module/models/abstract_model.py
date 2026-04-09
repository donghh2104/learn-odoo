from odoo import models, fields


class AnimalAbstract(models.AbstractModel):
    _name = 'my_module.animal_abstract'
    _description = 'Animal Abstract'

    name = fields.Char(string='Name', required=True)
    gender = fields.Selection([('female', 'Female'), ('male', 'Male')], string='Gender')
    color = fields.Char(string='Color')
    age = fields.Integer(string='Age')
    total = fields.Float(string='Total', digits=(2, 2), default=0.0)
    available = fields.Boolean(string='Available', default=True)

    def _sound(self):
        pass
    