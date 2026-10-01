"""Small platform-neutral FFmpeg process and executable helpers."""
from pathlib import Path
import os
import re
import shutil
import subprocess


def resolve_tool(name, explicit=None, env_name=None):
    executable = name + '.exe' if os.name == 'nt' and not name.lower().endswith('.exe') else name
    value = explicit or (os.environ.get(env_name) if env_name else None)
    candidates = []
    if value:
        candidate = Path(value).expanduser()
        candidates.extend([candidate, candidate / executable])
    found = next((item.resolve() for item in candidates if item.is_file()), None)
    if found is None:
        which = shutil.which(executable) or shutil.which(name)
        found = Path(which).resolve() if which else None
    if found is None or not found.is_file() or found.is_symlink():
        flag = '--' + name.replace('.exe', '')
        raise FileNotFoundError(f'{executable} is required. Set {flag}, {env_name}, or PATH.')
    return found


def version(executable):
    result = subprocess.run([str(executable), '-version'], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=30)
    if result.returncode:
        raise RuntimeError(f'Unable to read {Path(executable).name} version: {result.stderr.strip()}')
    return result.stdout.splitlines()[0].strip() if result.stdout else ''


def filtergraph_file_args(executable, filename):
    """Keep graphs off Windows' command line and support FFmpeg 9+.

    Older FFmpeg uses filter_complex_script. Newer releases removed that
    option and read string options from files with the -/option syntax.
    Detect the installed command's capabilities rather than guessing a version.
    """
    result = subprocess.run([str(executable), '-hide_banner', '-h', 'full'],
                            capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=30)
    if result.returncode:
        raise RuntimeError('Unable to inspect FFmpeg filtergraph options')
    help_text = result.stdout + result.stderr
    if re.search(r'(?m)^\s*-filter_complex_script\s', help_text):
        return ['-filter_complex_script', str(filename)]
    if re.search(r'(?m)^\s*-filter_complex\s', help_text):
        return ['-/filter_complex', str(filename)]
    raise RuntimeError('FFmpeg does not provide complex filtergraph support')


def run(executable, args, stdout_path, stderr_path, timeout, cwd=None):
    command = [str(executable), *map(str, args)]
    with Path(stdout_path).open('xb') as stdout, Path(stderr_path).open('xb') as stderr:
        try:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, cwd=cwd,
                                    timeout=timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise TimeoutError('FFmpeg process timed out; partial output and logs retained') from error
    return command, result.returncode
