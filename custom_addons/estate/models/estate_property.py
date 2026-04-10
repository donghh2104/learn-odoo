# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Bất động sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # === SQL Constraints ===
    _sql_constraints = [
        ('check_expected_price_positive',
         'CHECK(expected_price > 0)',
         'Giá mong muốn phải là số dương.'),
        ('check_selling_price_positive',
         'CHECK(selling_price >= 0)',
         'Giá bán không được là số âm.'),
    ]

    # === Basic Fields ===
    reference = fields.Char(
        string='Mã tham chiếu',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    name = fields.Char(string='Tiêu đề', required=True, tracking=True)
    description = fields.Text(string='Mô tả')
    postcode = fields.Char(string='Mã bưu điện')
    date_availability = fields.Date(
        string='Ngày có hiệu lực',
        default=lambda self: fields.Date.today() + relativedelta(months=3),
        copy=False,
    )
    expected_price = fields.Float(string='Giá mong muốn', required=True, tracking=True)
    selling_price = fields.Float(string='Giá bán thực tế', readonly=True, copy=False, tracking=True)
    bedrooms = fields.Integer(string='Số phòng ngủ', default=2)
    living_area = fields.Integer(string='Diện tích sàn (m2)')
    facades = fields.Integer(string='Số mặt tiền')
    garage = fields.Boolean(string='Có Gara')
    garden = fields.Boolean(string='Có sân vườn')
    garden_area = fields.Integer(string='Diện tích sân vườn (m2)')
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'Bắc'),
            ('south', 'Nam'),
            ('east', 'Đông'),
            ('west', 'Tây'),
        ],
        string='Hướng sân vườn',
    )
    active = fields.Boolean(string='Đang hoạt động', default=True)
    image = fields.Binary(string='Hình ảnh', attachment=True)

    # === State Field ===
    state = fields.Selection(
        selection=[
            ('new', 'Mới'),
            ('offer_received', 'Đã nhận đề nghị'),
            ('offer_accepted', 'Đã chấp nhận'),
            ('sold', 'Đã bán'),
            ('canceled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        copy=False,
        default='new',
        tracking=True,
    )

    # === Relational Fields ===
    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Loại BĐS',
    )
    buyer_id = fields.Many2one(
        'res.partner',
        string='Người mua',
        readonly=True,
        copy=False,
        tracking=True,
    )
    salesperson_id = fields.Many2one(
        'res.users',
        string='Nhân viên phụ trách',
        default=lambda self: self.env.user,
        tracking=True,
    )
    tag_ids = fields.Many2many(
        'estate.property.tag',
        string='Nhãn/Tags',
    )
    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_id',
        string='Danh sách lời đề nghị',
    )

    # === Computed Fields ===
    total_area = fields.Integer(
        string='Tổng diện tích (m2)',
        compute='_compute_total_area',
        help='Tổng diện tích sàn và diện tích sân vườn',
    )
    best_price = fields.Float(
        string='Giá đề nghị tốt nhất',
        compute='_compute_best_price',
        store=True,
    )
    offer_count = fields.Integer(
        string='Số lượng đề nghị',
        compute='_compute_offer_count',
    )

    priority_level = fields.Selection(
        selection=[
            ('high', 'Cao'),
            ('normal', 'Bình thường'),
            ('low', 'Thấp'),
        ],
        string='Mức độ ưu tiên',
        default='normal',
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('estate.property') or _('New')
        return super().create(vals_list)

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            if record.offer_ids:
                record.best_price = max(record.offer_ids.mapped('price'))
            else:
                record.best_price = 0.0

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    # === Onchange ===
    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'south'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # === Python Constraints ===
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if record.selling_price > 0 and record.expected_price > 0:
                if record.selling_price < record.expected_price * 0.9:
                    raise ValidationError(
                        "Giá bán không được thấp hơn 90% giá mong muốn! "
                        "Bạn cần điều chỉnh lại giá mong muốn nếu muốn chấp nhận đề nghị này."
                    )

    # === Action Methods ===
    def action_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise UserError("Nhà đã hủy thì không thể bán.")
            if record.state != 'offer_accepted':
                raise UserError("Bạn phải chấp nhận một lời đề nghị trước khi xác nhận Đã bán.")
            record.state = 'sold'
            record.message_post(body=_('Bất động sản đã được chốt bán.'))
        return True

    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError("Nhà đã bán thì không thể hủy.")
            record.state = 'canceled'
            record.message_post(body=_('Bất động sản đã bị hủy niêm yết.'))
        return True

    def action_set_to_new(self):
        for record in self:
            if record.state == 'sold':
                raise UserError('Không thể reset trạng thái cho bất động sản đã bán.')
            record.write({
                'state': 'new',
                'buyer_id': False,
                'selling_price': 0.0,
            })
            record.offer_ids.filtered(lambda offer: offer.status == 'accepted').write({'status': 'refused'})
            record.message_post(body=_('Bất động sản đã được reset về trạng thái Mới.'))
        return True

    @api.model
    def _cron_schedule_stale_property_activities(self):
        stale_days = int(self.env['ir.config_parameter'].sudo().get_param('estate.stale_days', 14))
        limit_date = fields.Datetime.now() - relativedelta(days=stale_days)
        stale_properties = self.search([
            ('state', 'in', ['new', 'offer_received']),
            ('create_date', '<=', limit_date),
            ('salesperson_id', '!=', False),
        ])

        todo_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not todo_type:
            return True

        for property_rec in stale_properties:
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', 'estate.property'),
                ('res_id', '=', property_rec.id),
                ('activity_type_id', '=', todo_type.id),
                ('user_id', '=', property_rec.salesperson_id.id),
                ('date_deadline', '>=', fields.Date.today()),
            ], limit=1)
            if not existing_activity:
                property_rec.activity_schedule(
                    activity_type_id=todo_type.id,
                    user_id=property_rec.salesperson_id.id,
                    note=_('Bất động sản đã tồn đọng khá lâu, vui lòng theo dõi và cập nhật tiến độ.'),
                    summary=_('Follow-up bất động sản tồn đọng'),
                )
        return True
