# Team Kairos · Hackathon Scanner

Discover upcoming and ongoing hackathons from live public Devpost, Hack Club, and Major League Hacking listings. The default view includes **New York State and online/hybrid hackathons**. Other location, format, affiliation, search, and estimated intensity filters are available.

## Start on a Mac

Double-click **Start Hackathon Scanner.command**. It creates a local Python environment, installs the certificate bundle once, starts the server, and opens your browser. Python 3.9+ and internet access are required. Leave the Terminal window open while using the scanner; press Ctrl+C to stop it.

Or start manually from the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python front/server.py --open
```

Open **http://localhost:8000**. If port 8000 is busy, run `python front/server.py --port 8001 --open`. The server works regardless of your current working directory and listens only on your computer. Opening `front/index.html` directly displays startup instructions; live discovery requires the server.

## Live discovery

- **Devpost:** its public hackathon listing feed, open and upcoming statuses, paginated with up to four concurrent requests. At most 32 pages are scanned per refresh; the status panel discloses any limit. Displayed dates are **submission windows**, not necessarily the dates of an in-person event. Date-only windows follow the dates supplied by Devpost.
- **Hack Club:** its public upcoming-events feed, including actual city/state, online/hybrid, and affiliation metadata.
- **MLH:** structured data scraped from the public season schedule HTML. The July–June season is selected automatically; online and hybrid formats are preserved.

Sources run concurrently, with verified HTTPS certificates and bounded request timeouts. Results are normalized, expired records are removed, and overlapping listings with the same name or website are combined. Recurring editions on different dates are preserved.

Normal page loads reuse scans for 15 minutes. **Refresh** requests a new scan, limited to once per minute to avoid hammering the sources. A failed source may use its last successful scan for up to 24 hours, clearly labeled with its original check time. There are no embedded sample events. If every source fails without usable saved data, the page shows a failure rather than invented results. The ignored `.cache/` folder holds local saved scans.

The calendar uses New York time, handles ongoing events and year boundaries, and shows the next six months; the event list includes all matching future listings. Intensity labels are a rough heuristic, not a guarantee of difficulty. Listings do not establish eligibility, registration availability, cost, or suitability—check the organizer's page. These public feeds do not cover every hackathon on the web, and source changes or outages appear in the status panel.

## Checks

```sh
python3 -m unittest discover -s tests -v
node --check front/app.js
node --test tests/frontend.test.cjs
```

Tests run offline using small fixtures captured from the public source responses. They cover source parsing, date ranges, location matching, validation, deduplication, caching and outages, HTTP responses, filters, calendar year boundaries, and safe rendering. GitHub Actions runs these checks on pull requests. Node is only needed for development tests, not for running the scanner.
