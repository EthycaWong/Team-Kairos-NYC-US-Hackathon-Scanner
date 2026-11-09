#!/usr/bin/env python3
"""Live hackathon discovery. Start from any directory: python3 front/server.py."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
import json
import logging
import math
from pathlib import Path
import re
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent
CACHE_FILE = ROOT.parent / '.cache' / 'sources.json'
UTC = timezone.utc
TTL = 15 * 60
MAX_STALE = 24 * 60 * 60
MAX_PAGES = 32
MAX_BYTES = 5 * 1024 * 1024
LOG = logging.getLogger('scanner')


def now():
    return datetime.now(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def parse_time(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def fetch(url):
    # certifi also supports Python.org macOS installations without configured CAs.
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 HackathonScanner/2.0',
                                    'Accept': 'application/json, text/html'})
    with urlopen(request, context=context, timeout=8) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Source response exceeds size limit')
        return data.decode('utf-8')


def location(text):
    parts = [p.strip() for p in (text or '').split(',') if p.strip()]
    ny = re.search(r'\b(new york|nyc|brooklyn|manhattan|queens|bronx|staten island)\b|(?:,\s*|^)NY(?:\s*,|$)', text or '', re.I)
    state = 'New York' if ny else (parts[1] if len(parts) > 1 else None)
    cc = 'US' if ny or (state and re.fullmatch(r'[A-Z]{2}', state)) or any(p in ('USA', 'United States', 'US') for p in parts) else None
    return {'city': parts[0] if parts else None, 'state': state,
            'countryCode': cc, 'country': 'United States' if cc else None}


MONTHS = {name: i for i, name in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}


def devpost_dates(text):
    """Parse same-month, cross-month and cross-year submission windows."""
    text = re.sub(r'[–—]', '-', text)
    pieces = re.split(r'\s+-\s+', text.strip())
    if len(pieces) not in (1, 2):
        raise ValueError('Unknown submission date range')
    pattern = r'^(?:(?P<month>[A-Za-z]+)\s+)?(?P<day>\d{1,2})(?:,?\s+(?P<year>\d{4}))?$'
    matches = [re.fullmatch(pattern, p.strip()) for p in pieces]
    if not all(matches) or not matches[0]['month']:
        raise ValueError('Unknown submission date format: ' + text)
    first, last = matches[0], matches[-1]
    sm = MONTHS[first['month'].lower()[:3]]
    em = MONTHS[(last['month'] or first['month']).lower()[:3]]
    # Never guess a year from the machine clock; the listing must supply one.
    if not (last['year'] or first['year']):
        raise ValueError('Submission date has no year')
    ey = int(last['year'] or first['year'])
    sy = int(first['year']) if first['year'] else ey - (sm > em)
    start = datetime(sy, sm, int(first['day']), tzinfo=UTC)
    end = datetime(ey, em, int(last['day']), 23, 59, 59, tzinfo=UTC)
    if end < start:
        raise ValueError('End precedes start')
    return iso(start), iso(end)


def parse_devpost(rows):
    result = []
    rejected = 0
    for row in rows:
        try:
            loc = row.get('displayed_location') or {}
            text = loc.get('location') or ''
            virtual = loc.get('icon') == 'globe' or bool(re.search(r'\b(online|virtual|remote)\b', text, re.I))
            start, end = devpost_dates(row.get('submission_period_dates', ''))
            result.append(dict(name=unescape(row['title']), website=row['url'], start=start, end=end,
                               virtual=virtual, hybrid='hybrid' in text.lower(), source='Devpost',
                               dateKind='Submission window', **location('' if virtual else text)))
        except (ValueError, KeyError, TypeError):
            rejected += 1
    return result, rejected


def scrape_devpost():
    def page(number):
        query = urlencode([('status[]', 'open'), ('status[]', 'upcoming'), ('page', number)])
        payload = json.loads(fetch('https://devpost.com/api/hackathons?' + query))
        if not isinstance(payload.get('hackathons'), list):
            raise ValueError('Devpost response schema changed')
        return payload
    first = page(1)
    per_page = int(first.get('meta', {}).get('per_page') or len(first['hackathons']) or 9)
    total_pages = max(1, math.ceil(int(first.get('meta', {}).get('total_count', len(first['hackathons']))) / per_page))
    rows = list(first['hackathons'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for payload in pool.map(page, range(2, min(total_pages, MAX_PAGES) + 1)):
            rows.extend(payload['hackathons'])
    events, rejected = parse_devpost(rows)
    if rows and not events:
        raise ValueError('No Devpost dates could be parsed')
    notes = []
    if total_pages > MAX_PAGES:
        notes.append(f'Scanned first {MAX_PAGES} of {total_pages} pages')
    if rejected:
        notes.append(f'Skipped {rejected} listings with invalid dates')
    return events, '; '.join(notes)


def scrape_hackclub():
    rows = json.loads(fetch('https://hackathons.hackclub.com/api/events/upcoming'))
    if not isinstance(rows, list):
        raise ValueError('Hack Club response schema changed')
    return [dict(row, source='Hack Club') for row in rows], ''


class MLHPage(HTMLParser):
    """Extract the structured event data embedded in MLH's public schedule HTML."""
    def __init__(self):
        super().__init__()
        self.active = False
        self.chunks = []
        self.page = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('data-page', '').startswith('{'):
            self.page = json.loads(attrs['data-page'])
        if tag == 'script' and attrs.get('data-page') == 'app' and attrs.get('type') == 'application/json':
            self.active = True
            self.chunks = []

    def handle_data(self, data):
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.page = json.loads(''.join(self.chunks))
            self.active = False


def parse_mlh(html):
    parser = MLHPage()
    parser.feed(html)
    props = (parser.page or {}).get('props', {})
    if not isinstance(props.get('upcomingEvents'), list):
        raise ValueError('MLH schedule markup changed')
    result = []
    for row in props['upcomingEvents']:
        addr = row.get('venueAddress') or {}
        fmt = str(row.get('formatType', '')).lower()
        inferred = location(row.get('location') or '')
        state = addr.get('state') or inferred['state']
        cc = addr.get('country') or inferred['countryCode']
        result.append(dict(name=row.get('name'), website=row.get('websiteUrl'),
                           start=row.get('startsAt'), end=row.get('endsAt'),
                           virtual=fmt in ('digital', 'virtual', 'online', 'hybrid_digital'),
                           hybrid=fmt.startswith('hybrid'),
                           mlhAssociated=True, source='MLH',
                           **dict(inferred, city=addr.get('city') or inferred['city'],
                                  state='New York' if state in ('NY', 'New York') else state,
                                  country='United States' if cc == 'US' else inferred['country'],
                                  countryCode=cc)))
    return result


def scrape_mlh():
    # MLH seasons run July–June; choose the season from today's date.
    today = now()
    season = today.year + (today.month >= 7)
    return parse_mlh(fetch(f'https://www.mlh.com/seasons/{season}/events')), ''


def normalize(event, checked_at):
    start, end = parse_time(event['start']), parse_time(event['end'])
    url = urlsplit(event.get('website') or '')
    name = str(event.get('name') or '').strip()
    if not name or url.scheme not in ('http', 'https') or not url.hostname or end < start or end < now():
        return None
    return dict(event, name=name, start=iso(start), end=iso(end),
                virtual=bool(event.get('virtual')), hybrid=bool(event.get('hybrid')),
                state='New York' if event.get('state') in ('NY', 'New York') else event.get('state'),
                checkedAt=checked_at, sources=[event['source']])


def deduplicate(events):
    result = []
    for event in sorted(events, key=lambda e: (e['start'], e['name'])):
        url = urlsplit(event['website'])
        identity = (url.netloc.lower().removeprefix('www.'), url.path.rstrip('/'))
        name = re.sub(r'\W+', '', event['name'].casefold())
        match = None
        for old in result:
            old_url = urlsplit(old['website'])
            same_url = identity == (old_url.netloc.lower().removeprefix('www.'), old_url.path.rstrip('/'))
            same_name = name == re.sub(r'\W+', '', old['name'].casefold())
            overlaps = event['start'] <= old['end'] and old['start'] <= event['end']
            if (same_url or same_name) and overlaps:
                match = old
                break
        if match is None:
            result.append(dict(event))
            continue
        match['sources'] = sorted(set(match['sources'] + event['sources']))
        match['source'] = ' / '.join(match['sources'])
        for flag in ('mlhAssociated', 'hack_club_event', 'virtual', 'hybrid'):
            match[flag] = bool(match.get(flag) or event.get(flag))
        for field in ('city', 'state', 'country', 'countryCode'):
            match[field] = match.get(field) or event.get(field)
    return result


class Scanner:
    def __init__(self, cache_file=CACHE_FILE, sources=None):
        self.sources = sources if sources is not None else {'Devpost': scrape_devpost, 'Hack Club': scrape_hackclub, 'MLH': scrape_mlh}
        self.cache_file = cache_file
        self.cache = {}
        self.lock = threading.Lock()
        self.last_attempt = 0
        self.last_status = []
        try:
            saved = json.loads(cache_file.read_text())
            for name, entry in saved.items():
                try:
                    age = now() - parse_time(entry['checkedAt'])
                    if name not in self.sources or not timedelta(0) <= age < timedelta(seconds=MAX_STALE):
                        continue
                    events = []
                    for row in entry['events']:
                        try:
                            event = normalize(dict(row, source=name), entry['checkedAt'])
                            if event:
                                events.append(event)
                        except (ValueError, TypeError, KeyError):
                            continue
                    self.cache[name] = {'events': events, 'checkedAt': entry['checkedAt']}
                except (ValueError, TypeError, AttributeError, KeyError):
                    continue
        except (OSError, ValueError, TypeError, AttributeError, KeyError):
            pass

    def scan(self, force=False):
        with self.lock:
            age = time.monotonic() - self.last_attempt if self.last_attempt else float('inf')
            if age < (60 if force else TTL):
                return self.payload(self.last_status, True)
            self.last_attempt = time.monotonic()
            statuses = []
            checked = iso(now())
            with ThreadPoolExecutor(max_workers=len(self.sources)) as pool:
                tasks = {pool.submit(scraper): name for name, scraper in self.sources.items()}
                for task in as_completed(tasks):
                    name = tasks[task]
                    try:
                        rows, note = task.result()
                        events = []
                        rejected = 0
                        for row in rows:
                            try:
                                event = normalize(row, checked)
                                if event:
                                    events.append(event)
                            except (ValueError, KeyError, TypeError):
                                rejected += 1
                        if rows and rejected == len(rows):
                            raise ValueError('Source returned no valid event records')
                        self.cache[name] = {'events': events, 'checkedAt': checked}
                        statuses.append({'name': name, 'status': 'live', 'count': len(events),
                                         'checkedAt': checked, 'message': note + (f' Skipped {rejected} invalid records.' if rejected else '')})
                    except Exception as error:
                        LOG.warning('%s scan failed: %s', name, error)
                        cached = self.cache.get(name)
                        usable = cached and now() - parse_time(cached['checkedAt']) < timedelta(seconds=MAX_STALE)
                        statuses.append({'name': name, 'status': 'stale' if usable else 'error',
                                         'checkedAt': cached['checkedAt'] if usable else None,
                                         'message': str(error)[:250]})
            self.last_status = sorted(statuses, key=lambda s: s['name'])
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                temp = self.cache_file.with_suffix('.tmp')
                temp.write_text(json.dumps(self.cache))
                temp.replace(self.cache_file)
            except OSError as error:
                LOG.warning('Could not save cache: %s', error)
            return self.payload(self.last_status, False)

    def payload(self, statuses, cached):
        events = []
        for entry in self.cache.values():
            if now() - parse_time(entry['checkedAt']) < timedelta(seconds=MAX_STALE):
                events.extend(e for e in entry['events'] if parse_time(e['end']) >= now())
        events = deduplicate(events)
        return {'events': events, 'sources': statuses, 'cached': cached,
                'generatedAt': iso(now()), 'refreshAfterSeconds': max(0, math.ceil(60 - (time.monotonic() - self.last_attempt))),
                'scope': 'Public listings; verify eligibility and registration with organizers.'}


class Handler(BaseHTTPRequestHandler):
    scanner = None

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == '/api/all':
            payload = self.scanner.scan(force='refresh=1' in path.query.split('&'))
            status = 200 if any(s['status'] != 'error' for s in payload['sources']) else 503
            return self.respond(status, json.dumps(payload).encode(), 'application/json; charset=utf-8')
        files = {'/': 'index.html', '/index.html': 'index.html', '/app.js': 'app.js'}
        if path.path == '/favicon.ico':
            return self.respond(204, b'', 'image/x-icon')
        if path.path not in files:
            return self.respond(404, b'Not found', 'text/plain')
        file = ROOT / files[path.path]
        self.respond(200, file.read_bytes(), 'text/javascript; charset=utf-8' if file.suffix == '.js' else 'text/html; charset=utf-8')

    def respond(self, status, data, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--open', action='store_true', help='Open the scanner in your browser')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    Handler.scanner = Scanner()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as error:
        parser.exit(1, f'Cannot start server: {error}. Try --port 8001.\n')
    with server:
        url = f'http://localhost:{server.server_port}'
        print(f'Hackathon scanner: {url}\nPress Ctrl+C to stop.', flush=True)
        if args.open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nScanner stopped.')


if __name__ == '__main__':
    main()
