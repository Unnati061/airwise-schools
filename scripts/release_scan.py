"""Read-only secret-pattern scan; findings contain locations, never matched values."""
import json
import re
import subprocess
from pathlib import Path

PATTERNS = {
    'AWS_ACCESS_KEY_ID': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'JWT_LITERAL': re.compile(rb'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b'),
    'PRIVATE_KEY': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'GITHUB_TOKEN': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'CREDENTIAL_URL': re.compile(rb'https?://[^\s/\x22\x27:@]+:[^\s/\x22\x27@]+@'),
    'STATIC_SECRET_ASSIGNMENT': re.compile(rb'(?i)(?:password|secret_access_key|aws_secret_access_key|refresh_token|access_token)\s*[=:]\s*[\x22\x27]([^\x22\x27\r\n]{12,})[\x22\x27]'),
}


def git(*args):
    return subprocess.check_output(['git', *args])


def scan():
    paths = git('ls-files', '-z').split(b'\0')
    objects = git('rev-list', '--objects', '--all').decode().splitlines()
    findings = []
    working_findings = []
    for path in paths:
        if not path: continue
        content = Path(path.decode()).read_bytes()
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                candidate = match.group(1) if label == 'STATIC_SECRET_ASSIGNMENT' else match.group()
                working_findings.append({'path': path.decode(), 'line': content[:match.start()].count(b'\n') + 1,
                    'kind': label, 'labelled_test_literal': candidate.startswith((b'SYNTHETIC', b'synthetic', b'test-', b'TEST_', b'OFFLINE'))})
    checked = 0
    process = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for entry in objects:
        oid, _, path = entry.partition(' ')
        process.stdin.write((oid + '\n').encode()); process.stdin.flush()
        header = process.stdout.readline().decode().split()
        if len(header) != 3: raise RuntimeError('Unexpected Git object header')
        content = process.stdout.read(int(header[2])); process.stdout.read(1)
        if header[1] != 'blob': continue
        checked += 1
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                candidate = match.group(1) if label == 'STATIC_SECRET_ASSIGNMENT' else match.group()
                synthetic = candidate.startswith((b'SYNTHETIC', b'synthetic', b'test-', b'TEST_', b'OFFLINE'))
                findings.append({'blob': oid, 'path': path, 'line': content[:match.start()].count(b'\n') + 1,
                                 'kind': label, 'labelled_test_literal': synthetic})
    process.stdin.close(); process.wait(timeout=10)
    private_paths = [p.decode() for p in paths if p and re.search(rb'(^|/)(\.env($|\.)|work/|\.venv/)|\.(pem|pfx|zip)$', p)
                     and not p.endswith(b'.env.example')]
    print(json.dumps({'tracked_paths': len([p for p in paths if p]), 'reachable_blobs_scanned': checked,
                      'private_path_findings': private_paths, 'history_pattern_findings': findings,
                      'working_tree_pattern_findings': working_findings,
                      'limitations': 'Pattern scan only, no entropy/remote secret validation; not a guarantee. Historical values never printed.'}))
    return findings, private_paths


if __name__ == '__main__':
    scan()
