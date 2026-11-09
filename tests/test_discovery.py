import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'front'))
import server as s
FIXTURES = Path(__file__).parent / 'fixtures'
NOW = datetime(2026, 11, 8, 20, tzinfo=timezone.utc)


class DiscoveryTests(unittest.TestCase):
    def test_eventbrite_public_state_tags_and_timezone(self):
        rows, pages, skipped = s.parse_eventbrite((FIXTURES / 'eventbrite.html').read_text())
        self.assertEqual(len(rows), 1)  # Excludes unrelated directory recommendations.
        self.assertEqual(rows[0]['state'], 'New York')
        self.assertEqual(rows[0]['start'], '2026-11-09T20:00:00Z')
        self.assertIn('Hackathon', rows[0]['themes'])
        self.assertEqual((pages, skipped), (2, 0))

    def test_luma_filters_networking_and_recognizes_remote_title(self):
        rows, skipped = s.parse_luma((FIXTURES / 'luma.html').read_text())
        self.assertEqual(len(rows), 2)
        self.assertTrue(any(r['state'] == 'New York' for r in rows))
        self.assertTrue(any(r['hybrid'] for r in rows))
        self.assertEqual(skipped, 0)
        self.assertFalse(any('Mixer' in r['name'] for r in rows))

    def test_devfolio_includes_online_and_excludes_past_section(self):
        rows, skipped = s.parse_devfolio((FIXTURES / 'devfolio.html').read_text())
        self.assertEqual(len(rows), 2)
        self.assertTrue(any(r['virtual'] for r in rows))
        self.assertEqual(skipped, 0)
        self.assertTrue(all(r['website'].endswith('.devfolio.co/') for r in rows))

    def test_changed_markup_raises_instead_of_empty_success(self):
        for parse in (s.parse_eventbrite, s.parse_luma, s.parse_devfolio):
            with self.subTest(parse=parse.__name__), self.assertRaises(ValueError):
                parse('<html>Please sign in</html>')

    def test_embedded_javascript_is_not_executed(self):
        page = s.directory_page('<script>window.__SERVER_DATA__ = {"safe":true}; throw new Error("not executed");</script>')
        self.assertEqual(page.eventbrite, {'safe': True})

    def test_eventbrite_pagination_retains_successful_pages_on_failure(self):
        config = {'eventbrite_pages_per_search': 2}
        urls = ['https://www.eventbrite.com/d/ny--new-york/hackathon/']
        def fetch(url):
            if 'page=2' in url:
                raise OSError('temporary source failure')
            return (FIXTURES / 'eventbrite.html').read_text()
        with patch.object(s, 'discovery_config', return_value=(config, urls)), patch.object(s, 'fetch', side_effect=fetch):
            result = s.scrape_eventbrite()
        self.assertTrue(result.partial)
        self.assertEqual(len(result.events), 1)
        self.assertIn('1 page requests failed', result.message)

    def test_luma_calendar_failures_do_not_discard_other_calendars(self):
        urls = ['https://luma.com/localhost-nyc', 'https://luma.com/example']
        with patch.object(s, 'discovery_config', return_value=({}, urls)), patch.object(s, 'fetch', side_effect=[(FIXTURES / 'luma.html').read_text(), OSError('offline')]):
            result = s.scrape_luma()
        self.assertTrue(result.partial)
        self.assertEqual(len(result.events), 2)
        self.assertIn('1/2', result.message)

    def test_large_search_configuration_has_bounded_request_count(self):
        urls = [f'https://www.eventbrite.com/d/online/hackathon/?q={i}' for i in range(12)]
        with patch.object(s, 'discovery_config', return_value=({'eventbrite_pages_per_search': 8}, urls)), \
             patch.object(s, 'fetch', return_value='page') as fetch, \
             patch.object(s, 'parse_eventbrite', return_value=([], 100, 0)):
            result = s.scrape_eventbrite()
        self.assertLessEqual(fetch.call_count, 32)
        self.assertTrue(result.partial)
        self.assertIn('Coverage limits', result.message)

    @patch.object(s, 'now', return_value=NOW)
    def test_partial_scan_status_and_search_metadata_survive_dedup(self, _):
        rows, _, _ = s.parse_eventbrite((FIXTURES / 'eventbrite.html').read_text())
        with TemporaryDirectory() as temp:
            scanner = s.Scanner(Path(temp) / 'cache.json', {'Eventbrite': lambda: s.SourceResult(rows, '5/49 pages', True)})
            result = scanner.scan()
        self.assertEqual(result['sources'][0]['status'], 'partial')
        self.assertIn('Hackathon', result['events'][0]['themes'])
        extra = dict(result['events'][0], source='Luma', sources=['Luma'], themes=['AI'], description='More detailed event description')
        merged = s.deduplicate([result['events'][0], extra])
        self.assertEqual(len(merged), 1)
        self.assertIn('AI', merged[0]['themes'])
        self.assertIn('Luma', merged[0]['sources'])

    def test_discovery_config_restricts_hosts(self):
        with patch.object(Path, 'read_text', return_value=json.dumps({'luma_calendars':['https://evil.example/calendar']})):
            with self.assertRaises(ValueError):
                s.discovery_config('luma_calendars', {'luma.com'})


if __name__ == '__main__':
    unittest.main()
