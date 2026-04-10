# -*- coding: utf-8 -*-

import base64
import json
import logging
from datetime import datetime, timedelta

import jwt

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class EstateAPI(http.Controller):

    # =========================================================
    # Helpers
    # =========================================================
    def _json_response(self, payload, status=200, headers=None):
        response = request.make_response(
            json.dumps(payload, default=str),
            headers=[('Content-Type', 'application/json')] + (headers or []),
        )
        response.status_code = status
        return response

    def _ok(self, data=None, message='Success', meta=None, status=200):
        return self._json_response({
            'status': 'success',
            'message': message,
            'data': data,
            'errors': [],
            'meta': meta or {},
        }, status=status)

    def _error(self, message='Error', errors=None, status=400):
        return self._json_response({
            'status': 'error',
            'message': message,
            'data': None,
            'errors': errors or [],
            'meta': {},
        }, status=status)

    def _parse_json_body(self):
        raw = request.httprequest.data or b'{}'
        if not raw:
            return {}
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception:
            raise ValidationError('Request body phải là JSON hợp lệ.')

    def _get_jwt_secret(self):
        return request.env['ir.config_parameter'].sudo().get_param('estate.jwt_secret') or 'default-secret-key-123'

    def _auth_with_jwt(self):
        auth_header = request.httprequest.headers.get('Authorization', '')
        parts = auth_header.split()
        if len(parts) < 2 or parts[0].lower() != 'bearer':
            return None, self._error('Unauthorized - Thiếu token Bearer', status=401)

        token = parts[1]
        try:
            payload = jwt.decode(token, str(self._get_jwt_secret()), algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                return None, self._error('Token không chứa user_id', status=401)
            return int(user_id), None
        except jwt.ExpiredSignatureError:
            return None, self._error('Token đã hết hạn', status=401)
        except jwt.InvalidTokenError:
            return None, self._error('Token không hợp lệ', status=401)

    def _execute_secured(self, callback, *args, **kwargs):
        user_id, auth_error = self._auth_with_jwt()
        if auth_error:
            return auth_error

        try:
            return callback(user_id, *args, **kwargs)
        except AccessError as exc:
            return self._error(str(exc), status=403)
        except (UserError, ValidationError) as exc:
            return self._error(str(exc), status=400)
        except Exception as exc:
            _logger.exception('Estate API internal error: %s', exc)
            return self._error('Internal Server Error', status=500)

    def _model(self, user_id, model_name):
        return request.env[model_name].with_user(user_id)

    def _require_estate_user(self, user_id):
        user = self._model(user_id, 'res.users').browse(user_id)
        if not (user.has_group('estate.group_estate_user') or user.has_group('estate.group_estate_manager')):
            raise AccessError('Bạn không có quyền sử dụng API Estate.')

    def _property_payload(self, prop):
        return {
            'id': prop.id,
            'reference': prop.reference,
            'name': prop.name,
            'description': prop.description,
            'expected_price': prop.expected_price,
            'selling_price': prop.selling_price,
            'best_price': prop.best_price,
            'state': prop.state,
            'type': prop.property_type_id.name,
            'salesperson_id': prop.salesperson_id.id,
            'salesperson_name': prop.salesperson_id.display_name,
            'buyer_id': prop.buyer_id.id,
            'buyer_name': prop.buyer_id.display_name,
        }

    # =========================================================
    # Auth
    # =========================================================
    @http.route('/api/v1/auth/login', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def api_login(self, **kwargs):
        params = request.params
        login = params.get('login')
        password = params.get('password')
        db = params.get('db', request.db)

        if not login or not password:
            return {
                'status': 'error',
                'message': 'Thiếu login/password',
                'data': None,
                'errors': ['login/password required'],
                'meta': {},
            }

        try:
            uid = request.session.authenticate(db, login, password)
            if not uid:
                return {
                    'status': 'error',
                    'message': 'Sai tài khoản hoặc mật khẩu',
                    'data': None,
                    'errors': ['invalid_credentials'],
                    'meta': {},
                }

            param = request.env['ir.config_parameter'].sudo()
            secret = param.get_param('estate.jwt_secret') or 'default-secret-key-123'
            expiry_hours = int(param.get_param('estate.jwt_expiry') or 24)

            payload = {
                'user_id': uid,
                'user_login': login,
                'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
                'iat': datetime.utcnow(),
            }
            token = jwt.encode(payload, str(secret), algorithm='HS256')

            return {
                'status': 'success',
                'message': 'Đăng nhập thành công',
                'data': {
                    'access_token': token,
                    'expires_in': expiry_hours * 3600,
                    'user_id': uid,
                },
                'errors': [],
                'meta': {},
            }
        except Exception as exc:
            _logger.exception('Login error: %s', exc)
            return {
                'status': 'error',
                'message': 'Lỗi đăng nhập hệ thống',
                'data': None,
                'errors': ['internal_error'],
                'meta': {},
            }

    # =========================================================
    # Properties CRUD
    # =========================================================
    @http.route('/api/v1/properties', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def list_properties(self, **kwargs):
        return self._execute_secured(self._list_properties, **kwargs)

    def _list_properties(self, user_id, **kwargs):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        domain = [('active', '=', True)]
        if kwargs.get('state'):
            domain.append(('state', '=', kwargs['state']))
        if kwargs.get('min_price'):
            domain.append(('expected_price', '>=', float(kwargs['min_price'])))
        if kwargs.get('max_price'):
            domain.append(('expected_price', '<=', float(kwargs['max_price'])))
        if kwargs.get('salesperson_id'):
            domain.append(('salesperson_id', '=', int(kwargs['salesperson_id'])))

        limit = int(kwargs.get('limit', 20))
        offset = int(kwargs.get('offset', 0))
        order = kwargs.get('sort', 'id desc')

        total = property_model.search_count(domain)
        records = property_model.search(domain, limit=limit, offset=offset, order=order)
        data = [self._property_payload(rec) for rec in records]

        return self._ok(
            data=data,
            message='Lấy danh sách thành công',
            meta={
                'total': total,
                'limit': limit,
                'offset': offset,
                'returned': len(data),
            },
        )

    @http.route('/api/v1/properties/<int:pid>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_property(self, pid, **kwargs):
        return self._execute_secured(self._get_property, pid)

    def _get_property(self, user_id, pid):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        prop = property_model.browse(pid)
        if not prop.exists():
            return self._error('Không tìm thấy bất động sản', status=404)

        data = self._property_payload(prop)
        data['offers'] = [{
            'id': o.id,
            'price': o.price,
            'status': o.status,
            'partner_id': o.partner_id.id,
            'partner_name': o.partner_id.display_name,
            'date_deadline': o.date_deadline,
        } for o in prop.offer_ids]

        return self._ok(data=data, message='Lấy chi tiết thành công')

    @http.route('/api/v1/properties', type='http', auth='public', methods=['POST'], csrf=False)
    def create_property(self, **kwargs):
        return self._execute_secured(self._create_property)

    def _create_property(self, user_id):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        body = self._parse_json_body()
        vals = {
            'name': body.get('name'),
            'expected_price': body.get('expected_price'),
            'description': body.get('description'),
            'salesperson_id': body.get('salesperson_id') or user_id,
        }
        if not vals['name'] or vals['expected_price'] is None:
            raise ValidationError('Thiếu trường bắt buộc: name, expected_price.')
        if body.get('image_base64'):
            vals['image'] = body['image_base64']

        prop = property_model.create(vals)
        return self._ok(data={'id': prop.id, 'reference': prop.reference}, message='Tạo bất động sản thành công', status=201)

    @http.route('/api/v1/properties/<int:pid>', type='http', auth='public', methods=['PUT'], csrf=False)
    def update_property(self, pid, **kwargs):
        return self._execute_secured(self._update_property, pid)

    def _update_property(self, user_id, pid):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        prop = property_model.browse(pid)
        if not prop.exists():
            return self._error('Không tìm thấy bất động sản', status=404)

        body = self._parse_json_body()
        allowed_fields = {'name', 'description', 'expected_price', 'salesperson_id', 'postcode', 'bedrooms', 'living_area'}
        vals = {k: v for k, v in body.items() if k in allowed_fields}
        if not vals:
            raise ValidationError('Không có trường hợp lệ để cập nhật.')

        prop.write(vals)
        return self._ok(data={'id': prop.id}, message='Đã cập nhật')

    @http.route('/api/v1/properties/<int:pid>', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_property(self, pid, **kwargs):
        return self._execute_secured(self._delete_property, pid)

    def _delete_property(self, user_id, pid):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        prop = property_model.browse(pid)
        if not prop.exists():
            return self._error('Không tìm thấy bất động sản', status=404)
        prop.unlink()
        return self._ok(message='Đã xóa')

    # =========================================================
    # Business action API
    # =========================================================
    @http.route('/api/v1/properties/<int:pid>/action/sold', type='http', auth='public', methods=['POST'], csrf=False)
    def mark_property_sold(self, pid, **kwargs):
        return self._execute_secured(self._mark_property_sold, pid)

    def _mark_property_sold(self, user_id, pid):
        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        prop = property_model.browse(pid)
        if not prop.exists():
            return self._error('Không tìm thấy bất động sản', status=404)

        prop.action_sold()
        return self._ok(data={'id': prop.id, 'state': prop.state}, message='Đã chuyển trạng thái Đã bán')

    @http.route('/api/v1/offers/<int:oid>/action/accept', type='http', auth='public', methods=['POST'], csrf=False)
    def offer_accept(self, oid, **kwargs):
        return self._execute_secured(self._offer_action, oid, 'accept')

    @http.route('/api/v1/offers/<int:oid>/action/refuse', type='http', auth='public', methods=['POST'], csrf=False)
    def offer_refuse(self, oid, **kwargs):
        return self._execute_secured(self._offer_action, oid, 'refuse')

    def _offer_action(self, user_id, oid, action_type):
        self._require_estate_user(user_id)
        offer_model = self._model(user_id, 'estate.property.offer')

        offer = offer_model.browse(oid)
        if not offer.exists():
            return self._error('Không tìm thấy đề nghị', status=404)

        if action_type == 'accept':
            offer.action_accept()
        else:
            offer.action_refuse()

        return self._ok(
            data={
                'offer_id': offer.id,
                'status': offer.status,
                'property_id': offer.property_id.id,
                'property_state': offer.property_id.state,
            },
            message='Thực hiện thao tác %s thành công' % action_type,
        )

    # =========================================================
    # Binary image endpoint
    # =========================================================
    @http.route('/api/v1/properties/<int:pid>/image', type='http', auth='public', methods=['GET'], csrf=False)
    def get_image(self, pid, **kwargs):
        user_id, auth_error = self._auth_with_jwt()
        if auth_error:
            return auth_error

        self._require_estate_user(user_id)
        property_model = self._model(user_id, 'estate.property')

        prop = property_model.browse(pid)
        if not prop.exists() or not prop.image:
            return self._error('Không có ảnh', status=404)

        image_data = base64.b64decode(prop.image)
        return request.make_response(
            image_data,
            headers=[('Content-Type', 'image/png'), ('Content-Length', str(len(image_data)))],
        )


class EstateJsonAPI(http.Controller):
    @http.route('/api/json/properties/list', type='json', auth='public', csrf=False, cors='*')
    def list_properties_json(self, **kwargs):
        properties = request.env['estate.property'].sudo().search_read([], ['reference', 'name', 'expected_price'])
        return {'status': 'success', 'data': properties}
