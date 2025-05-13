from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    codeforward_csv_directory = fields.Char(
        string='CSV Directory Path',
        config_parameter='codeforward.csv_directory',
        default='/mnt/csv_files',
        help="The local path to the directory containing devices.csv and content.csv"
    )
    codeforward_csv_delimiter = fields.Char(
        string='CSV Delimiter',
        config_parameter='codeforward.csv_delimiter',
        default=',',
        help="The delimiter to use in the CSV files (default is comma).",
        size=1
    ) 