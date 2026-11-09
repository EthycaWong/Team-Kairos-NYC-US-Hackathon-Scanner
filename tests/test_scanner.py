import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'front'))
import server as s
FIXTURES = Path(__file__).parent / 'fixtures'
NOW = datetime(2026, 11, 8, 20, tzinfo=timezone.utc)


def event(**changes):
    return dict(dict(name='NY Build', website='https://example.com/hack',
                     start='2026-12-01T12:00:00Z', end='2026-12-02T12:00:00Z',
                     source='Test', state='NY', countryCode='US', virtual=False), **changes)


class ParsingTests(unittest.TestCase):
    def test_devpost_live_fixture_and_pagination(self):
        data = json.loads((FIXTURES / 'devpost.json').read_text())
        data['meta'] = {'per_page': 2, 'total_count': 4}
        with patch.object(s, 'fetch', return_value=json.dumps(data)) as fetch:
            rows, note = s.scrape_devpost()
        self.assertEqual(len(rows), 4)
        self.assertEqual(fetch.call_count, 2)
        self.assertTrue(rows[0]['virtual'])
        self.assertEqual(rows[0]['end'], '2026-11-12T23:59:59Z')
        self.assertEqual(rows[0]['dateKind'], 'Submission window')
        self.assertEqual(note, '')
        self.assertTrue(all('status%5B%5D=upcoming' in c.args[0] for c in fetch.call_args_list))

    def test_date_ranges(self):
        for text, start, end in [
            ('Nov 8 - 10, 2026', '2026-11-08', '2026-11-10'),
            ('Nov 30 - Dec 02, 2026', '2026-11-30', '2026-12-02'),
            ('Dec 20 - Jan 05, 2027', '2026-12-20', '2027-01-05'),
            ('Dec 20, 2026 – Jan 05, 2027', '2026-12-20', '2027-01-05'),
            ('Jan 05, 2027', '2027-01-05', '2027-01-05')]:
            with self.subTest(text=text):
                a, b = s.devpost_dates(text)
                self.assertTrue(a.startswith(start))
                self.assertTrue(b.startswith(end))
                self.assertIn('23:59:59', b)
        for text in ['TBA', 'Jan 99, 2027', 'Jan 1 - Feb 2']:
            with self.assertRaises((ValueError, KeyError)):
                s.devpost_dates(text)

    def test_mlh_scraped_html(self):
        rows = s.parse_mlh((FIXTURES / 'mlh.html').read_text())
        self.assertTrue(any(e['hybrid'] for e in rows))
        self.assertTrue(any(e['state'] == 'New York' for e in rows))
        self.assertTrue(all(e['mlhAssociated'] for e in rows))
        with self.assertRaises(ValueError):
            s.parse_mlh('<html>Access denied</html>')

    def test_hackclub_feed(self):
        with patch.object(s, 'fetch', return_value=(FIXTURES / 'hackclub.json').read_text()):
            rows, _ = s.scrape_hackclub()
        self.assertEqual(rows[0]['source'], 'Hack Club')
        self.assertEqual(rows[0]['city'], 'San Jose')

    def test_location(self):
        for text in ['Brooklyn, NY', 'New York, United States', 'NYC', 'Queens, New York']:
            self.assertEqual(s.location(text)['state'], 'New York')
            self.assertEqual(s.location(text)['countryCode'], 'US')
        for text in ['Albany, CA', 'Sydney, Australia', 'York, UK']:
            self.assertNotEqual(s.location(text)['state'], 'New York')

    @patch.object(s, 'now', return_value=NOW)
    def test_normalization_and_url_validation(self, _):
        self.assertEqual(s.normalize(event(), s.iso(NOW))['state'], 'New York')
        for changes in [{'website': 'javascript:alert(1)'}, {'website': '/relative'},
                        {'end': '2026-01-01T00:00:00Z'}, {'name': ''},
                        {'start': '2027-01-01T00:00:00Z'}]:
            self.assertIsNone(s.normalize(event(**changes), s.iso(NOW)))

    @patch.object(s, 'now', return_value=NOW)
    def test_deduplication_keeps_recurring_editions(self, _):
        rows = [event(), event(source='MLH', mlhAssociated=True),
                event(start='2027-12-01T12:00:00Z', end='2027-12-02T12:00:00Z')]
        result = s.deduplicate([s.normalize(e, s.iso(NOW)) for e in rows])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['sources'], ['MLH', 'Test'])
        self.assertTrue(result[0]['mlhAssociated'])


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'sources.json'
        self.clock = patch.object(s, 'now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def test_cache_refresh_and_failure_recovery(self):
        source = Mock(return_value=([event()], ''))
        scanner = s.Scanner(self.path, {'Test': source})
        first = scanner.scan()
        self.assertFalse(first['cached'])
        self.assertEqual(first['sources'][0]['status'], 'live')
        second = scanner.scan(force=True)
        self.assertTrue(second['cached'])
        self.assertEqual(source.call_count, 1)
        scanner.last_attempt -= 61
        source.side_effect = OSError('Source offline')
        stale = scanner.scan(force=True)
        self.assertEqual(stale['sources'][0]['status'], 'stale')
        self.assertEqual(len(stale['events']), 1)
        self.assertEqual(stale['events'][0]['checkedAt'], s.iso(NOW))
        scanner.cache['Test']['checkedAt'] = s.iso(NOW - timedelta(hours=25))
        scanner.last_attempt -= 61
        failed = scanner.scan(force=True)
        self.assertEqual(failed['sources'][0]['status'], 'error')
        self.assertEqual(failed['events'], [])

    def test_disk_cache_and_expired_event_removal(self):
        self.path.write_text(json.dumps({'Test': {'checkedAt': s.iso(NOW), 'events': [
            s.normalize(event(), s.iso(NOW)),
            event(start='2026-10-01T00:00:00Z', end='2026-10-02T00:00:00Z')]}}))
        scanner = s.Scanner(self.path, {'Test': Mock(side_effect=OSError('offline'))})
        result = scanner.scan()
        self.assertEqual(len(result['events']), 1)
        self.assertEqual(result['sources'][0]['status'], 'stale')

    def test_malformed_cache_and_partial_outage(self):
        self.path.write_text('{broken')
        scanner = s.Scanner(self.path, {'Good': lambda: ([event()], ''), 'Bad': Mock(side_effect=OSError('offline'))})
        result = scanner.scan()
        self.assertEqual(len(result['events']), 1)
        self.assertEqual({s['status'] for s in result['sources']}, {'live', 'error'})

    def test_simultaneous_requests_share_one_scan(self):
        source = Mock(return_value=([event()], ''))
        scanner = s.Scanner(self.path, {'Test': source})
        with s.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: scanner.scan(), range(4)))
        self.assertEqual(source.call_count, 1)
        self.assertEqual(len(results), 4)


class HTTPTests(unittest.TestCase):
    def test_routes_and_failure_status(self):
        handler = type('TestHandler', (s.Handler,), {'scanner': Mock()})
        handler.scanner.scan.return_value = {'events': [], 'sources': [{'status': 'error'}]}
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{httpd.server_port}'
        try:
            with urlopen(base + '/') as response:
                self.assertIn(b'app.js', response.read())
            with self.assertRaises(HTTPError) as caught:
                urlopen(base + '/api/all?refresh=1')
            self.assertEqual(caught.exception.code, 503)
            caught.exception.close()
            handler.scanner.scan.assert_called_with(force=True)
            for path in ['/server.py', '/../README.md', '/.cache/sources.json']:
                with self.assertRaises(HTTPError) as caught:
                    urlopen(base + path)
                self.assertEqual(caught.exception.code, 404)
                caught.exception.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
