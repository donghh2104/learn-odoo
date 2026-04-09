from odoo import models


class Dog(models.Model):
    _name = 'dog'
    _inherit = ['my_module.animal_abstract']

    def _sound(self):
        super(Dog, self)._sound()
        return "Gau Gau"

    def action_create_dog(self):
        return {
            'name': 'Create Dog',
            'res_model': 'transient.model',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }