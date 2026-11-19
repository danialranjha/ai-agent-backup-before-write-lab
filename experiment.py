"""Offline component assay. Never opens a real application database."""
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace as NS
from upstream import SOURCES

CASES = [
    dict(name='running_default', running=True),
    dict(name='running_forced_backup', running=True, force=True),
    dict(name='running_forced_no_backup', running=True, force=True, no_backup=True),
    dict(name='closed_default', running=False),
    dict(name='closed_no_backup', running=False, no_backup=True),
    dict(name='copy_failure', running=False, fail_copy=True),
    dict(name='missing_database', running=False, missing=True),
    dict(name='sidecars', running=False, sidecars=True),
]

def run_case(mode, case, fault=None):
    events = []
    with tempfile.TemporaryDirectory(prefix='backup-assay-') as directory:
        root = Path(directory)
        path = root / 'master.db'
        if not case.get('missing'):
            path.write_text('fixture-before')
        if case.get('sidecars'):
            for suffix in ['-wal', '-shm']:
                Path(str(path)+suffix).write_text('fixture'+suffix)
        playlist = NS(Name='demo', Songs=['one', 'two'])
        def remove(pl, song):
            events.append('remove:'+song)
            pl.Songs.remove(song)
            path.write_text('fixture-after')
        db = NS(engine=NS(url=NS(database=str(path))),
                get_playlist=lambda: [playlist], remove_from_playlist=remove)
        def open_db():
            events.append('open')
            return db
        def copy(src, dst):
            events.append('copy_attempt:'+src.name)
            if case.get('fail_copy'):
                raise OSError('injected copy failure')
            shutil.copy2(src, dst)
            events.append('copied:'+src.name)
        class ClickException(Exception):
            pass
        env = dict(Path=Path, time=NS(strftime=lambda _: 'FIXED'),
                   shutil=NS(copy2=copy), click=NS(ClickException=ClickException),
                   _is_rekordbox_running=lambda: case['running'], _open_db=open_db,
                   _commit_force=lambda _: events.append('commit'),
                   _commit_db_write=lambda _: events.append('commit'),
                   _emit=lambda *_: events.append('emit'))
        for source in SOURCES[mode].values():
            exec(compile(source, '<pinned-upstream>', 'exec'), env)
        if fault == 'bypass_guard' and mode == 'after':
            env['_open_db_for_write'] = lambda **_: (db, {})
        if fault == 'skip_backup' and mode == 'after':
            env['_backup_database'] = lambda _: []
        error = None
        try:
            if mode == 'before':
                env['playlist_clear'](None, 'demo')
            else:
                env['playlist_clear'](None, 'demo', case.get('force', False), case.get('no_backup', False))
        except (ClickException, OSError) as exc:
            error = type(exc).__name__+': '+str(exc).replace(str(root), '<fixture>')
        backups = {p.name:p.read_text() for p in sorted((root/'cli-anything-backups').glob('*'))}
        return dict(case=case['name'], mode=mode, events=events,
                    remaining_songs=playlist.Songs, error=error,
                    final_bytes=path.read_text() if path.exists() else None,
                    backups=backups)

def run():
    return dict(scope='Offline extracted source, synthetic database callbacks and bytes; no live model or SQLCipher',
                scenario_pairs=len(CASES), rows=[run_case(mode,c) for c in CASES for mode in ['before','after']])

if __name__ == '__main__':
    result=run()
    Path('results.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Exact component observations','','Eight designed pairs, sixteen rows. Not attack rates. Before ignores force/backup settings, which did not exist in that function. Both versions open the synthetic database for lookup before any guard.','','|Scenario|Revision|Removals|Commit|Backups|Error|','|---|---|---:|---|---:|---|']
    for r in result['rows']:
        lines.append('|'+ '|'.join([r['case'],r['mode'],str(sum(e.startswith('remove:') for e in r['events'])),str('commit' in r['events']),str(len(r['backups'])),r['error'] or 'none'])+'|')
    lines += ['','Full ordered events and exact fixture bytes: [results.json](results.json).','Copy failure prevents removal/commit in the guarded function. Closed-state no-backup remains allowed. The stub can mutate missing-file state in the before arm; that is not evidence of real database behavior. Copying separate active database files does not establish a consistent recoverable snapshot.']
    Path('evidence.md').write_text('\n'.join(lines)+'\n')
