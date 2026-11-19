import hashlib
import json
from pathlib import Path
import unittest
import experiment as e
from upstream import SOURCES

class AssayTests(unittest.TestCase):
    def case(self, name, mode='after', fault=None):
        return e.run_case(mode,next(c for c in e.CASES if c['name']==name),fault)
    def test_running_refused(self):
        r=self.case('running_default')
        self.assertEqual(r['events'],['open'])
        self.assertEqual(r['remaining_songs'],['one','two'])
        self.assertIn('Refusing',r['error'])
        self.assertIn('commit',self.case('running_default','before')['events'])
    def test_forced_no_backup_refused(self):
        r=self.case('running_forced_no_backup')
        self.assertEqual(r['events'],['open'])
        self.assertIn('without a backup',r['error'])
    def test_forced_and_benign_backup_before_remove(self):
        for name in ['running_forced_backup','closed_default']:
            r=self.case(name)
            self.assertIsNone(r['error'])
            self.assertEqual(r['backups'],{'master.db.FIXED.bak':'fixture-before'})
            self.assertLess(r['events'].index('copied:master.db'),r['events'].index('remove:one'))
            self.assertEqual(r['remaining_songs'],[])
            self.assertEqual(r['final_bytes'],'fixture-after')
            self.assertIn('commit',r['events'])
    def test_copy_failure_stops_mutation(self):
        r=self.case('copy_failure')
        self.assertIn('injected copy failure',r['error'])
        self.assertEqual(r['remaining_songs'],['one','two'])
        self.assertNotIn('commit',r['events'])
        self.assertEqual(r['final_bytes'],'fixture-before')
    def test_missing_file_stops(self):
        r=self.case('missing_database')
        self.assertIn('missing database',r['error'])
        self.assertEqual(r['remaining_songs'],['one','two'])
        self.assertIsNone(r['final_bytes'])
    def test_no_backup_closed_is_allowed_limit(self):
        r=self.case('closed_no_backup')
        self.assertEqual(r['backups'],{})
        self.assertIn('commit',r['events'])
    def test_all_sidecar_bytes_and_order(self):
        r=self.case('sidecars')
        expected={'master.db.FIXED.bak':'fixture-before','master.db-wal.FIXED.bak':'fixture-wal','master.db-shm.FIXED.bak':'fixture-shm'}
        self.assertEqual(r['backups'],expected)
        for name in ['master.db','master.db-wal','master.db-shm']:
            self.assertLess(r['events'].index('copied:'+name),r['events'].index('remove:one'))
        self.assertLess(r['events'].index('remove:two'),r['events'].index('commit'))
    def test_source_identities(self):
        manifest=json.loads(Path('source.json').read_text())
        for mode, functions in SOURCES.items():
            for name,source in functions.items():
                self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),manifest[mode]['functions'][name])
    def test_guard_fault_detected(self):
        good=self.case('running_default');bad=self.case('running_default',fault='bypass_guard')
        self.assertNotIn('commit',good['events'])
        self.assertIn('commit',bad['events'])
    def test_backup_fault_detected(self):
        good=self.case('closed_default');bad=self.case('closed_default',fault='skip_backup')
        self.assertTrue(good['backups']);self.assertFalse(bad['backups'])
        self.assertIn('commit',bad['events'])

if __name__=='__main__': unittest.main()
