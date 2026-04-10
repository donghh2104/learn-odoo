# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class EstatePropertyOfferWizard(models.TransientModel):
    _name = 'estate.property.offer.wizard'
    _description = 'Tạo đề nghị hàng loạt'

    price = fields.Float(string='Giá đề nghị', required=True)
    discount_percent = fields.Float(string='Chiết khấu (%)', default=0.0)
    validity = fields.Integer(string='Hiệu lực (ngày)', default=7)
    partner_id = fields.Many2one('res.partner', string='Người mua', required=True)
    note = fields.Text(string='Ghi chú nội bộ')
    property_ids = fields.Many2many('estate.property', string='Bất động sản', required=True)

    @api.constrains('discount_percent')
    def _check_discount_percent(self):
        for rec in self:
            if rec.discount_percent < 0 or rec.discount_percent > 100:
                raise UserError('Chiết khấu phải nằm trong khoảng từ 0 đến 100%.')

    def _get_final_price(self):
        self.ensure_one()
        return self.price * (1 - (self.discount_percent / 100.0))

    def action_create_offers(self):
        self.ensure_one()
        final_price = self._get_final_price()

        valid_properties = self.property_ids.filtered(lambda p: p.state in ('new', 'offer_received'))
        if not valid_properties:
            raise UserError('Không có BĐS hợp lệ để tạo đề nghị (chỉ cho phép trạng thái Mới/Đã nhận đề nghị).')

        offers = self.env['estate.property.offer']
        for property_rec in valid_properties:
            offer = self.env['estate.property.offer'].create({
                'price': final_price,
                'partner_id': self.partner_id.id,
                'property_id': property_rec.id,
                'validity': self.validity,
            })
            offers |= offer
            if self.note:
                property_rec.message_post(body='[Wizard] %s' % self.note)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tạo đề nghị thành công',
                'message': 'Đã tạo %s đề nghị mới.' % len(offers),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
