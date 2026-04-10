# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestEstateFlow(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Buyer Test'})
        cls.property_type = cls.env['estate.property.type'].create({'name': 'Type Test'})

    def test_offer_accept_flow(self):
        property_rec = self.env['estate.property'].create({
            'name': 'Property Test 01',
            'expected_price': 1000000,
            'property_type_id': self.property_type.id,
        })
        self.assertTrue(property_rec.reference)
        self.assertEqual(property_rec.state, 'new')

        offer = self.env['estate.property.offer'].create({
            'price': 950000,
            'partner_id': self.partner.id,
            'property_id': property_rec.id,
        })
        self.assertEqual(property_rec.state, 'offer_received')

        offer.action_accept()
        self.assertEqual(offer.status, 'accepted')
        self.assertEqual(property_rec.state, 'offer_accepted')
        self.assertEqual(property_rec.selling_price, 950000)

        property_rec.action_sold()
        self.assertEqual(property_rec.state, 'sold')

    def test_offer_below_90_percent_should_fail(self):
        property_rec = self.env['estate.property'].create({
            'name': 'Property Test 02',
            'expected_price': 1000000,
            'property_type_id': self.property_type.id,
        })

        offer = self.env['estate.property.offer'].create({
            'price': 800000,
            'partner_id': self.partner.id,
            'property_id': property_rec.id,
        })

        with self.assertRaises(ValidationError):
            offer.action_accept()
