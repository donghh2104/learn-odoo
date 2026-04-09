# -*- coding: utf-8 -*-
from odoo import http


class MyModule(http.Controller):
    @http.route('/football/', auth='public')
    def index(self, **kw):
        return "Hello, worldsds11"

    @http.route('/football/<int:id>', auth='public', type='http')
    def football_check(self, id):
        return "Football check check check %s" % str(id)

#     @http.route('/my_module/my_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('my_module.listing', {
#             'root': '/my_module/my_module',
#             'objects': http.request.env['my_module.my_module'].search([]),
#         })

#     @http.route('/my_module/my_module/objects/<model("my_module.my_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('my_module.object', {
#             'object': obj
#         })
