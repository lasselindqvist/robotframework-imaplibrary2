#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2015-2016 Richard Huang <rickypc@users.noreply.github.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
IMAP Library - a IMAP email testing library.
"""

from email import message_from_bytes
from email.header import decode_header
from imaplib import IMAP4, IMAP4_SSL
from re import findall
from time import sleep, time

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
from builtins import str as ustr
from ImapLibrary2.version import get_version
from ImapLibrary2.imap_proxy import IMAP4Proxy, IMAP4SSLProxy
import os.path
__version__ = get_version()


class ImapLibrary2(object):
    """ImapLibrary2 is an email testing library for [http://goo.gl/lES6WM|Robot Framework].

    *Deprecated Keywords Warning*

    These keywords will be removed in the future 3 to 5 releases.
    | *Deprecated Keyword*  | *Alternative Keyword*     |
    | `Open Link From Mail` | `Open Link From Email`    |
    | `Mark As Read`        | `Mark All Emails As Read` |
    | `Wait For Mail`       | `Wait For Email`          |

    Example:
    | `Open Mailbox`   | host=imap.domain.com   | user=email@domain.com        | password=secret |
    | ${LATEST} =      | `Wait For Email`       | sender=noreply@domain.com    | timeout=300     |
    | ${HTML} =        | `Open Link From Email` | ${LATEST}                    |                 |
    | `Should Contain` | ${HTML}                | address has been updated     |                 |
    | `Close Mailbox`  |                        |                              |                 |

    Multipart Email Example:
    | `Open Mailbox`   | host=imap.domain.com   | user=email@domain.com        | password=secret |
    | ${LATEST} =      | `Wait For Email`       | sender=noreply@domain.com    | timeout=300     |
    | ${parts} =       | `Walk Multipart Email` | ${LATEST}                    |                 |
    | :FOR             | ${i}                   | IN RANGE                     | ${parts}        |
    | \\               | `Walk Multipart Email` | ${LATEST}                    |                 |
    | \\               | ${ctype} =             | `Get Multipart Content Type` |                 |
    | \\               | `Continue For Loop If` | '${ctype}' != 'text/html'    |                 |
    | \\               | ${payload} =           | `Get Multipart Payload`      | decode=True     |
    | \\               | `Should Contain`       | ${payload}                   | your email      |
    | \\               | ${HTML} =              | `Open Link From Email`       | ${LATEST}       |
    | \\               | `Should Contain`       | ${HTML}                      | Your email      |
    | `Close Mailbox`  |                        |                              |                 |
    """

    PORT = 143
    PORT_SECURE = 993
    FOLDER = 'INBOX'
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self):
        """ImapLibrary2 can be imported without argument.

        Examples:
        | = Keyword Definition =  | = Description =       |
        | Library `|` ImapLibrary2 | Initiate Imap library |
        """
        self._email_index = None
        self._imap = None
        self._mails = []
        self._mp_iter = None
        self._mp_msg = None
        self._part = None

    def close_mailbox(self):
        """Close IMAP email client session.

        Examples:
        | Close Mailbox |
        """
        self._imap.close()

    def delete_all_emails(self):
        """Delete all emails.

        Examples:
        | Delete All Emails |
        """
        self._get_all_emails()
        for mail in self._mails:
            self.delete_email(mail)
        self._imap.expunge()

    def delete_email(self, email_index):
        """Delete email on given ``email_index``.

        Arguments:
        - ``email_index``: An email index to identity the email message.

        Examples:
        | Delete Email | INDEX |
        """
        self._imap.uid('store', email_index, '+FLAGS', r'(\DELETED)')
        self._imap.expunge()

    def get_email_body(self, email_index):
        """Returns the decoded email body on multipart email message,
        otherwise returns the body text.

        Arguments:
        - ``email_index``: An email index to identity the email message.

        Examples:
        | Get Email Body | INDEX |
        """
        if self._is_walking_multipart(email_index):
            body = self.get_multipart_payload(decode=True)
        else:
            encodedMessage = self._imap.uid('fetch', email_index, '(BODY[])')[1][0][1]
            msg = message_from_bytes(encodedMessage)
            if not msg.is_multipart():
                body = msg.get_payload(decode=True).decode()
            else:
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                raise Exception("get_email_body called on multipart email '%s'. Please first use method walk_multipart_email." % (subject))

        return body

    def get_links_from_email(self, email_index):
        """Returns all links found in the email body from given ``email_index``.

        Arguments:
        - ``email_index``: An email index to identity the email message.

        Examples:
        | Get Links From Email | INDEX |
        """
        body = self.get_email_body(email_index)
        return findall(r'href=[\'"]?([^\'" >]+)', body)

    def get_matches_from_email(self, email_index, pattern):
        """Returns all Regular Expression ``pattern`` found in the email body
        from given ``email_index``.

        Arguments:
        - ``email_index``: An email index to identity the email message.
        - ``pattern``: It consists of one or more character literals, operators, or constructs.

        Examples:
        | Get Matches From Email | INDEX | PATTERN |
        """
        body = self.get_email_body(email_index)
        return findall(pattern, body)

    def get_multipart_content_type(self):
        """Returns the content type of current part of selected multipart email message.

        Examples:
        | Get Multipart Content Type |
        """
        return self._part.get_content_type()

    def get_multipart_field(self, field):
        """Returns the value of given header ``field`` name.

        Arguments:
        - ``field``: A header field name: ``From``, ``To``, ``Subject``, ``Date``, etc.
                     All available header field names of an email message can be found by running
                     `Get Multipart Field Names` keyword.

        Examples:
        | Get Multipart Field | Subject |
        """
        return self._mp_msg[field]

    def get_multipart_field_names(self):
        """Returns all available header field names of selected multipart email message.

        Examples:
        | Get Multipart Field Names |
        """
        return list(self._mp_msg.keys())

    def get_multipart_payload(self, decode=False):
        """Returns the payload of current part of selected multipart email message.

        Arguments:
        - ``decode``: An indicator flag to decode the email message. (Default False)

        Examples:
        | Get Multipart Payload |
        | Get Multipart Payload | decode=True |
        """
        payload = self._part.get_payload(decode=decode)
        charset = self._part.get_content_charset()
        if charset is not None:
            return payload.decode(charset)
        return payload

    def mark_all_emails_as_read(self):
        """Mark all received emails as read.

        Examples:
        | Mark All Emails As Read |
        """
        self._get_all_emails()
        for mail in self._mails:
            self._imap.uid('store', mail, '+FLAGS', r'\SEEN')

    def mark_as_read(self):
        """****DEPRECATED****
        Shortcut to `Mark All Emails As Read`.
        """
        self.mark_all_emails_as_read()

    def mark_email_as_read(self, email_index):
        """Mark email on given ``email_index`` as read.

        Arguments:
        - ``email_index``: An email index to identity the email message.

        Examples:
        | Mark Email As Read | INDEX |
        """
        self._imap.uid('store', email_index, '+FLAGS', r'\SEEN')

    def open_link_from_email(self, email_index, link_index=0):
        """Open link URL from given ``link_index`` in email message body of given ``email_index``.
        Returns HTML content of opened link URL.

        Arguments:
        - ``email_index``: An email index to identity the email message.
        - ``link_index``: The link index to be open. (Default 0)

        Examples:
        | Open Link From Email |
        | Open Link From Email | 1 |
        """
        urls = self.get_links_from_email(email_index)

        if len(urls) > link_index:
            resp = urlopen(urls[link_index])
            content_type = resp.headers.get('content-type')
            if content_type:
                enc = content_type.split('charset=')[-1]
                return ustr(resp.read(), enc)
            else:
                return resp.read()
        else:
            raise AssertionError("Link number %i not found!" % link_index)

    def open_link_from_mail(self, email_index, link_index=0):
        """****DEPRECATED****
        Shortcut to `Open Link From Email`.
        """
        return self.open_link_from_email(email_index, link_index)

    def open_mailbox(self, **kwargs):
        """Open IMAP email client session to given ``host`` with given ``user`` and ``password``.

        Arguments:
        - ``host``: The IMAP host server. (Default None)
        - ``is_secure``: An indicator flag to connect to IMAP host securely or not. (Default True)
        - ``password``: The plaintext password to be use to authenticate mailbox on given ``host``.
        - ``port``: The IMAP port number. (Default None)
        - ``user``: The username to be use to authenticate mailbox on given ``host``.
        - ``folder``: The email folder to read from. (Default INBOX)
        - ``proxy_host``: Proxy host to connect via. (Default None)
        - ``proxy_port``: Proxy port to connect via. (Default None)
        - ``proxy_user``: Proxy username to connect via. (Default None)
        - ``proxy_password``: Proxy password to connect via. (Default None)
        - ``proxy_type``: Proxy type to connect via. Available values are: http, socks4, socks5 (Default http)

        Examples:
        | Open Mailbox | host=HOST | user=USER | password=SECRET |
        | Open Mailbox | host=HOST | user=USER | password=SECRET | is_secure=False |
        | Open Mailbox | host=HOST | user=USER | password=SECRET | port=8000 |
        | Open Mailbox | host=HOST | user=USER | password=SECRET | folder=Drafts
        | Open Mailbox | host=HOST | user=USER | password=SECRET | folder=Drafts | proxy_host=ProxyHost | proxy_port=8080 | proxy_username=ProxyUsername | proxy_password=ProxyPassword | proxy_type=http
        """
        host = kwargs.pop('host', kwargs.pop('server', None))
        is_secure = kwargs.pop('is_secure', 'True') == 'True'
        port = int(kwargs.pop('port', self.PORT_SECURE if is_secure else self.PORT))
        folder = '"%s"' % str(kwargs.pop('folder', self.FOLDER))
        proxy_host = kwargs.pop('proxy_host', None)
        proxy_port = kwargs.pop('proxy_port', None)
        proxy_user = kwargs.pop('proxy_user', None)
        proxy_password = kwargs.pop('proxy_password', None)
        proxy_type = kwargs.pop('proxy_type', 'http')
        if proxy_host != None and proxy_port != None:
            if is_secure:
                self._imap = IMAP4SSLProxy(
                                host=host,
                                port=port,
                                proxy_host=proxy_host,
                                proxy_port=int(proxy_port),
                                proxy_type=proxy_type)
            else:
                self._imap = IMAP4Proxy(
                                host=host,
                                port=port,
                                proxy_host=proxy_host,
                                proxy_port=int(proxy_port),
                                proxy_type=proxy_type)
        else:
            self._imap = IMAP4_SSL(host, port) if is_secure else IMAP4(host, port)
        self._imap.login(kwargs.pop('user', None), kwargs.pop('password', None))
        self._imap.select(folder)
        self._init_multipart_walk()

    def open_mailbox_oauth(self, **kwargs):
        """Open IMAP email client session to oauth provider with given ``user`` and ``access_token``.
        Arguments:
        - ``host``: The IMAP host server. (Default None)
        - ``debug_level``: An integer from 0 to 5 where 0 disables debug output and 5 enables full output with wire logging and parsing logs. (Default 0)
        - ``folder``: The email folder to read from. (Default INBOX)
        - ``user``: The username (email address) of the account to authenticate.
        - ``access_token``: An OAuth2 access token. Must not be base64-encoded, since imaplib does its own base64-encoding.

        Examples:
        | Open Mailbox | host=HOST | debug_level=2 | user=email@gmail.com | access_token=SECRET |
        | Open Mailbox | host=HOST | debug_level=0 | user=email@gmail.com | access_token=SECRET | folder=Drafts
        """
        host = kwargs.pop('host', kwargs.pop('server', None))
        debug_level = int(kwargs.pop('debug_level', 0))
        folder = '"%s"' % str(kwargs.pop('folder', self.FOLDER))
        user = str(kwargs.pop('user', None))
        access_token = str(kwargs.pop('access_token', None))
        access_string = 'user=%s\1auth=Bearer %s\1\1' % (user, access_token)
        self._imap = IMAP4_SSL(host)
        self._imap.debug = debug_level
        self._imap.authenticate('XOAUTH2', lambda x: access_string)
        self._imap.select(folder)
        self._init_multipart_walk()

    def wait_for_email(self, **kwargs):
        """Wait for email message to arrived base on any given filter criteria.
        Returns email index of the latest email message received.

        Arguments:
        - ``poll_frequency``: The delay value in seconds to retry the mailbox check. (Default 10)
        - ``recipient``: Email recipient. (Default None)
        - ``sender``: Email sender. (Default None)
        - ``status``: A mailbox status filter: ``MESSAGES``, ``RECENT``, ``UIDNEXT``,
                      ``UIDVALIDITY``, and ``UNSEEN``.
                      Please see [https://goo.gl/3KKHoY|Mailbox Status] for more information.
                      (Default None)
        - ``subject``: Email subject. (Default None)
        - ``text``: Email body text. (Default None)
        - ``timeout``: The maximum value in seconds to wait for email message to arrived.
                       (Default 60)
        - ``folder``: The email folder to check for emails. (Default INBOX)

        Examples:
        | Wait For Email | sender=noreply@domain.com |
        | Wait For Email | sender=noreply@domain.com | folder=OUTBOX
        """
        poll_frequency = float(kwargs.pop('poll_frequency', 10))
        timeout = int(kwargs.pop('timeout', 60))
        end_time = time() + timeout
        while time() < end_time:
            self._mails = self._check_emails(**kwargs)
            if len(self._mails) > 0:
                return self._mails[-1]
            if time() < end_time:
                sleep(poll_frequency)
        raise AssertionError("No email received within %ss" % timeout)

    def wait_for_mail(self, **kwargs):
        """****DEPRECATED****
        Shortcut to `Wait For Email`.
        """
        return self.wait_for_email(**kwargs)

    def walk_multipart_email(self, email_index):
        """Returns total parts of a multipart email message on given ``email_index``.
        Email message is cache internally to be used by other multipart keywords:
        `Get Multipart Content Type`, `Get Multipart Field`, `Get Multipart Field Names`,
        `Get Multipart Field`, and `Get Multipart Payload`.

        Arguments:
        - ``email_index``: An email index to identity the email message.

        Examples:
        | Walk Multipart Email | INDEX |
        """
        if not self._is_walking_multipart(email_index):
            data = self._imap.uid('fetch', email_index, '(RFC822)')[1][0][1]
            msg = message_from_bytes(data)
            self._start_multipart_walk(email_index, msg)
        try:
            self._part = next(self._mp_iter)
        except StopIteration:
            self._init_multipart_walk()
            return False
        # return number of parts
        return len(self._mp_msg.get_payload())

    def get_email_count(self, **kwargs):
        return len(self._check_emails(**kwargs))

    def _check_emails(self, **kwargs):
        """Returns filtered email."""
        folder = '"%s"' % str(kwargs.pop('folder', self.FOLDER))
        criteria = self._criteria(**kwargs)
        # Calling select before each search is necessary with gmail
        status, data = self._imap.select(folder)
        if status != 'OK':
            raise Exception("imap.select error: %s, %s" % (status, data))
        subject = kwargs.pop('subject', None)
        if subject:
            self._imap.literal = subject.encode("utf-8")
        typ, msgnums = self._imap.uid('search', None, *criteria)
        if typ != 'OK':
            raise Exception('imap.search error: %s, %s, criteria=%s' % (typ, msgnums, criteria))
        if msgnums[0] is not None:
            if type(msgnums[0]) != bytes:
                return msgnums[0]
            return msgnums[0].split()
        else:
            return []

    @staticmethod
    def _criteria(**kwargs):
        """Returns email criteria."""
        criteria = []
        recipient = kwargs.pop('recipient', kwargs.pop('to_email', kwargs.pop('toEmail', None)))
        sender = kwargs.pop('sender', kwargs.pop('from_email', kwargs.pop('fromEmail', None)))
        cc = kwargs.pop('cc', kwargs.pop('cc_email', kwargs.pop('ccEmail', None)))
        status = kwargs.pop('status', None)
        subject = kwargs.pop('subject', None)
        text = kwargs.pop('text', None)
        if recipient:
            criteria += ['TO', '"%s"' % recipient]
        if sender:
            criteria += ['FROM', '"%s"' % sender]
        if cc:
            criteria += ['CC', '"%s"' % cc]
        if text:
            criteria += ['TEXT', '"%s"' % text]
        if status:
            criteria += [status]
        if not criteria:
            criteria = ['UNSEEN']
        if subject:
            criteria += ['SUBJECT']
        return criteria

    def _init_multipart_walk(self):
        """Initialize multipart email walk."""
        self._email_index = None
        self._mp_msg = None
        self._part = None

    def _is_walking_multipart(self, email_index):
        """Returns boolean value whether the multipart email walk is in-progress or not."""
        return self._mp_msg is not None and self._email_index == email_index

    def _start_multipart_walk(self, email_index, msg):
        """Start multipart email walk."""
        self._email_index = email_index
        self._mp_msg = msg
        self._mp_iter = msg.walk()

    def _get_all_emails(self):
        """Saves all existing emails to internal variable."""
        typ, mails = self._imap.uid('search', None, 'ALL')
        self._mails = mails[0].split()

    def get_attachments_from_email (self, **kwargs) :
        """Save attachments of email message on given ``email_index`` (overwrite if already exists).

        Arguments:
        - ``email_index``: An email index to identity the email message.
        - ``target_folder`` : local folder for saving attachments to (needs to exist),
            defaults to current directory if None

        Examples:
        | Get Attachments Email | INDEX | C:\\Users\\User\\test
        """
        email_index = kwargs.pop('email_index', None)
        target_folder = kwargs.pop('target_folder', None)
        attachments = []
        data = self._imap.uid('fetch', email_index, '(RFC822)')[1][0][1]
        msg = message_from_bytes(data)

        if target_folder is None:
            target_folder = './'

        for part in msg.walk():
            content_maintype = part.get_content_maintype()
            filename = None
            if content_maintype != "multipart":
                filename = part.get_filename()
                if filename :
                    filepath = os.path.join(target_folder, filename)
                    fp = open(filepath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                    attachments.append(str(filepath))
        return attachments
