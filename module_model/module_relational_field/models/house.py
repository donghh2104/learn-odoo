from odoo import models, fields, api


class House(models.Model):
    _name = 'house'
    _description = 'House'

    name = fields.Char(string='Name')

    # Many2one field
    people_id = fields.Many2one('people', string='Owner')

    price = fields.Float(string='Price', compute='_compute_price', store=True)

    owner_gender = fields.Selection(related='people_id.gender', string='Owner Gender', store=True)
    # Many2many field
    people_ids = fields.Many2many('people', string='People')

    @api.depends('people_ids.age')
    def _compute_price(self):
        for record in self:
            total_price = 0
            for person in record.people_ids:
                if person.age > 6:
                    total_price += 30
                else:
                    total_price += 10
            record.price = total_price