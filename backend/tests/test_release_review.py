import hashlib
import json
from pathlib import Path

from scripts.collect_notices import notice

ROOT = Path(__file__).resolve().parents[2]


def test_notices_preserve_upstream_bytes_and_browser_runtime_terms():
    manifest = json.loads((ROOT / 'docs/third_party/manifest.json').read_text())
    assert manifest['entries']
    for entry in manifest['entries']:
        content = (ROOT / 'docs/third_party' / entry['file']).read_bytes()
        assert len(content) == entry['bytes']
        assert hashlib.sha256(content).hexdigest() == entry['sha256']
    public = (ROOT / 'frontend/public/THIRD_PARTY_NOTICES.txt').read_bytes()
    for package in ('react', 'react-dom', 'scheduler', 'lucide-react'):
        content = (ROOT / 'docs/third_party/frontend' / package / 'LICENSE').read_bytes()
        assert content in public
    assert (ROOT / 'LICENSE').read_bytes() in public
    numpy = (ROOT / 'docs/third_party/backend/numpy-2.5.3.dist-info/licenses/LICENSE.txt').read_text()
    assert 'LGPL-2.1-or-later' in numpy and 'GCC-exception-3.1' in numpy
    assert notice('ThirdPartyNoticeText.txt') and not notice('notice_provider.py')
