"""Transport diagnosis must distinguish TLS/DNS from authentication without echoing secrets."""
import socket
import ssl
import urllib.error

from arc.scripts.check_arc_network import describe_connection_error


def test_transport_categories_and_redaction():
    assert 'certificate' in describe_connection_error(urllib.error.URLError(ssl.SSLCertVerificationError(1,'private details')))
    assert 'DNS' in describe_connection_error(urllib.error.URLError(socket.gaierror(-2,'private details')))
    assert 'timed out' in describe_connection_error(TimeoutError())
    assert 'refused' in describe_connection_error(ConnectionRefusedError())
    assert 'sk-private-token' not in describe_connection_error(urllib.error.URLError('sk-private-token'))
