from odoo import models, fields, api
import os
import logging
import csv
from odoo.exceptions import UserError, ValidationError
import dateutil.parser

_logger = logging.getLogger(__name__)

class Device(models.Model):
    _name = 'codeforward.device'
    _description = 'Device Information'

    device_id = fields.Integer(string='ID', required=True)
    name = fields.Char(string='Name', required=True, size=32)
    description = fields.Text(string='Description', required=True, size=128)
    code = fields.Char(string='Code', required=True, size=30)
    expire_date = fields.Date(string='Expire Date', required=True)
    state = fields.Selection(string='State', selection=[('enabled', 'Enabled'), ('disabled', 'Disabled'), ('deleted', 'Deleted')], required=True, default='enabled')
    content_ids = fields.One2many('codeforward.device.content', 'device_id', string='Content')

    # Check if code and id are unique
    _sql_constraints = [
        ('code_uniq', 'unique(code)', "Device with given code already exists!"),
        ('device_id_uniq', 'unique(device_id)', "Device with given ID already exists!")
    ]

    # Check if expire_date is in the future
    #@api.model
    def create(self, vals):
        _logger.debug(f"Creating device with vals: {vals}")

        expire_date_str = vals.get('expire_date')

        if expire_date_str:
            expire_date = fields.Date.to_date(expire_date_str)
            today = fields.Date.today()

            if expire_date < today:
                _logger.info(f"Expire date {expire_date} is in the past. Setting state to 'disabled'.")
                vals['state'] = 'disabled'
            else:
                 pass

        new_device = super(Device, self).create(vals)

        return new_device

    @api.model
    def _run_csv_import(self):
        params = self.env['ir.config_parameter'].sudo()
        csv_directory = params.get_param('codeforward.csv_directory', default=False)
        delimiter = params.get_param('codeforward.csv_delimiter', default=',')

        #failed_devices = []
        #failed_contents = []
        #processed_devices = 0
        #processed_contents = 0

        if not csv_directory:
            _logger.error("[CSV Import] Aborted: CSV directory path is not configured in settings.")
            raise UserError("CSV Import directory not set in CodeForward settings.")
        elif not os.path.isdir(csv_directory):
            _logger.error(f"[CSV Import] Aborted: Configured directory path '{csv_directory}' does not exist or is not a directory.")
            raise UserError(f"Configured CSV Import directory '{csv_directory}' not found or is not a directory.")
        if not delimiter:
            _logger.warning("[CSV Import] CSV delimiter not configured, defaulting to ','.")
            delimiter = ','

        devices_path = os.path.join(csv_directory, 'devices.csv')
        content_path = os.path.join(csv_directory, 'content.csv')

        # Process devices
        _logger.info(f"[CSV Import] Attempting to process devices file: {devices_path}")
        if not os.path.exists(devices_path):
            _logger.error(f"[CSV Import] Devices file not found at: {devices_path}")
            raise UserError(f"Required devices file not found: {devices_path}")
        else:
            try:
                with open(devices_path, mode='r') as file:
                    reader = csv.reader(file, delimiter=delimiter)

                    # Process rows
                    for i, row in enumerate(reader):
                        line_num = i + 1 # Start from 1
                        _logger.info(f"[CSV Import] Processing devices.csv line {line_num}: {row}")
                        try:
                            # Check if row has expected number of columns
                            if len(row) < 6:
                                _logger.warning(f"[CSV Import] Skipping devices.csv line {line_num} due to insufficient columns (expected 6, got {len(row)}): {row}")
                                continue

                            # Columns by index
                            device_id_str = row[0].strip()
                            name = row[1].strip()
                            description = row[2].strip()
                            code = row[3].strip()
                            expire_date_str = row[4].strip()
                            state = row[5].strip().lower()

                            # Requried fields
                            if not device_id_str or not name or not description or not code or not expire_date_str or not state:
                                _logger.warning(f"[CSV Import] Skipping devices.csv line {line_num} due to missing required fields (ID, Name, Description, Code, Expire Date, State): {row}")
                                continue

                            # Parse ID
                            try:
                                device_id = int(device_id_str)
                            except ValueError:
                                _logger.warning(f"[CSV Import] Skipping devices.csv line {line_num} due to invalid ID format ('{device_id_str}'). Row: {row}")
                                continue

                            # Parse Date (YYYY-MM-DD)
                            try:
                                date_only_str = expire_date_str.strip().split(' ')[0]
                                expire_date = dateutil.parser.parse(date_only_str).date()
                            except (ValueError, IndexError) as date_err:
                                _logger.warning(f"[CSV Import] Skipping devices.csv line {line_num} due to invalid date format or structure ('{expire_date_str}'): {date_err}. Row: {row}")
                                continue

                            # State validation, catches double dates in devices.csv
                            # Constructor will handle date in past to switch them to disabled again
                            # Only deleted devices will be "lost" by being set to enabled or disabled
                            valid_states = ['enabled', 'disabled', 'deleted']
                            if state not in valid_states:
                                _logger.warning(f"[CSV Import] Invalid state '{state}' on devices.csv line {line_num}. Setting to 'enabled'. Row: {row}")
                                state = 'enabled'

                            vals = {
                                'device_id': device_id,
                                'name': name,
                                'description': description,
                                'code': code,
                                'expire_date': expire_date,
                                'state': state,
                            }


                            _logger.info(f"[CSV Import] Creating new device (Code: {code}, ID: {device_id}) from devices.csv line {line_num}.")
                            try:
                                self.env['codeforward.device'].create(vals)
                            except ValidationError as val_err:
                                _logger.error(f"[CSV Import] Validation Error creating device (Code: {code}) from devices.csv line {line_num}: {val_err}. Vals: {vals}")
                                self.env.cr.rollback()
                            except Exception as create_err:
                                _logger.error(f"[CSV Import] Error creating device (Code: {code}) from devices.csv line {line_num}: {create_err}. Vals: {vals}", exc_info=True)
                                self.env.cr.rollback()

                            self.env.cr.commit()

                        except ValueError as ve:
                             _logger.error(f"[CSV Import] Data Error processing devices.csv line {line_num}: {ve}. Row: {row}", exc_info=True)
                             self.env.cr.rollback()
                        except Exception as row_err:
                            _logger.error(f"[CSV Import] Unexpected Error processing devices.csv line {line_num}: {row_err}. Row: {row}", exc_info=True)
                            self.env.cr.rollback()

            except csv.Error as csv_err:
                _logger.error(f"[CSV Import] CSV parsing error in devices file {devices_path}: {csv_err}", exc_info=True)
                raise UserError(f"Error reading devices CSV file: {csv_err}")
            except Exception as e:
                _logger.error(f"[CSV Import] Unexpected error during devices file processing: {e}", exc_info=True)
                raise UserError(f"An unexpected error occurred processing {devices_path}")


        # Process content
        _logger.info(f"[CSV Import] Attempting to process content file: {content_path}")
        if not os.path.exists(devices_path):
            _logger.error(f"[CSV Import] Content file not found at: {content_path}")
            raise UserError(f"Required content file not found: {content_path}")
        else:
            try:
                with open(content_path, mode='r') as file:
                    reader = csv.reader(file, delimiter=delimiter)

                    # Process rows
                    for i, row in enumerate(reader):
                        line_num = i + 1 # Start from 1
                        _logger.info(f"[CSV Import] Processing content.csv line {line_num}: {row}")
                        try:
                            # Check if row has expected number of columns
                            if len(row) < 6:
                                _logger.warning(f"[CSV Import] Skipping content.csv line {line_num} due to insufficient columns (expected 6, got {len(row)}): {row}")
                                continue

                            # Columns by index
                            content_id_str = row[0].strip()
                            name = row[1].strip()
                            description = row[2].strip()
                            device_id = row[3].strip()
                            expire_date_str = row[4].strip()
                            state = row[5].strip().lower()

                            # Requried fields
                            if not content_id_str or not name or not description or not device_id or not expire_date_str or not state:
                                _logger.warning(f"[CSV Import] Skipping content.csv line {line_num} due to missing required fields (ID, Name, Description, Device, Expire Date, State): {row}")
                                continue

                            # Parse ID
                            try:
                                content_id = int(content_id_str)
                            except ValueError:
                                _logger.warning(f"[CSV Import] Skipping content.csv line {line_num} due to invalid ID format ('{content_id_str}'). Row: {row}")
                                continue

                            # Parse Date (YYYY-MM-DD)
                            try:
                                date_only_str = expire_date_str.strip().split(' ')[0]
                                expire_date = dateutil.parser.parse(date_only_str).date()
                            except (ValueError, IndexError) as date_err:
                                _logger.warning(f"[CSV Import] Skipping content.csv line {line_num} due to invalid date format or structure ('{expire_date_str}'): {date_err}. Row: {row}")
                                continue

                            # State validation, catches double dates in devices.csv
                            # Constructor will handle date in past to switch them to disabled again
                            # Only deleted devices will be "lost" by being set to enabled or disabled
                            valid_states = ['enabled', 'disabled', 'deleted']
                            if state not in valid_states:
                                _logger.warning(f"[CSV Import] Invalid state '{state}' on content.csv line {line_num}. Setting to 'enabled'. Row: {row}")
                                state = 'enabled'

                            device = self.env['codeforward.device'].search([('device_id', '=', int(device_id))], limit=1)
                            if not device:
                                _logger.warning(f"Device with ID {device_id} not found for content line {line_num}")
                                continue

                            vals = {
                                'content_id': content_id,
                                'name': name,
                                'description': description,
                                'device_id': device.id,
                                'expire_date': expire_date,
                                'state': state,
                            }


                            _logger.info(f"[CSV Import] Creating new content (ID: {content_id}, Device: {device_id}) from content.csv line {line_num}.")
                            try:
                                self.env['codeforward.device.content'].create(vals)
                            except ValidationError as val_err:
                                _logger.error(f"[CSV Import] Validation Error creating content (Code: {content_id}) from content.csv line {line_num}: {val_err}. Vals: {vals}")
                                self.env.cr.rollback()
                            except Exception as create_err:
                                _logger.error(f"[CSV Import] Error creating content (Code: {content_id}) from content.csv line {line_num}: {create_err}. Vals: {vals}", exc_info=True)
                                self.env.cr.rollback()

                            self.env.cr.commit()

                        except ValueError as ve:
                             _logger.error(f"[CSV Import] Data Error processing content.csv line {line_num}: {ve}. Row: {row}", exc_info=True)
                             self.env.cr.rollback()
                        except Exception as row_err:
                            _logger.error(f"[CSV Import] Unexpected Error processing content.csv line {line_num}: {row_err}. Row: {row}", exc_info=True)
                            self.env.cr.rollback()

            except csv.Error as csv_err:
                _logger.error(f"[CSV Import] CSV parsing error in content file {content_path}: {csv_err}", exc_info=True)
                raise UserError(f"Error reading content CSV file: {csv_err}")
            except Exception as e:
                _logger.error(f"[CSV Import] Unexpected error during content file processing: {e}", exc_info=True)
                raise UserError(f"An unexpected error occurred processing {content_path}")

        _logger.info("[CSV Import] CSV import process finished.")
        return True