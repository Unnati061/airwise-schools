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


def test_missing_tools_resolved_and_native_licences_preserved():
    manifest = json.loads((ROOT / 'docs/third_party/manifest.json').read_text())
    assert manifest['missing_installed_notices'] == []
    public = (ROOT / 'frontend/public/THIRD_PARTY_NOTICES.txt').read_bytes()
    for package in ('change-case', 'uri-js-replace', '@rolldown/binding-win32-x64-msvc'):
        content = (ROOT / 'docs/third_party/upstream/frontend' / package / 'LICENSE').read_bytes()
        assert content in public
    upstream = json.loads((ROOT / 'docs/third_party/upstream/manifest.json').read_text())
    uri = next(e for e in upstream['entries'] if e.get('package') == 'uri-js-replace')
    assert len(uri['verified_dist_files']) == 8 and 'Subsequently supplied' in uri['ref_basis']
    for name in ('CoinUtils', 'Osi', 'Clp', 'Cgl', 'Cbc'):
        assert b'Eclipse Public License - v 2.0' in (ROOT / 'docs/third_party/upstream/backend' / name / 'LICENSE').read_bytes()


def test_public_repo_artifact_rules():
    from scripts.repository_artifacts import unsafe_path
    assert unsafe_path('frontend/node_modules/native/addon.node')
    assert unsafe_path('hidden/libcrypto.so.3')
    assert unsafe_path('deployment.zip')
    assert unsafe_path('frontend/.env.d2')
    assert not unsafe_path('frontend/.env.example')
    assert not unsafe_path('docs/third_party/backend/SCIP/LICENSE')
