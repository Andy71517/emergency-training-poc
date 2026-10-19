"""Verified HTTPS contexts for ARC clients; use native Windows chain validation."""
import ssl
import sys


def arc_ssl_context():
    if sys.platform=='win32':
        try:
            import truststore
        except ImportError:
            raise ValueError('Windows HTTPS support is missing. Run .\\.venv\\Scripts\\python.exe -m pip install -e . from the project folder.') from None
        context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.verify_mode=ssl.CERT_REQUIRED
        context.check_hostname=True
        return context
    return ssl.create_default_context()
