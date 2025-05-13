from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class DeviceContent(models.Model):
    _name = 'codeforward.device.content'
    _description = 'Content on Device'

    content_id = fields.Integer(string='ID', required=True)
    name = fields.Char(string='Name', required=True, size=100)
    description = fields.Text(string='Description', required=True, size=128)
    device_id = fields.Many2one('codeforward.device', string='Device', required=True, ondelete='cascade')
    expire_date = fields.Date(string='Expire Date', required=True)
    state = fields.Selection(string='State', selection=[('enabled', 'Enabled'), ('disabled', 'Disabled'), ('deleted', 'Deleted')], required=True, default='enabled')

    # Check if expire_date is in the future
    #@api.model
    def create(self, vals):
            _logger.debug(f"Creating content with vals: {vals}")

            expire_date_str = vals.get('expire_date')

            if expire_date_str:
                expire_date = fields.Date.to_date(expire_date_str)
                today = fields.Date.today()

                if expire_date < today:
                    _logger.info(f"Expire date {expire_date} is in the past. Setting state to 'disabled'.")
                    vals['state'] = 'disabled'
                else:
                     pass

            new_content = super(DeviceContent, self).create(vals)

            return new_content