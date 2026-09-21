import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'validate_project.py'

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'draft.md').write_text('雨停了。她收起傘，走進書店。', encoding='utf-8')
        self.project = {
            'schema_version': 1, 'project_id': 'test-original',
            'domain': 'narrative', 'mode': 'writing',
            'versions': {'outline': 'v1', 'characters': 'v1'},
            'consumed_versions': {'outline': 'v1', 'characters': 'v1'},
            'units': [{'id': 'CH01', 'file': 'draft.md', 'status': 'draft',
                       'length': {'min': 1, 'max': 100}}],
        }

    def run_contract(self):
        self.assertTrue(SCRIPT.is_file(), '尚未實作專案契約檢查器')
        path = self.root / 'project.json'
        path.write_text(json.dumps(self.project, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run(['python3', str(SCRIPT), str(path)], capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def assert_blocked(self, word):
        result, payload = self.run_contract()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertFalse(payload['ok'])
        self.assertIn(word, ' '.join(payload['errors']))

    def test_outdated_version_is_blocked(self):
        self.project['consumed_versions']['outline'] = 'v0'
        self.assert_blocked('版本')

    def test_missing_versions_are_blocked(self):
        self.project.pop('versions')
        self.assert_blocked('versions')

    def test_missing_draft_is_blocked(self):
        self.project['units'][0]['file'] = 'missing.md'
        self.assert_blocked('檔案')

    def test_path_traversal_is_blocked(self):
        self.project['units'][0]['file'] = '../outside.md'
        self.assert_blocked('路徑')

    def test_wrong_length_is_blocked(self):
        self.project['units'][0]['length']['max'] = 1
        self.assert_blocked('字數')

    def test_duplicate_unit_is_blocked(self):
        self.project['units'].append(dict(self.project['units'][0]))
        self.assert_blocked('重複')

    def test_nonfiction_does_not_require_characters(self):
        self.project['domain'] = 'nonfiction'
        for name in ('versions', 'consumed_versions'):
            self.project[name].pop('characters')
        result, payload = self.run_contract()
        self.assertEqual(result.returncode, 0, payload)

    def screen_project(self):
        self.project.update(mode='screen', continuity_level='A2',
                            generation={'requested': False},
                            assets=[{'id': 'CHR01', 'kind': 'CHR', 'version': 'v1',
                                     'status': 'approved', 'file': 'reference.svg'}],
                            shots=[{'id': 'SH01', 'scene_id': 'SC01',
                                    'asset_refs': [{'id': 'CHR01', 'version': 'v1'}],
                                    'duration': {'seconds': 4, 'source': 'estimated'}}],
                            scenes=[{'id': 'SC01'}])
        self.project['units'][0]['status'] = 'approved'
        (self.root / 'reference.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        for name in ('versions', 'consumed_versions'):
            self.project[name]['script'] = 'v1'

    def test_screen_plan_can_use_estimated_timing(self):
        self.screen_project()
        result, payload = self.run_contract()
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload['checks']['shots'], 1)
        self.assertFalse(payload['executed'])

    def test_screen_rejects_unapproved_script(self):
        self.screen_project()
        self.project['units'][0]['status'] = 'draft'
        self.assert_blocked('劇本')

    def test_screen_rejects_unapproved_asset(self):
        self.screen_project()
        self.project['assets'][0]['status'] = 'draft'
        self.assert_blocked('資產')

    def test_screen_rejects_missing_reference_image(self):
        self.screen_project()
        (self.root / 'reference.svg').unlink()
        self.assert_blocked('檔案')

    def test_screen_rejects_asset_version_drift(self):
        self.screen_project()
        self.project['shots'][0]['asset_refs'][0]['version'] = 'v0'
        self.assert_blocked('資產版本')

    def test_screen_rejects_dangling_scene(self):
        self.screen_project()
        self.project['shots'][0]['scene_id'] = 'missing'
        self.assert_blocked('場景')

    def test_screen_rejects_unknown_duration_source(self):
        self.screen_project()
        self.project['shots'][0]['duration']['source'] = 'guessed-as-fact'
        self.assert_blocked('時長來源')

    def test_screen_measured_timing_requires_file(self):
        self.screen_project()
        self.project['shots'][0]['duration']['source'] = 'measured'
        self.assert_blocked('量測')

    def test_screen_requires_explicit_no_generation(self):
        self.screen_project()
        self.project.pop('generation')
        self.assert_blocked('generation')

    def test_paid_generation_is_never_executed(self):
        self.screen_project()
        self.project['generation']['requested'] = True
        self.assert_blocked('離線')

    def test_a0_does_not_need_reference_assets(self):
        self.screen_project()
        self.project['continuity_level'] = 'A0'
        self.project['assets'] = []
        self.project['shots'][0]['asset_refs'] = []
        result, payload = self.run_contract()
        self.assertEqual(result.returncode, 0, payload)

    def test_a2_does_need_reference_assets(self):
        self.screen_project()
        self.project['assets'] = []
        self.project['shots'][0]['asset_refs'] = []
        self.assert_blocked('資產')

    def test_schema_version_bool_is_rejected(self):
        self.project['schema_version'] = True
        self.assert_blocked('schema_version')

    def test_numeric_false_generation_is_rejected(self):
        self.project['generation'] = {'requested': 0}
        self.assert_blocked('generation')

    def test_duplicate_json_keys_are_rejected(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"schema_version": 0, "schema_version": 1}')
        result = subprocess.run(['python3', str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('重複', ' '.join(json.loads(result.stdout)['errors']))

    def test_writing_draft_accepts_valid_contract(self):
        result, payload = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['checks']['units'], 1)
        self.assertFalse(payload['executed'])

if __name__ == '__main__':
    unittest.main()
