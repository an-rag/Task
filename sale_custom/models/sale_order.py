from odoo import models, fields, api,_
from lxml import etree
from datetime import date
from odoo.exceptions import UserError



class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    manager_reference = fields.Text(string="Manager Reference")
    is_automatic = fields.Boolean(string='Auto Workflow')


    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        views_type = ['list', 'form']
        for type in views_type:
            arch = res['views'].get(type, {}).get('arch')
            if arch:
                doc = etree.fromstring(arch)
                for field in doc.xpath("//field[@name='manager_reference']"):
                    if self.env.user.has_group('sale_custom.group_sale_admin'):
                        field.set('readonly', '0')
                    else:
                        field.set('readonly', '1')
                arch = etree.tostring(doc, encoding='unicode')
                res['views'].setdefault(type, {})['arch'] = arch 
        return res
    
    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for rec in self:
            sale_order_limit = self.env['res.config.settings'].sudo().search([],limit=1).sale_order_limit
            if rec.amount_total > sale_order_limit and not self.env.user.has_group('sale_custom.group_sale_admin'):
                raise UserError(_('Only the Sales Admin is authorized to confirm orders that exceed the limit...'))
            if rec.is_automatic:
                procurement_group = self.procurement_group_id
                rec.picking_ids = False
                product_ids =  rec.order_line.mapped('product_id')
                for lines in product_ids:
                    quantity = sum(rec.order_line.filtered(lambda l:l.product_id.id ==lines.id).mapped('product_uom_qty'))
                    stock_picking = self.env['stock.picking']
                    picking_type_id = self.env['stock.picking.type'].search([('code','=','outgoing')],limit="1")
                    dest_location = self.env['stock.location'].search([('usage','=','customer')],limit="1")
                    source_location = self.env['stock.picking.type'].search([('warehouse_id','=',rec.warehouse_id.id),('code', '=', 'outgoing')]).default_location_src_id
                    order1_vals = {
                                    "product_id": lines.id,
                                    "name" : lines.name,
                                    "product_uom" : lines.uom_id.id,
                                    "product_uom_qty" : quantity,
                                    "quantity" : quantity,
                                    'group_id': procurement_group.id,
                                    "location_id" : source_location.id,
                                    "location_dest_id" : dest_location.id,
                                    }
                    do_vals = { 'partner_id': rec.partner_id.id,
                                'location_id': source_location.id,
                                'location_dest_id': dest_location.id,
                                'picking_type_id': picking_type_id.id,
                                'group_id': procurement_group.id,
                                'sale_id' : rec.id,
                                'state': 'draft',
                                'move_ids_without_package': [(0, None, order1_vals)]}
                    stock_picking = stock_picking.create(do_vals)
                    stock_picking.action_confirm()
                    stock_picking.action_assign()
                    stock_picking.button_validate()
                invoices = rec._create_invoices()
                invoices.action_post()
                register_payment =self.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoices.ids).create({'payment_date': date.today()})
                action = register_payment.action_create_payments() 
                payment = self.env['account.payment'].browse(action['res_id'])
        return result