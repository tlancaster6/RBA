"""code for managing real-time email notifications"""
import time
import datetime as dt

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, Content)
import logging
import base64
import os
logger = logging.getLogger(__name__)

class Notification:

    def __init__(self, subject, message, attachment_path=None):
        self.subject, self.message, self.attachment_path = subject, message, attachment_path
        self.time = dt.datetime.now().isoformat()

    def as_mail(self, from_email, to_email):
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=self.subject,
            html_content=Content('text/plain', self.message)
        )
        if self.attachment_path is not None:
            self.attachment_path = str(self.attachment_path)
            with open(self.attachment_path, 'rb') as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            attachment.file_type = FileType(f'application/{self.attachment_path.split(".")[-1]}')
            attachment.file_name = FileName(os.path.basename(self.attachment_path))
            attachment.disposition = Disposition('attachment')
            mail.attachment = attachment
        return mail


class Notifier:

    def __init__(self, user_email, from_email, api_key, admin_email, min_notification_interval=600, max_notifications_per_day=20):
        logger.debug('Beginning Notifier initialization')
        self.user_email, self.from_email, self.admin_email, self.api_key = user_email, from_email, admin_email, api_key
        self.disabled_flag = (self.user_email is None) or (self.api_key is None)
        self.min_notification_interval = min_notification_interval
        self.last_notification_timestamp = 0
        self.max_notifications_per_day = max_notifications_per_day
        self.notification_count = 0
        if self.disabled_flag:
            logger.info('Notifier initialized in light mode. To enable email notifications, provide values for '
                        'both the "api_key" and "user_email" parameters in the project config file.')
        else:
            self.api_client = SendGridAPIClient(api_key)
            logger.debug('Notifier successfully initialized')

    def notify(self, notification: Notification, override_checks=False):
        if self.disabled_flag:
            logger.debug('ignoring notification call because notifier is in light mode')
            return
        if override_checks or self.check_conditions():
            self.send_user_email(notification)

    def send_user_email(self, notification: Notification):
        mail = notification.as_mail(self.from_email, self.user_email)
        try:
            response = self.api_client.send(mail)
        except Exception as e:
            logger.warning(f'unexpected error during notification: {e}')
            return
        if str(response.status_code) == '202':
            logger.debug('notification appears to have sent successfully')
            self.notification_count += 1
            self.last_notification_timestamp = time.time()
        else:
            logger.warning(f'Expected response status code 202 from sendgrid api, got {response.status_code}. '
                           f'Email notification likely failed')

    def send_admin_email(self, notification: Notification):
        if self.admin_email is not None:
            mail = notification.as_mail(self.from_email, self.admin_email)
            try:
                response = self.api_client.send(mail)
            except Exception as e:
                logger.warning(f'unexpected error during notification: {e}')
                return
            if str(response.status_code) == '202':
                logger.debug('notification appears to have sent successfully')
                self.notification_count += 1
                self.last_notification_timestamp = time.time()
            else:
                logger.warning(f'Expected response status code 202 from sendgrid api, got {response.status_code}. '
                               f'Email notification likely failed')
        else:
            logger.debug('admin email not found. skipping.')


    def check_conditions(self):
        logger.debug('checking notification conditions')
        if (time.time() - self.last_notification_timestamp) < self.min_notification_interval:
            logger.debug('min notification interval has not elapsed, rejecting notification request')
            return False
        if self.notification_count >= self.max_notifications_per_day:
            logger.debug('max notifications per day reached, rejecting notification request')
            return False
        logger.debug('all conditions passed')
        return True

    def reset(self):
        self.notification_count = 0
        self.last_notification_timestamp = 0


