from odoo import models, fields


class Cetizen(models.Model):
    _name = 'cetizen'
    _description = 'Cetizen'
    _inherits = {'people': 'passport_id'}


    def _selection_list(self):
        models = self.env['ir.model'].search([('model', 'in', ['res.users', 'res.country'])])
        return [(model.model, model.name) for model in models]


    # One2one field
    passport_id = fields.Many2one('people',required=True, ondelete = 'cascade', string='Passport')        

    #reference field
    ref_model = fields.Selection(_selection_list, string='Reference Model')
    ref_id = fields.Many2oneReference(
        "Reference",
        model_field="ref_model",
        ondelete="cascade",
    )