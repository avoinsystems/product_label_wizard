# -*- coding: utf-8 -*-
#
#    Copyright (C) 2017 Avoin Systems (<https://avoin.systems>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# noinspection PyProtectedMember
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class ProductLabelWizard(models.TransientModel):
    # region Private attributes
    _name = 'product.label.wizard'
    _description = 'Product Label Wizard'
    # endregion

    # region Defaults
    @api.model
    def default_get(self, fieldz):
        res = super(ProductLabelWizard, self).default_get(fieldz)

        model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')
        line_model = self.env['product.label.wizard.line']

        if model == 'product.product':
            res['product_label_lines'] = [
                line_model.create({'product_id': active_id,
                                   'number_of_labels': 1}).id
                for active_id in active_ids
            ]
        elif model == 'product.template':
            templates = self.env['product.template'].browse(active_ids)
            res['product_label_lines'] = [
                line_model.create({'product_id': variant.id,
                                   'number_of_labels': 1}).id
                for variant in templates.mapped('product_variant_ids')
            ]
        elif model == 'stock.picking':
            # Loosely coupled, this module has no dependency to stock.
            pickings = self.env['stock.picking'].browse(active_ids)
            res['product_label_lines'] = [
                line_model.create({'product_id': move.product_id.id,
                                   'number_of_labels': move.product_uom_qty}
                                  ).id
                for move in pickings.mapped('move_lines')
            ]

        return res
    # endregion

    # region Fields declaration
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
        change_default=True,
        required=True,
    )

    product_label_lines = fields.One2many(
        'product.label.wizard.line',
        'wizard_id',
        'Products',
    )
    # endregion


class ProductLabelWizardLine(models.TransientModel):
    # region Private attributes
    _name = 'product.label.wizard.line'
    _description = 'Product Label Wizard Line'
    # endregion

    # region Fields declaration
    wizard_id = fields.Many2one(
        'product.label.wizard.line',
        'Wizard',
    )

    product_id = fields.Many2one(
        'product.product',
        'Product',
        required=True,
    )

    number_of_labels = fields.Integer(
        'Number of Labels',
        default=1,
        required=True,
    )
    # endregion

    # region Constraints and onchanges
    @api.constrains('number_of_labels')
    def _validate_number_of_labels(self):
        for line in self:
            if line.number_of_labels < 0:
                raise ValidationError(
                    _(u"The number of labels can't be negative")
                )
    # endregion
