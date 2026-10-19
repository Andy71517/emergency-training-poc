"""Check ARC connectivity with the backend's Python. Never reads or sends an API key."""
import socket
import ssl
import urllib.error
import urllib.request

HOST='llm-api.arc.vt.edu'


def describe_connection_error(error):
    reason=error.reason if isinstance(error,urllib.error.URLError) else error
    if isinstance(reason,ssl.SSLCertVerificationError):
        return ('Python could not verify ARC\'s HTTPS certificate. '
                'This is a certificate-trust problem, not an API-key rejection. '
                'Run the ARC network check with the same .venv Python; keep certificate verification enabled.')
    if isinstance(reason,ssl.SSLError):
        return 'Python could not establish a secure TLS connection to ARC. Run the ARC network check to isolate the TLS problem.'
    if isinstance(reason,socket.gaierror):
        return 'DNS lookup failed: Python could not find llm-api.arc.vt.edu. Check the VPN DNS connection and run the ARC network check.'
    if isinstance(reason,TimeoutError):
        return 'The connection to ARC timed out. Run the ARC network check to distinguish network access from an HTTPS/model timeout.'
    if isinstance(reason,ConnectionRefusedError):
        return 'The network connection was refused by ARC or a configured proxy. Run the ARC network check.'
    if isinstance(reason,ConnectionResetError):
        return 'The connection to ARC was reset before a response arrived. Run the ARC network check.'
    code=getattr(reason,'winerror',None) or getattr(reason,'errno',None)
    suffix=f' (OS error {code})' if isinstance(code,int) else ''
    return 'ARC connection failed before an HTTP response'+suffix+'. Run the ARC network check; no API-key rejection was received.'


def main():
    print('ARC network check — no API key read or sent')
    print('HTTPS proxy configured:', 'yes' if urllib.request.getproxies().get('https') else 'no')
    try:
        socket.getaddrinfo(HOST,443,type=socket.SOCK_STREAM)
        print('DNS lookup: OK')
    except OSError as exc:
        print('DNS lookup:',describe_connection_error(exc))
    try:
        with socket.create_connection((HOST,443),timeout=10):
            print('Direct connection to port 443: OK')
    except OSError as exc:
        print('Direct connection:',describe_connection_error(exc))
        print('Continuing HTTPS test; a configured proxy may use a different route.')
    request=urllib.request.Request('https://'+HOST+'/api/v1/models',headers={'User-Agent':'FIELDWORK-network-check'})
    try:
        with urllib.request.urlopen(request,timeout=20) as response:
            print('Python HTTPS: HTTP',response.status)
    except urllib.error.HTTPError as exc:
        print('Python HTTPS: HTTP',exc.code)
        print('An HTTP response was received. HTTPS certificate verification passed.')
        if exc.code in (401,403):
            print('Authentication was deliberately omitted; this response does not test your key.')
    except (urllib.error.URLError,OSError) as exc:
        print('Python HTTPS:',describe_connection_error(exc))
    print('Finished. Share this output; it contains no API key.')


if __name__=='__main__':
    main()
