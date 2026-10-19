"""Small ARC-hosted LLM access check. No GPU job or extra Python packages needed.
The personal key is entered privately and never saved or printed.
"""
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request

try:
    from .arc_http import arc_ssl_context
except ImportError:
    from arc_http import arc_ssl_context


def safe_error_detail(raw, token):
    """Extract only an error description; never dump headers or a raw response."""
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return 'No JSON error description available.'
    if not isinstance(body, dict):
        return 'Unexpected error format.'
    error = body.get('error', body.get('detail', body.get('message')))
    if isinstance(error, dict):
        error = error.get('message', error.get('detail', error.get('code')))
    if not isinstance(error, str):
        return 'No text error description available.'
    for secret in (token, token.strip()):
        if secret:
            error = error.replace(secret, '[REDACTED]')
    error = re.sub(r'(?i)bearer\s+[^\s"<>]+', 'Bearer [REDACTED]', error)
    error = re.sub(r'(?i)sk-[a-z0-9_-]+', '[REDACTED]', error)
    return ' '.join(error.split())[:800]


def main():
    token = os.environ.get('ARC_LLM_API_KEY') or getpass.getpass('ARC LLM API key (hidden; not saved): ')
    if not token.strip():
        raise SystemExit('No key entered. Nothing sent.')
    model = os.environ.get('ARC_LLM_MODEL', 'gpt-oss-120b')
    payload = {'model': model, 'max_tokens': 256,
               'messages': [{'role': 'user', 'content': 'Reply with the words ARC planner access OK. Do not explain.'}]}
    request = urllib.request.Request('https://llm-api.arc.vt.edu/api/v1/chat/completions',
        data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + token.strip(),
                                                   'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=120, context=arc_ssl_context()) as response:
            result = json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        messages = {401: 'Key rejected. Check the key privately in your ARC account.',
                    403: 'Access denied by the service.', 429: 'Service busy or rate limit reached. Retry later.'}
        detail = safe_error_detail(exc.read(16_384), token)
        print(f'HTTP {exc.code}: ' + messages.get(exc.code, 'Request rejected.'))
        raise SystemExit('Sanitized service error: ' + detail) from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise SystemExit('Connection, timeout, or response-format error. No credentials printed.') from None
    choices = result.get('choices', [])
    if not choices or not isinstance(choices[0].get('message'), dict):
        raise SystemExit('Unexpected response format. No response body printed.')
    message = choices[0]['message']
    if not message.get('content') and not message.get('reasoning_content'):
        raise SystemExit('Service replied without text. Access is reachable, but model response needs investigation.')
    print('ARC hosted planner endpoint: reachable')
    print('Authenticated model response: received')
    print('Requested model: ' + model)
    print('No key saved. Full scenario generation has not run.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit('\nCancelled; no key saved.')

