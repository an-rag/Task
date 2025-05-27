{
    'name': 'Sale Order Customisation',
    'version': '17.0.0.0.1',
    "summary": """ Sales Customization""",
    "description": """Sales Customization""",
    'category': 'Sales',
    'depends': ['sale'],
    'data': [
        'data/data.xml',
        'views/sale_order.xml',
        'views/res_config_setting.xml',
    ],
    "license": "OPL-1",
    "installable": True,
    "application": False,
}