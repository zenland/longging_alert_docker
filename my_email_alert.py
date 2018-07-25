from smtplib import SMTP
from smtplib import SMTP_SSL
from smtplib import SMTPAuthenticationError
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.utils import formatdate
from HTMLParser import HTMLParser
from socket import error
from elastalert.util import EAException
from elastalert.util import elastalert_logger
from elastalert.util import lookup_es_key
from elastalert.util import pretty_ts
from elastalert.util import resolve_string
from elastalert.util import ts_now
from elastalert.util import ts_to_dt

import json
import requests
from elastalert.alerts import Alerter, DateTimeEncoder
from requests.exceptions import RequestException
from elastalert.util import EAException

class EmailAlerter(Alerter):
    """ Sends an email alert """
    required_options = frozenset(['email'])

    def __init__(self, *args):
        super(EmailAlerter, self).__init__(*args)

        self.smtp_host = self.rule.get('smtp_host', 'localhost')
        self.smtp_ssl = self.rule.get('smtp_ssl', False)
        self.from_addr = self.rule.get('from_addr', 'ElastAlert')
        self.smtp_port = self.rule.get('smtp_port')
        if self.rule.get('smtp_auth_file'):
            self.get_account(self.rule['smtp_auth_file'])
        self.smtp_key_file = self.rule.get('smtp_key_file')
        self.smtp_cert_file = self.rule.get('smtp_cert_file')
        # Convert email to a list if it isn't already
        if isinstance(self.rule['email'], basestring):
            self.rule['email'] = [self.rule['email']]
        # If there is a cc then also convert it a list if it isn't
        cc = self.rule.get('cc')
        if cc and isinstance(cc, basestring):
            self.rule['cc'] = [self.rule['cc']]
        # If there is a bcc then also convert it to a list if it isn't
        bcc = self.rule.get('bcc')
        if bcc and isinstance(bcc, basestring):
            self.rule['bcc'] = [self.rule['bcc']]
        add_suffix = self.rule.get('email_add_domain')
        if add_suffix and not add_suffix.startswith('@'):
            self.rule['email_add_domain'] = '@' + add_suffix

    def my_create_alert_body(self,matches):
        body=''
        index=0
        body+='<table>'
        body+='<tr><td colspan="2"><b>From staging environment</b></td></tr>'
        body+='<tr><td colspan="2"><b>===================</b></td></tr>'
        for match in matches:
           body+='<tr><td><b>k8s:host: </b></td><td>'+str(match['k8s:host'])+'</tr>'
           if match.has_key('k8s:app'):
               body+='<tr><td><b>k8s:app: </b></td><td>'+str(match['k8s:app'])+'</tr>'
           body+='<tr><td><b>level: </b></td><td>'+str(match['level'])+'</tr>'
           body+='<tr><td><b>message: </b></td><td>'+str(match['message'])+'</td></tr>'
	body+='</table>'
        return body

    def alert(self, matches):
        body = self.my_create_alert_body(matches)

        # Add JIRA ticket if it exists
        if self.pipeline is not None and 'jira_ticket' in self.pipeline:
            url = '%s/browse/%s' % (self.pipeline['jira_server'], self.pipeline['jira_ticket'])
            body += '\nJIRA ticket: %s' % (url)

        to_addr = self.rule['email']
        if 'email_from_field' in self.rule:
            recipient = lookup_es_key(matches[0], self.rule['email_from_field'])
            if isinstance(recipient, basestring):
                if '@' in recipient:
                    to_addr = [recipient]
                elif 'email_add_domain' in self.rule:
                    to_addr = [recipient + self.rule['email_add_domain']]
            elif isinstance(recipient, list):
                to_addr = recipient
                if 'email_add_domain' in self.rule:
                    to_addr = [name + self.rule['email_add_domain'] for name in to_addr]
        if self.rule.get('email_format') == 'html':
            email_msg = MIMEText(body.encode('UTF-8'), 'html', _charset='UTF-8')
        else:
            email_msg = MIMEText(body.encode('UTF-8'), _charset='UTF-8')
        email_msg['Subject'] = self.create_title(matches)
        email_msg['To'] = ', '.join(to_addr)
        email_msg['From'] = self.from_addr
        email_msg['Reply-To'] = self.rule.get('email_reply_to', email_msg['To'])
        email_msg['Date'] = formatdate()
        if self.rule.get('cc'):
            email_msg['CC'] = ','.join(self.rule['cc'])
            to_addr = to_addr + self.rule['cc']
        if self.rule.get('bcc'):
            to_addr = to_addr + self.rule['bcc']

        try:
            if self.smtp_ssl:
                if self.smtp_port:
                    self.smtp = SMTP_SSL(self.smtp_host, self.smtp_port, keyfile=self.smtp_key_file, certfile=self.smtp_cert_file)
                else:
                    self.smtp = SMTP_SSL(self.smtp_host, keyfile=self.smtp_key_file, certfile=self.smtp_cert_file)
            else:
                if self.smtp_port:
                    self.smtp = SMTP(self.smtp_host, self.smtp_port)
                else:
                    self.smtp = SMTP(self.smtp_host)
                self.smtp.ehlo()
                if self.smtp.has_extn('STARTTLS'):
                    self.smtp.starttls(keyfile=self.smtp_key_file, certfile=self.smtp_cert_file)
            if 'smtp_auth_file' in self.rule:
                self.smtp.login(self.user, self.password)
        except (SMTPException, error) as e:
            raise EAException("Error connecting to SMTP host: %s" % (e))
        except SMTPAuthenticationError as e:
            raise EAException("SMTP username/password rejected: %s" % (e))
        self.smtp.sendmail(self.from_addr, to_addr, email_msg.as_string())
        self.smtp.close()

        elastalert_logger.info("Sent email to %s" % (to_addr))

    def create_default_title(self, matches):
        subject = '%s - alert' % (self.rule['name'])

        # If the rule has a query_key, add that value plus timestamp to subject
        if 'query_key' in self.rule:
            qk = matches[0].get(self.rule['query_key'])
            if qk:
                subject += ' - %s' % (qk[0:128])

        return subject

    def get_info(self):
        return {'type': 'email',
                'recipients': self.rule['email']}
