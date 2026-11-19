# Backup before mutation: an offline agent-CLI component assay

Hypothesis: CLI-Anything's Rekordbox write guard stops playlist mutations while the application is reported running unless force and backup are enabled, and completes backup before removing entries when backup is requested. A failed backup must prevent mutation.

This tests extracted source functions with synthetic objects and harmless temporary file bytes. No AI model, desktop application, SQLCipher connection, real playlist, process detector or network endpoint runs. It is not a reproduction of prompt injection, data corruption or database recovery.

## Reproduce

Python 3.10+ standard library only. From this directory:

```sh
python3 -B -m unittest -v
python3 -B experiment.py
```

Ten focused tests pass. The runner emits [results.json](results.json) with ordered events and normalized fixture bytes, and [evidence.md](evidence.md) with sixteen rows across eight designed scenario pairs. Counts describe fixtures, not real-world attack rates. Tests also demonstrate that bypassing the guard permits a refused action and skipping backup loses the pre-change copy.

## Threat model and intervention

Assume an agent or user asks the wrapper to clear a playlist. The caller may supply force/no-backup options, but the guard, file-copy implementation and test recorder remain trusted. The experiment demonstrates no attacker persuasion. Running-state detection is an injected boolean. No real processes are inspected.

The control is the original `playlist_clear` body from commit `1dd4b4e40b387add8504156c7843c5a41ae7e69b`. The intervention is the revised body and `_db_path`, `_backup_database`, `_open_db_for_write` from `5ceeb4b2e6ca4217c048fd7872897aaf63e9572e`, [PR252](https://github.com/HKUDS/CLI-Anything/pull/252). [source.json](source.json) records exact source URLs, Git blob identities and function hashes. [upstream.py](upstream.py) contains the unchanged selected function text, without CLI decorators. The original function has no force/no-backup arguments; scenario options affect only the revised version. This is a historical patch comparison, not a new vulnerability report.

`experiment.py` supplies one fake playlist with two entries. Database opens, removals, commit callbacks and summary emission are recorded. Removal callbacks change a temporary file from `fixture-before` to `fixture-after`. The real extracted backup code uses `shutil.copy2`; only time formatting is fixed for stable filenames. Click's exception class is represented by a local exception. SQLCipher sessions, transaction bookkeeping and actual commits are replaced by recording callbacks. Before/after calls see the same fake database object.

## Technical walkthrough and actual results

With running state true and default options, the original body removes both invented entries and records a commit. The guarded body opens the fake database for its initial playlist lookup, then refuses: neither removal nor commit occurs. Refusal therefore does not mean no database open.

With running state true and force plus backup, the guarded body copies `fixture-before` before either removal and then records the commit. Force without backup refuses while running. When closed, default backup succeeds; explicitly disabling backup allows mutation with no backup. This is a deliberate limit of the selected rule, not universal backup enforcement.

Injecting an `OSError` in the copy operation leaves both entries and the original bytes unchanged, without a commit. A missing database file also stops the guarded path before removal. The original fake callback still writes in this missing-file scenario; that reflects the stub and says nothing about a real database's ability to open a missing file.

The sidecar scenario copies exact main, WAL and SHM fixture bytes before removal. See the ordered trace for each copy. The ordinary closed-state write is the benign comparison; refusing everything would fail it.

## Limits

- Separate copies of an active database and its sidecars are not proven to be a consistent or recoverable snapshot. No concurrent writer, restore, crash, filesystem durability, SQLCipher encryption or transaction behavior was tested.
- Running-state checks can race. Repeated backups can share a second-resolution filename. Neither property is evaluated here.
- Initial lookup happens before the guard, and real code reopens the database. The fake object does not model separate sessions or open-time side effects.
- Source functions are selected components, not the installed CLI path. Other commands, error cleanup and production configuration need integration testing.
- Backup is recovery preparation, not authorization against an attacker who can request force. No prompt-injection resistance or broad supply-chain protection is established.

For this bounded component, the supported check is ordering: require the applicable safety conditions and successful backup before mutation, and verify a failed copy produces no mutation or commit. Test real snapshot consistency and restore separately before relying on backups for recovery.

## Attribution

Extracted source: HKUDS/CLI-Anything contributors, Copyright 2026 HKUDS CLI-Anything Team. The pinned repository LICENSE is Apache-2.0, included verbatim here, even though the component's documentation describes MIT. Extraction/dependency substitution is identified above; function bodies are unchanged. Harness code is supplied under Apache-2.0. No source document, social copy or editorial artifacts are included.
