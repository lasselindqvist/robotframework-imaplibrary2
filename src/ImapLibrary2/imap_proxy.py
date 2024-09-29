import ssl

from socks import create_connection
from socks import PROXY_TYPE_SOCKS4
from socks import PROXY_TYPE_SOCKS5
from socks import PROXY_TYPE_HTTP

from imaplib import IMAP4
from imaplib import IMAP4_PORT
from imaplib import IMAP4_SSL_PORT

# Credits to example: https://gist.github.com/liuyun201990/1b3a3464bdbf53ac7e7041a149ab118e

class IMAP4Proxy(IMAP4):
    """
    IMAP service trough SOCKS proxy. PySocks module required.
    """

    PROXY_TYPES = {"socks4": PROXY_TYPE_SOCKS4,
                   "socks5": PROXY_TYPE_SOCKS5,
                   "http": PROXY_TYPE_HTTP}

    def __init__(self, host, port=IMAP4_PORT,
                 proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None,
                 rdns=True, username=None, password=None, proxy_type="http"):

        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.rdns = rdns
        self.username = username
        self.password = password
        self.proxy_type = IMAP4Proxy.PROXY_TYPES[proxy_type.lower()]

        IMAP4.__init__(self, host, port)

    def _create_socket(self, timeout=None):
        return create_connection((self.host, self.port), proxy_type=self.proxy_type, proxy_addr=self.proxy_host,
                                 proxy_port=self.proxy_port, proxy_rdns=self.rdns, proxy_username=self.proxy_username,
                                 proxy_password=self.proxy_password)


class IMAP4SSLProxy(IMAP4Proxy):

    def __init__(self, host='', port=IMAP4_SSL_PORT, keyfile=None, certfile=None, ssl_context=None,
                 proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None,
                 rdns=True, username=None, password=None, proxy_type="socks5"):

        if ssl_context is not None and keyfile is not None:
                raise ValueError("ssl_context and keyfile arguments are mutually "
                                 "exclusive")
        if ssl_context is not None and certfile is not None:
            raise ValueError("ssl_context and certfile arguments are mutually "
                             "exclusive")

        self.keyfile = keyfile
        self.certfile = certfile
        if ssl_context is None:
            ssl_context = ssl._create_stdlib_context(certfile=certfile,
                                                     keyfile=keyfile)
        self.ssl_context = ssl_context

        IMAP4Proxy.__init__(self, host, port,
                            proxy_host=proxy_host, proxy_port=proxy_port, proxy_username=proxy_username, proxy_password=proxy_password,
                            rdns=rdns, username=username, password=password, proxy_type=proxy_type)

    def _create_socket(self, timeout=None):
        sock = IMAP4Proxy._create_socket(self, timeout=None)
        server_hostname = self.host if ssl.HAS_SNI else None
        return self.ssl_context.wrap_socket(sock, server_hostname=server_hostname)

    def open(self, host='', port=IMAP4_PORT, timeout=None):
        IMAP4Proxy.open(self, host, port, timeout=None)
