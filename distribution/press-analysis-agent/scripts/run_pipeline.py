"""Run GH, LS-PrePost and a factual HTML draft. Engineering review belongs to Codex."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import uuid
import zlib

import run_analysis as analysis
import render_report

ROOT = Path(__file__).resolve().parents[1]


def raw_hashes(run):
    raw = run / 'raw'
    files = list(raw.rglob('*'))
    if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in files):
        raise ValueError('Raw contains links')
    return {str(p.relative_to(raw)): analysis.digest(p) for p in files if p.is_file()}


def rewrite_cfile(text, input_path, output_dir, expected):
    """Redirect registered cfile I/O; LS-PrePost interprets all other commands unchanged."""
    lines, images, inputs = [], [], 0
    for line in text.splitlines():
        command = line.strip()
        if not command or command.startswith('$'):
            lines.append(line)
            continue
        if re.fullmatch(r'openc d3plot "[^"\r\n]+"', command, re.I):
            inputs += 1
            lines.append(f'openc d3plot "{input_path}"')
            continue
        match = re.fullmatch(r'print png "([^"\r\n]+)"(.*)\s*', command, re.I)
        if match:
            name = match[1].replace('\\', '/').split('/')[-1]
            if name not in expected or name in images:
                raise ValueError('Unexpected or duplicate image output: ' + name)
            images.append(name)
            lines.append(f'print png "{output_dir / name}"{match[2]}')
            continue
        # Reject only I/O statements that cannot be redirected reliably.
        if re.match(r'(?:openc\s+d3plot|print\s+png)\b', command, re.I):
            raise ValueError('Cannot redirect cfile I/O: ' + command)
        lines.append(line)
    if inputs != 1 or set(images) != set(expected):
        raise ValueError('Require one d3plot input and all configured PNG outputs')
    result = '\n'.join(lines) + '\nexit\n'
    result.encode('ascii')  # Legacy LS-PrePost: do not silently corrupt paths.
    return result


def validate_png(path):
    data = path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Invalid PNG: ' + str(path))
    pos, dimensions, image_data = 8, None, False
    while pos + 12 <= len(data):
        size = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 8 + size
        if end + 4 > len(data) or zlib.crc32(data[pos + 4:end]) != struct.unpack('>I', data[end:end + 4])[0]:
            raise ValueError('Incomplete or corrupt PNG: ' + str(path))
        if kind == b'IHDR':
            dimensions = struct.unpack('>II', data[pos + 8:pos + 16])
        if kind == b'IDAT':
            image_data = True
        if kind == b'IEND':
            if dimensions and all(dimensions) and image_data and end + 4 == len(data):
                return dimensions
            break
        pos = end + 4
    raise ValueError('Incomplete PNG: ' + str(path))


def settings(root, process_id, config):
    process = analysis.read_json(root / 'processes' / process_id / 'process.json')
    post = process.get('postprocess')
    local = config.get('processes', {}).get(process_id, {}).get('postprocess', {})
    if not post:
        raise ValueError('Process has no postprocess definition')
    expected = post['expected_images']
    if not expected or len(expected) != len(set(expected)) or any(not re.fullmatch(r'[A-Za-z0-9_-]+\.png', n) for n in expected):
        raise ValueError('Invalid expected_images')
    exe = Path(config.get('lsprepost_executable', '')).resolve()
    source = Path(local.get('cfile') or post.get('cfile') or '')
    source = (root / source).resolve()
    if not exe.is_file() or exe.suffix.lower() != '.exe' or not source.is_file():
        raise ValueError('Configure existing lsprepost_executable and processes.<id>.postprocess.cfile')
    timeout = config.get('post_timeout_seconds', 600)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('post_timeout_seconds must be positive')
    # Validate redirectable I/O before launching GH, using dummy ASCII paths.
    rewrite_cfile(source.read_text(encoding='utf-8-sig'), Path('input/d3plot'), Path('output'), expected)
    return post, exe, source, timeout


def postprocess(root, run, config):
    manifest_file = run / 'exchange/run.json'
    manifest = analysis.read_json(manifest_file)
    if manifest['status'] != 'succeeded':
        raise ValueError('GH has not completed successfully')
    post, exe, source, timeout = settings(root, manifest['process_id'], config)
    expected = post['expected_images']
    baseline = analysis.definition_hashes(root)
    recorded_raw = analysis.read_json(run / 'exchange/raw-hashes.json')
    if raw_hashes(run) != recorded_raw:
        raise ValueError('Raw hash mismatch before postprocessing')
    d3plot = run / 'raw/solver/d3plot'
    if not d3plot.is_file() or not d3plot.stat().st_size:
        raise ValueError('Missing d3plot')
    post_id = 'lsprepost-' + uuid.uuid4().hex[:12]
    folder = run / 'post' / post_id
    folder.mkdir(exist_ok=False)
    source_hash = analysis.digest(source)
    shutil.copyfile(source, folder / 'original.cfile')
    state = {'status': 'preparing', 'post_id': post_id, 'cfile_sha256': source_hash,
             'expected_images': expected, 'timeout_seconds': timeout, 'executable': str(exe)}
    state_file = folder / 'execution.json'
    lock = root / 'workspace/.post.lock'
    owned, retain = False, False
    try:
        with lock.open('x', encoding='utf-8') as stream:
            json.dump({'run_directory': str(run), 'post_directory': str(folder)}, stream)
        owned = True
        _, alias = analysis.execution_path(run, post_id, config.get('execution_path_alias_root'))
        execution_run = Path(alias) if alias else run
        execution_folder = execution_run / 'post' / post_id
        text = rewrite_cfile((folder / 'original.cfile').read_text(encoding='utf-8-sig'), execution_run / 'raw/solver/d3plot', execution_folder, expected)
        (folder / 'execute.cfile').write_text(text, encoding='ascii')
        if analysis.digest(source) != source_hash or analysis.digest(folder / 'original.cfile') != source_hash:
            raise ValueError('cfile changed during preparation')
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        command = [str(exe), 'c=' + str(execution_folder / 'execute.cfile'), 'w=1200x900']
        state.update(status='running', command=command, alias=alias)
        manifest.update(post_status='running', post_directory=str(folder), report_status='not_started')
        analysis.write_json(manifest_file, manifest)
        with (folder / 'stdout.log').open('wb') as stdout, (folder / 'stderr.log').open('wb') as stderr:
            child = subprocess.Popen(command, cwd=folder, stdout=stdout, stderr=stderr, startupinfo=startup)
            state['pid'] = child.pid
            analysis.write_json(state_file, state)
            try:
                state['exit_code'] = child.wait(timeout=timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                retain = True
                state['status'] = 'unknown'
                raise TimeoutError('LS-PrePost still may be running; no kill or automatic retry') from None
        if state['exit_code'] != 0:
            raise ValueError('LS-PrePost returned a nonzero exit code')
        state['images'] = [{'path': str((folder / n).relative_to(run)), 'dimensions': validate_png(folder / n), 'sha256': analysis.digest(folder / n)} for n in expected]
        state['status'] = 'succeeded'
    except BaseException as exc:
        state.update(status='unknown' if retain else 'error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            integrity = raw_hashes(run) == recorded_raw and analysis.definition_hashes(root) == baseline and analysis.digest(source) == source_hash
        except (OSError, ValueError):
            integrity = False
        if not integrity:
            state.update(status='blocked', error='Raw, definition or original cfile changed')
        state['integrity_verified'] = integrity
        analysis.write_json(state_file, state)
        manifest.update(post_status=state['status'], post_directory=str(folder))
        analysis.write_json(manifest_file, manifest)
        if owned and not retain:
            lock.unlink()
    if state['status'] != 'succeeded':
        raise ValueError(state.get('error', 'Postprocessing incomplete'))
    return folder, state


def draft_report(run, folder, state):
    manifest = analysis.read_json(run / 'exchange/run.json')
    def statement(text, *ids):
        return {'text': text, 'evidence': list(ids)}
    def row(name, value):
        return {'name': name, 'value': value, 'evidence': ['E1']}
    evidence = [{'id': 'E1', 'label': '解析実行記録', 'path': 'exchange/run.json'},
                {'id': 'E2', 'label': 'ポスト処理実行記録', 'path': str((folder / 'execution.json').relative_to(run))}]
    figures = []
    for i, item in enumerate(state['images']):
        eid = f'E{i + 3}'
        evidence.append({'id': eid, 'label': f'図{i + 1}', 'path': item['path']})
        figures.append({'title': f'図{i + 1} 解析結果', 'path': item['path'], 'conditions': '指定cfileの表示条件。Agentによる確認待ち。',
                        'observation': '未記入。画像確認後に記載。', 'evidence': [eid, 'E2']})
    data = {'run_id': manifest['run_id'], 'title': 'プレス解析レポート', 'subtitle': Path(manifest['source']).name,
            'status_label': '下書き／画像確認・解釈待ち', 'input': [row('入力', Path(manifest['source']).name), row('解析種類', manifest['process_id'])],
            'conditions': [row('GH応答待ち', str(manifest['timeout_seconds']) + '秒')],
            'raw_results': [statement(f'GHの通常応答を受信。LS-PrePostで{len(figures)}枚のPNGを生成し、ファイル構造・終了コード・Raw不変を確認。', 'E1', 'E2')],
            'figures': figures, 'interpretation': [statement('画像と専門資料を確認してから記載。現在は未評価。', 'E2')],
            'recommendations': [], 'warnings': [statement('GH応答受信はソルバー内部の正常終了・数値的妥当性の証明ではない。', 'E1')],
            'evidence': evidence, 'conclusion': [statement('解析・画像出力まで完了。Agentによる画像確認とレポート編集が必要。', 'E1', 'E2')]}
    return render_report.render(run, data, 'draft-' + state['post_id'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--process', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--config', type=Path, default=ROOT / 'config/user-config.json')
    args = parser.parse_args()
    run = None
    try:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', args.process):
            raise ValueError('Invalid process id')
        config = analysis.read_json(args.config)
        settings(ROOT, args.process, config)
        if (ROOT / 'workspace/.post.lock').exists():
            raise ValueError('Previous postprocessing is running or unknown; inspect .post.lock')
        run, manifest = analysis.execute(ROOT, args.process, args.input, args.config)
        if manifest['status'] != 'succeeded' or manifest['post_status'] in ('error', 'blocked'):
            raise ValueError('Analysis incomplete; see exchange/run.json')
        folder, state = postprocess(ROOT, run, config)
        # Set review handoff before rendering so report evidence hashes stay current.
        manifest = analysis.read_json(run / 'exchange/run.json')
        manifest['report_status'] = 'awaiting_agent_review'
        analysis.write_json(run / 'exchange/run.json', manifest)
        report = draft_report(run, folder, state)
        print(json.dumps({'run_directory': str(run), 'post_status': 'succeeded', 'report_status': 'awaiting_agent_review', 'draft_report': str(report)}, ensure_ascii=False))
        return 0
    except Exception as exc:
        if run:
            manifest = analysis.read_json(run / 'exchange/run.json')
            manifest['pipeline_error'] = f'{type(exc).__name__}: {exc}'
            if manifest.get('post_status') == 'pending_implementation':
                manifest['post_status'] = 'error'
            manifest['report_status'] = 'incomplete'
            analysis.write_json(run / 'exchange/run.json', manifest)
        print(json.dumps({'run_directory': str(run) if run else None, 'error': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
