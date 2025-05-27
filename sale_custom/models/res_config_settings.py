from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"


    sale_order_limit = fields.Float(
        config_parameter='sale_custom.sale_order_limit',
        string="Sale Order Limit",
        default=0,
    )