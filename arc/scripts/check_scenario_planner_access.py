"""Small ARC-hosted LLM access check. No GPU job or extra Python packages needed.
The personal key is entered privately and never saved or printed.
"""
import getpass
import json
import os
import sys
import urllib.error
import urllib.request


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
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read(1_000_000))
    except urllib.error.HTTPError as exc:
        messages = {401: 'Key rejected. Check the key privately in your ARC account.',
                    403: 'Access denied by the service.', 429: 'Service busy or rate limit reached. Retry later.'}
        raise SystemExit(f'HTTP {exc.code}: ' + messages.get(exc.code, 'Request failed; no response body printed.')) from None
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
