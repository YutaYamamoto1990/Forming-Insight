"""Run one local Rhino.Compute GH request; never retry a solve automatically."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def contained(base, path):
    return Path(path).resolve().is_relative_to(Path(base).resolve())


def definition_hashes(root):
    result = {}
    for name in ('AGENTS.md', 'scripts', 'processes', 'docs', 'schemas', 'defaults', 'assets', '.agents'):
        start = root / name
        files = [start] if start.is_file() else start.rglob('*')
        for path in files:
            if path.is_file() and '__pycache__' not in path.parts:
                result[str(path.relative_to(root))] = digest(path)
    return result


def execution_path(solver_dir, run_id, alias_root):
    """Optional ASCII junction for legacy solvers. Data stays inside the run."""
    if not alias_root:
        return solver_dir / 'input.k', None
    if os.name != 'nt':
        raise ValueError('execution_path_alias_root requires Windows')
    alias_root = Path(alias_root)
    if not alias_root.is_absolute() or not str(alias_root).isascii() or any(c.isspace() for c in str(alias_root)):
        raise ValueError('Alias root must be an absolute ASCII path without whitespace')
    alias_root.mkdir(parents=True, exist_ok=True)
    alias = alias_root / run_id
    if alias.exists():
        raise ValueError('Alias already exists; refusing to reuse it')
    environment = os.environ.copy()
    environment['FI_ALIAS_PATH'] = str(alias)
    environment['FI_SOLVER_PATH'] = str(solver_dir)
    powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-Command',
                    "$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path $env:FI_ALIAS_PATH -Target $env:FI_SOLVER_PATH | Out-Null"],
                   env=environment, check=True, capture_output=True,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    if not alias.samefile(solver_dir):
        raise ValueError('Alias target verification failed')
    return alias / 'input.k', str(alias)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post(url, payload, timeout, response_file, api_key=None):
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['RhinoComputeKey'] = api_key
    request = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    # No proxy, redirect, or automatic retry: local file paths only work on this PC.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    completed = queue.Queue(maxsize=1)

    def fetch():
        try:
            with opener.open(request, timeout=timeout) as response:
                completed.put((response.read(), None))
        except urllib.error.HTTPError as exc:
            completed.put((exc.read(), exc))
        except Exception as exc:
            completed.put((None, exc))

    # A wall-clock deadline also covers a peer that keeps sending partial bytes.
    # The worker never writes files; late responses cannot overwrite unknown state.
    threading.Thread(target=fetch, daemon=True).start()
    try:
        content, error = completed.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(f'No complete GH response within {timeout} seconds') from None
    if content is not None:
        Path(response_file).write_bytes(content)
    if error:
        raise error
    value = json.loads(content.decode('utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError('Compute response must be a JSON object')
    return value


def execute(root, process_id, input_file, config_file, prepare_only=False):
    root = Path(root).resolve()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', process_id):
        raise ValueError('Invalid process id')
    process_file = root / 'processes' / process_id / 'process.json'
    if not contained(root / 'processes', process_file):
        raise ValueError('Process definition escapes processes/')
    process = read_json(process_file)
    config = read_json(config_file)
    timeout = config.get('timeout_seconds', 600)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout_seconds must be a positive number')
    url = config.get('compute_url', '').rstrip('/')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('Version 1 requires an explicit local http://localhost:port Compute URL')
    key_env = config.get('api_key_environment')
    api_key = os.environ.get(key_env) if key_env else None
    if key_env and not api_key:
        raise ValueError('Configured API key environment variable is missing')
    settings = config.get('processes', {}).get(process_id, {})
    gh_setting = settings.get('gh_definition') or process.get('gh_definition')
    if not gh_setting:
        raise ValueError('Set processes.<id>.gh_definition in user config')
    gh = Path(gh_setting)
    gh = (root / gh).resolve() if not gh.is_absolute() else gh.resolve()
    source = Path(input_file).resolve(strict=True)
    if source.suffix.lower() != '.k' or not source.is_file() or source.stat().st_size == 0:
        raise ValueError('Input must be a nonempty .k file')
    if not gh.is_file() or gh.suffix.lower() not in ('.gh', '.ghx'):
        raise ValueError('GH definition must be an existing .gh or .ghx file')
    # Do not silently copy an incomplete deck. Include-bundle support is future work.
    with source.open(encoding='utf-8', errors='replace') as stream:
        if any(line.lstrip().upper().startswith('*INCLUDE') for line in stream):
            raise ValueError('Related INCLUDE files require an explicit copy plan; this version accepts a single k file')
    input_parameter = process['input_parameter']
    if not isinstance(input_parameter, str) or not input_parameter:
        raise ValueError('input_parameter is required')
    baseline = definition_hashes(root)
    source_hash, gh_hash = digest(source), digest(gh)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12]
    run = root / 'workspace' / 'runs' / process_id / run_id
    if not contained(root, run) or not contained(root / 'workspace', run):
        raise ValueError('Run folder escapes workspace')
    run.mkdir(parents=True, exist_ok=False)
    for name in ('input', 'work', 'raw', 'logs', 'exchange', 'post', 'report'):
        (run / name).mkdir()
    manifest = {
        'run_id': run_id, 'process_id': process_id, 'status': 'preparing',
        'source': str(source), 'source_sha256': source_hash,
        'gh_source': str(gh), 'gh_sha256': gh_hash,
        'timeout_seconds': timeout, 'compute_url': url,
        'success_basis': None, 'solver_success_verified': False,
        'post_status': 'not_started', 'created_at': datetime.now(timezone.utc).isoformat(),
    }
    manifest_file = run / 'exchange' / 'run.json'
    write_json(manifest_file, manifest)
    lock = root / 'workspace' / '.analysis.lock'
    lock_owned = False
    retain_lock = False
    solve_sent = False
    try:
        shutil.copyfile(source, run / 'input' / source.name)
        shutil.copyfile(gh, run / 'input' / gh.name)
        if digest(run / 'input' / source.name) != source_hash or digest(run / 'input' / gh.name) != gh_hash:
            raise ValueError('Input changed during copying')
        # The solver can modify its own copy without changing the input snapshot.
        solver_dir = run / 'work' / 'solver'
        solver_dir.mkdir()
        solver_input = solver_dir / 'input.k'
        shutil.copyfile(run / 'input' / source.name, solver_input)
        write_json(run / 'exchange' / 'definition-hashes.json', baseline)
        write_json(run / 'exchange' / 'process.json', process)
        manifest['status'] = 'prepared'
        if prepare_only:
            return run, manifest
        with lock.open('x', encoding='utf-8') as stream:
            json.dump({'run_id': run_id, 'run_directory': str(run)}, stream)
        lock_owned = True
        passed_input, alias = execution_path(solver_dir, run_id, config.get('execution_path_alias_root'))
        manifest['solver_input'] = str(solver_input)
        manifest['gh_input_path'] = str(passed_input)
        manifest['execution_path_alias'] = alias
        algo = base64.b64encode((run / 'input' / gh.name).read_bytes()).decode('ascii')
        payload = {'algo': algo, 'pointer': None, 'values': [], 'fileName': gh.name, 'cachesolve': False}
        manifest['status'] = 'checking_connection'
        write_json(manifest_file, manifest)
        io = post(url + '/io', payload, min(timeout, 60), run / 'exchange' / 'io-response.json', api_key)
        if io.get('Errors') or io.get('errors'):
            raise ValueError('Compute could not load the GH definition; see io-response.json')
        names = io.get('InputNames', [x.get('Name') for x in io.get('Inputs', [])])
        if names != [input_parameter]:
            raise ValueError('This version requires one exposed file-path input matching the process definition')
        if definition_hashes(root) != baseline or digest(source) != source_hash or digest(gh) != gh_hash:
            raise ValueError('Definition or original input changed before solve')
        payload['values'] = [{'ParamName': input_parameter, 'InnerTree': {'{0}': [
            {'type': 'System.String', 'data': json.dumps(str(passed_input), ensure_ascii=False)}
        ]}}]
        write_json(run / 'exchange' / 'solve-request.json', payload)
        manifest['status'] = 'running'
        write_json(manifest_file, manifest)
        solve_sent = True
        result = post(url + '/grasshopper', payload, timeout, run / 'raw' / 'gh-response.json', api_key)
        if not isinstance(result.get('values'), list):
            raise ValueError('Response is not a Compute solve result (values array missing)')
        # User-authorized policy: a normal GH response is success, not a solver audit.
        manifest.update(status='succeeded', success_basis='gh_response_received',
                        gh_errors=result.get('errors', []), gh_warnings=result.get('warnings', []))
        # Preserve all files produced beside the execution copy, without following links.
        if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in solver_dir.rglob('*')):
            manifest['post_status'] = 'error'
            raise ValueError('Solver output contains links; refusing to copy outside the run')
        shutil.copytree(solver_dir, run / 'raw' / 'solver')
        write_json(run / 'exchange' / 'raw-hashes.json', {
            str(p.relative_to(run / 'raw')): digest(p) for p in (run / 'raw').rglob('*') if p.is_file()
        })
        manifest['post_status'] = 'pending_implementation'
    except (Exception, KeyboardInterrupt) as exc:
        if manifest['status'] == 'succeeded':
            manifest['post_status'] = 'error'
        else:
            manifest['status'] = 'unknown' if solve_sent else 'failed_before_solve'
        retain_lock = solve_sent and manifest['status'] == 'unknown'
        manifest['error'] = f'{type(exc).__name__}: {exc}'
        (run / 'logs' / 'error.txt').write_text(manifest['error'], encoding='utf-8')
    finally:
        try:
            unchanged = definition_hashes(root) == baseline and digest(source) == source_hash and digest(gh) == gh_hash
        except OSError:
            unchanged = False
        if not unchanged:
            manifest['status'] = 'integrity_error'
            manifest['post_status'] = 'blocked'
            manifest['integrity_error'] = 'Definition or original input changed; no automatic restoration'
        manifest['updated_at'] = datetime.now(timezone.utc).isoformat()
        write_json(manifest_file, manifest)
        if lock_owned and not retain_lock:
            lock.unlink()
    return run, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--process', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--config', default=str(ROOT / 'config' / 'user-config.json'))
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    try:
        run, manifest = execute(ROOT, args.process, args.input, args.config, args.prepare_only)
        print(json.dumps({'run_directory': str(run), **manifest}, ensure_ascii=False, indent=2))
        return 0 if manifest['status'] in ('prepared', 'succeeded') and manifest['post_status'] != 'error' else 1
    except Exception as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
