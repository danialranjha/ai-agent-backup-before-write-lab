# Exact component observations

Eight designed pairs, sixteen rows. Not attack rates. Before ignores force/backup settings, which did not exist in that function. Both versions open the synthetic database for lookup before any guard.

|Scenario|Revision|Removals|Commit|Backups|Error|
|---|---|---:|---|---:|---|
|running_default|before|2|True|0|none|
|running_default|after|0|False|0|ClickException: Refusing to clear playlist 'demo' while Rekordbox is running. Close Rekordbox first, or rerun with --force to acknowledge the risk. Forced writes still create a backup.|
|running_forced_backup|before|2|True|0|none|
|running_forced_backup|after|2|True|1|none|
|running_forced_no_backup|before|2|True|0|none|
|running_forced_no_backup|after|0|False|0|ClickException: Refusing forced write while Rekordbox is running without a backup|
|closed_default|before|2|True|0|none|
|closed_default|after|2|True|1|none|
|closed_no_backup|before|2|True|0|none|
|closed_no_backup|after|2|True|0|none|
|copy_failure|before|2|True|0|none|
|copy_failure|after|0|False|0|OSError: injected copy failure|
|missing_database|before|2|True|0|none|
|missing_database|after|0|False|0|ClickException: Cannot back up missing database: <fixture>/master.db|
|sidecars|before|2|True|0|none|
|sidecars|after|2|True|3|none|

Full ordered events and exact fixture bytes: [results.json](results.json).
Copy failure prevents removal/commit in the guarded function. Closed-state no-backup remains allowed. The stub can mutate missing-file state in the before arm; that is not evidence of real database behavior. Copying separate active database files does not establish a consistent recoverable snapshot.
