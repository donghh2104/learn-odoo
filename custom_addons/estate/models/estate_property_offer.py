# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Lời đề nghị mua'
    _order = 'price desc'

    # === SQL Constraints ===
    _sql_constraints = [
        ('check_price_positive',
         'CHECK(price > 0)',
         'Giá đề nghị phải là số dương.'),
    ]

    # === Fields ===
    price = fields.Float(string='Giá đề nghị')
    status = fields.Selection(
        selection=[
            ('accepted', 'Đã chấp nhận'),
            ('refused', 'Đã từ chối'),
        ],
        string='Trạng thái',
        copy=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
        required=True,
    )
    property_id = fields.Many2one(
        'estate.property',
        string='Bất động sản',
        required=True,
    )

    validity = fields.Integer(
        string='Hiệu lực (ngày)',
        default=7,
    )
    date_deadline = fields.Date(
        string='Hạn chót',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
    )

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for record in self:
            date = record.create_date or fields.Datetime.now()
            record.date_deadline = date.date() + relativedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline and record.create_date:
                record.validity = (record.date_deadline - record.create_date.date()).days
            elif record.date_deadline:
                record.validity = (record.date_deadline - fields.Date.today()).days

    @api.model_create_multi
    def create(self, vals_list):
        offers = super().create(vals_list)
        for offer in offers:
            if offer.property_id.state in ('sold', 'canceled'):
                raise UserError('Không thể tạo đề nghị cho BĐS đã bán hoặc đã hủy.')
            if offer.property_id.state == 'new':
                offer.property_id.state = 'offer_received'
        return offers

    # === Action Methods ===
    def action_accept(self):
        for record in self:
            if record.property_id.state in ('sold', 'canceled'):
                raise UserError('Không thể chấp nhận đề nghị cho BĐS đã bán hoặc đã hủy.')
            existing_accepted = record.property_id.offer_ids.filtered(
                lambda o: o.status == 'accepted' and o.id != record.id
            )
            if existing_accepted:
                raise UserError("Bất động sản này đã có lời đề nghị được chấp nhận rồi!")

            record.status = 'accepted'
            record.property_id.write({
                'selling_price': record.price,
                'buyer_id': record.partner_id.id,
                'state': 'offer_accepted',
            })
            record.property_id.offer_ids.filtered(
                lambda o: o.id != record.id and o.status == 'accepted'
            ).write({'status': 'refused'})
            record.property_id.message_post(
                body=_('Đã chấp nhận đề nghị %(price)s từ khách hàng %(partner)s.') % {
                    'price': record.price,
                    'partner': record.partner_id.display_name,
                }
            )
        return True

    def action_refuse(self):
        for record in self:
            if record.status == 'accepted':
                raise UserError(
                    "Không thể từ chối lời đề nghị đã được chấp nhận. "
                    "Vui lòng kiểm tra lại trạng thái."
                )
            record.status = 'refused'
            record.property_id.message_post(
                body=_('Đã từ chối đề nghị %(price)s từ khách hàng %(partner)s.') % {
                    'price': record.price,
                    'partner': record.partner_id.display_name,
                }
            )
        return True

    @api.model
    def _cron_notify_expiring_offers(self):
        target_date = fields.Date.today() + relativedelta(days=1)
        offers = self.search([
            ('status', '=', False),
            ('date_deadline', '=', target_date),
            ('property_id.state', 'in', ['new', 'offer_received']),
            ('property_id.salesperson_id', '!=', False),
        ])
        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_type:
            return True

        for offer in offers:
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', 'estate.property'),
                ('res_id', '=', offer.property_id.id),
                ('activity_type_id', '=', todo_type.id),
                ('user_id', '=', offer.property_id.salesperson_id.id),
                ('summary', '=', 'Offer sắp hết hạn'),
            ], limit=1)
            if not existing_activity:
                offer.property_id.activity_schedule(
                    activity_type_id=todo_type.id,
                    user_id=offer.property_id.salesperson_id.id,
                    summary='Offer sắp hết hạn',
                    note=_('Đề nghị từ %(partner)s sẽ hết hạn vào %(deadline)s.') % {
                        'partner': offer.partner_id.display_name,
                        'deadline': offer.date_deadline,
                    },
                    date_deadline=offer.date_deadline,
                )
        return True
