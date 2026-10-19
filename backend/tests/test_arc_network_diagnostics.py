"""Transport diagnosis must distinguish TLS/DNS from authentication without echoing secrets."""
import socket
import ssl
import urllib.error
from types import SimpleNamespace

from arc.scripts import arc_http
from arc.scripts.check_arc_network import describe_connection_error


def test_transport_categories_and_redaction():
    assert 'certificate' in describe_connection_error(urllib.error.URLError(ssl.SSLCertVerificationError(1,'private details')))
    assert 'DNS' in describe_connection_error(urllib.error.URLError(socket.gaierror(-2,'private details')))
    assert 'timed out' in describe_connection_error(TimeoutError())
    assert 'refused' in describe_connection_error(ConnectionRefusedError())
    assert 'sk-private-token' not in describe_connection_error(urllib.error.URLError('sk-private-token'))


def test_windows_uses_native_context_without_disabling_verification(monkeypatch):
    import sys
    expected=ssl.create_default_context()
    protocols=[]
    def native(protocol):
        protocols.append(protocol)
        return expected
    monkeypatch.setattr(arc_http,'sys',SimpleNamespace(platform='win32'))
    monkeypatch.setitem(sys.modules,'truststore',SimpleNamespace(SSLContext=native))
    context=arc_http.arc_ssl_context()
    assert context is expected and protocols==[ssl.PROTOCOL_TLS_CLIENT]
    assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname is True
