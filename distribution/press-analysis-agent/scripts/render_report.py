"""Render reviewed report JSON; never calculate results or infer engineering judgements."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = (
    ('input', '1. 入力情報'),
    ('conditions', '2. 解析条件'),
    ('raw_results', '3. 解析結果'),
    ('interpretation', '4. 結果の解釈'),
    ('recommendations', '5. 技術コメント・提案'),
    ('warnings', '6. 注意事項'),
    ('evidence', '7. ファイルの保存場所'),
    ('conclusion', '8. 結論'),
)


def esc(value):
    return html.escape(str(value), quote=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def within(path, parent):
    path = path.resolve()
    if not path.is_relative_to(parent.resolve()):
        raise ValueError(f'Path outside allowed directory: {path}')
    return path


def render(run, data, output_name):
    run = within(Path(run), ROOT / 'workspace' / 'runs')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', output_name):
        raise ValueError('Output name must be an ASCII identifier')
    manifest_path = run / 'exchange' / 'run.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode('utf-8-sig'))
    if data['run_id'] != manifest['run_id']:
        raise ValueError('Report run_id does not match run manifest')
    evidence = data['evidence']
    ids = [item['id'] for item in evidence]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r'E[0-9]+', i) for i in ids):
        raise ValueError('Evidence IDs must be unique E<number> identifiers')
    sources = {}
    for item in evidence:
        path = within(run / item['path'], run)
        sources[item['path']] = sha(path.read_bytes())

    def refs(items):
        if not items or any(i not in ids for i in items):
            raise ValueError('Each statement and figure must reference existing evidence IDs')
        return ''  # References remain in report-data.json and provenance.json.

    def statements(items):
        return '<ul>' + ''.join('<li>' + esc(i['text']) + ' ' + refs(i['evidence']) + '</li>' for i in items) + '</ul>'

    content = []
    for key, title in SECTIONS:
        if key in ('input', 'conditions'):
            body = '<table>' + ''.join('<tr><th>' + esc(i['name']) + '</th><td>' + esc(i['value']) + ' ' + refs(i['evidence']) + '</td></tr>' for i in data[key]) + '</table>'
            if key == 'input':
                status = {'succeeded': 'GH応答受信済み', 'unknown': '状態未確定', 'failed_before_solve': '解析開始前に失敗', 'prepared': '準備のみ'}.get(manifest['status'], manifest['status'])
                verified = '確認済み' if manifest.get('solver_success_verified') is True else '未確認'
                body += '<p class="note">実行状態：' + esc(status) + ' ／ ソルバー内部の正常終了：' + verified + '</p>'
        elif key == 'raw_results':
            body = statements(data[key]) + '<div class="figures">'
            for figure in data['figures']:
                path = within(run / figure['path'], run / 'post')
                image = path.read_bytes()
                if not image.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise ValueError(f'Not a PNG: {path}')
                sources[figure['path']] = sha(image)
                uri = 'data:image/png;base64,' + base64.b64encode(image).decode('ascii')
                body += '<figure><figcaption>' + esc(figure['title']) + ' ' + refs(figure['evidence']) + '</figcaption><img src="' + uri + '" alt="' + esc(figure['title']) + '"><p><span class="label">表示条件</span>' + esc(figure['conditions']) + '</p><p><span class="label">観察</span>' + esc(figure['observation']) + '</p></figure>'
            body += '</div>'
        elif key == 'evidence':
            locations = [('入力ファイル', manifest.get('source', '未記録')), ('解析結果', str(run / 'raw' / 'solver'))]
            body = '<table class="locations">' + ''.join('<tr><th>' + esc(label) + '</th><td>' + esc(path) + '</td></tr>' for label, path in locations) + '</table>'
        else:
            body = statements(data[key])
        content.append('<section class="' + key + '"><h2>' + title + '</h2>' + body + '</section>')
    template_path = ROOT / 'assets' / 'report' / 'template.html'
    template = template_path.read_text(encoding='utf-8')
    values = {'TITLE': esc(data['title']), 'SUBTITLE': esc(data['subtitle']),
              'STATUS': esc(data['status_label']), 'CONTENT': '\n'.join(content)}
    result = re.sub(r'\{\{([A-Z]+)\}\}', lambda m: values[m[1]], template)
    output = within(run / 'report' / output_name, run / 'report')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'report.html').write_text(result, encoding='utf-8')
    (output / 'report-data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    record = {'created_at': datetime.now(timezone.utc).isoformat(), 'run_id': data['run_id'],
              'sources_sha256': sources, 'run_manifest_sha256': sha(manifest_bytes),
              'template_sha256': sha(template.encode('utf-8')), 'renderer_sha256': sha(Path(__file__).read_bytes()),
              'html_sha256': sha(result.encode('utf-8'))}
    (output / 'provenance.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    return output / 'report.html'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding='utf-8-sig'))
    print(render(args.run, data, args.name))


if __name__ == '__main__':
    main()
