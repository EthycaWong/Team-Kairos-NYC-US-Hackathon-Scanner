'use strict';
var ICONS = {
  pin: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`,
  globe: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  clock: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`,
  calendar: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>`,
  link: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/></svg>`,
  empty: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>`
};

const NY_TIME = 'America/New_York';
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateKey = (date, dateOnly = false) => {
  if (dateOnly) return date.toISOString().slice(0, 10);
  const parts = new Intl.DateTimeFormat('en-US', {timeZone:NY_TIME,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date);
  const get = type => parts.find(p => p.type === type).value;
  return `${get('year')}-${get('month')}-${get('day')}`;
};
const keyFor = (year, month, day) => `${year}-${String(month + 1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;

class HackathonScanner {
  constructor() {
    this.events = [];
    this.selectedDay = null;
    this.activeRegion = 'NY';
    this.loading = false;
    this.bindEvents();
    this.updateChips();
    this.load();
  }

  bindEvents() {
    ['compSlider','locSearch','chkVirtual','chkInPerson','chkHC','chkMLH'].forEach(id => {
      document.getElementById(id).addEventListener(id === 'compSlider' || id === 'locSearch' ? 'input' : 'change', () => {
        this.selectedDay = null;
        this.render();
      });
    });
    document.querySelectorAll('#regionChips .chip').forEach(chip => chip.addEventListener('click', () => {
      this.activeRegion = chip.dataset.region;
      this.selectedDay = null;
      document.getElementById('locSearch').value = '';
      this.updateChips();
      this.render();
    }));
    document.getElementById('calendarGrid').addEventListener('click', event => {
      const day = event.target.closest('[data-date]');
      if (!day || !day.classList.contains('has-event')) return;
      this.selectedDay = this.selectedDay === day.dataset.date ? null : day.dataset.date;
      this.render();
    });
  }

  updateChips() {
    document.querySelectorAll('#regionChips .chip').forEach(chip => {
      chip.classList.toggle('active', chip.dataset.region === this.activeRegion);
      chip.setAttribute('aria-pressed', String(chip.dataset.region === this.activeRegion));
    });
  }

  async load(force = false) {
    if (this.loading) return;
    this.loading = true;
    this.showLoading(true);
    this.showError('');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 90000);
    try {
      if (window.location.protocol === 'file:') {
        throw new Error('Double-click “Start Hackathon Scanner.command” in the project folder, or run python3 front/server.py and open http://localhost:8000. Live scanning needs the local server.');
      }
      const response = await fetch('/api/all' + (force ? '?refresh=1' : ''), {signal:controller.signal, cache:'no-store'});
      const data = await response.json();
      if (!Array.isArray(data.events) || !Array.isArray(data.sources)) throw new Error('The server returned an invalid response. Restart the scanner server.');
      this.processData(data.events);
      document.getElementById('sourceStatus').innerHTML = data.sources.map(source => {
        const label = source.status === 'live' ? (data.cached ? 'cached' : 'live') : source.status === 'stale' ? 'saved data · source unavailable' : 'unavailable';
        return `<div><strong>${esc(source.name)}</strong>: ${esc(label)}${source.count !== undefined ? ` · ${source.count} events` : ''}${source.checkedAt ? ` · checked ${esc(new Date(source.checkedAt).toLocaleString('en-US', {timeZone:NY_TIME}))} ET` : ''}${source.message ? ` · ${esc(source.message)}` : ''}</div>`;
      }).join('') + '<div>Public listings; check organizer eligibility and registration. Refreshes are limited to once per minute.</div>';
      const hasProblems = data.sources.some(s => s.status !== 'live');
      if (!response.ok) this.showError('No sources could be reached. Check your internet connection and try Refresh in a minute.');
      else if (hasProblems) this.showError('Some sources are unavailable. Any saved results are clearly marked above and expire after 24 hours.');
      document.getElementById('lastScan').textContent = `${this.events.length} upcoming or ongoing events · ${data.cached ? 'cached scan' : 'scan complete'}`;
    } catch (error) {
      this.showError(error.name === 'AbortError' ? 'The scan timed out. Check your connection and try again.' : error.message);
      document.getElementById('lastScan').textContent = this.events.length ? 'refresh failed · previous results retained' : 'scan unavailable';
    } finally {
      clearTimeout(timer);
      this.loading = false;
      this.showLoading(false);
      this.render();
    }
  }

  refresh() { return this.load(true); }

  processData(raw) {
    const current = Date.now();
    this.events = raw.filter(e => {
      try { return ['http:','https:'].includes(new URL(e.website).protocol) && e.name && Number.isFinite(Date.parse(e.start)) && Number.isFinite(Date.parse(e.end)) && Date.parse(e.end) >= current && Date.parse(e.end) >= Date.parse(e.start); }
      catch { return false; }
    }).map(e => {
      const start = new Date(e.start), end = new Date(e.end);
      const durationHours = (end - start) / 3600000;
      const durationStr = e.dateKind ? 'Submission window' : durationHours < 24 ? `${Math.round(durationHours)} hours` : `${Math.round(durationHours / 24 * 10) / 10} days`;
      let competitiveness = (e.virtual ? -2 : 0) + (e.mlhAssociated ? 3 : 0) + (e.hack_club_event ? 1 : 0);
      if (!e.dateKind) competitiveness += durationHours >= 48 ? 3 : durationHours >= 24 ? 2 : durationHours >= 12 ? 1 : 0;
      const compLabel = competitiveness <= 0 ? 'Low' : competitiveness <= 2 ? 'Medium' : 'High';
      const color = competitiveness <= 0 ? 'green' : competitiveness <= 2 ? 'yellow' : 'red';
      const physicalLocation = [e.city, e.state, e.country].filter(Boolean).join(', ') || 'Location not specified';
      const locationStr = e.hybrid ? `Hybrid · ${physicalLocation}` : e.virtual ? 'Online' : physicalLocation;
      const startKey = dateKey(start, Boolean(e.dateKind)), endKey = dateKey(end, Boolean(e.dateKind));
      const format = key => new Date(key + 'T12:00:00Z').toLocaleDateString('en-US', {timeZone:'UTC',month:'short',day:'numeric',year:'numeric'});
      return {...e, startDate:start, endDate:end, startKey, endKey, durationHours, durationStr, competitiveness, compLabel,
        compColor:`var(--${color})`, compBg:`var(--${color}-dim)`, locationStr,
        isNY: ['NY','New York'].includes(e.state),
        dateStr: format(startKey) + (startKey !== endKey ? ' – ' + format(endKey) : '')};
    }).sort((a,b) => {
      const nextDate = e => e.startDate.getTime() >= current ? e.startDate.getTime() : e.endDate.getTime();
      return nextDate(a) - nextDate(b);
    });
  }

  getFiltered(includeDay = true) {
    const max = Number(document.getElementById('compSlider').value);
    const search = document.getElementById('locSearch').value.toLowerCase().trim();
    const checked = id => document.getElementById(id).checked;
    return this.events.filter(e => {
      if (max < 7 && e.competitiveness > max) return false;
      const online = e.virtual || e.hybrid;
      const physical = !e.virtual || e.hybrid;
      if (!(online && checked('chkVirtual') || physical && checked('chkInPerson'))) return false;
      if (e.hack_club_event && !checked('chkHC') || e.mlhAssociated && !checked('chkMLH')) return false;
      if (this.activeRegion === 'NY' && !online && !e.isNY) return false;
      if (this.activeRegion === 'NY-only' && (!physical || !e.isNY)) return false;
      if (this.activeRegion === 'US' && !online && e.countryCode !== 'US') return false;
      if (this.activeRegion === 'virtual' && !online) return false;
      if (search && !`${e.name} ${e.locationStr} ${e.countryCode || ''} ${e.source}`.toLowerCase().includes(search)) return false;
      return !includeDay || !this.selectedDay || e.startKey <= this.selectedDay && this.selectedDay <= e.endKey;
    });
  }

  render() {
    const max = Number(document.getElementById('compSlider').value);
    document.getElementById('compLabel').textContent = max === 7 ? 'All events' : `Score ≤ ${max}`;
    this.renderCalendar(this.getFiltered(false));
    this.renderEvents(this.getFiltered());
    const indicator = document.getElementById('dayIndicator');
    indicator.classList.toggle('visible', Boolean(this.selectedDay));
    if (this.selectedDay) document.getElementById('dayLabel').textContent = this.selectedDay;
  }

  renderCalendar(filtered) {
    const [year, month] = dateKey(new Date()).split('-').map(Number);
    const grid = document.getElementById('calendarGrid');
    const today = dateKey(new Date());
    const months = Array.from({length:6}, (_, i) => new Date(Date.UTC(year, month - 1 + i, 1)));
    // Build a date index once; avoid scanning every event for every rendered day.
    const first = keyFor(year, month - 1, 1);
    const lastMonth = months[5];
    const last = keyFor(lastMonth.getUTCFullYear(), lastMonth.getUTCMonth(), 31);
    const byDay = new Map();
    filtered.forEach(event => {
      const start = event.startKey > first ? event.startKey : first;
      const end = event.endKey < last ? event.endKey : last;
      const cursor = new Date(start + 'T12:00:00Z');
      while (cursor.toISOString().slice(0,10) <= end) {
        const key = cursor.toISOString().slice(0,10);
        if (!byDay.has(key)) byDay.set(key, []);
        if (byDay.get(key).length < 3) byDay.get(key).push(event);
        cursor.setUTCDate(cursor.getUTCDate() + 1);
      }
    });
    grid.innerHTML = months.map(date => {
      const y = date.getUTCFullYear(), m = date.getUTCMonth();
      let html = `<div class="month-card"><div class="month-name">${MONTHS[m]} ${y}</div><div class="day-labels">${['S','M','T','W','T','F','S'].map(d => `<div class="day-label">${d}</div>`).join('')}</div><div class="days-grid">`;
      html += '<div class="day empty"></div>'.repeat(date.getUTCDay());
      const count = new Date(Date.UTC(y,m+1,0)).getUTCDate();
      for (let d = 1; d <= count; d++) {
        const key = keyFor(y,m,d), events = byDay.get(key) || [];
        html += `<button type="button" class="day${events.length ? ' has-event' : ''}${key === today ? ' today' : ''}${key === this.selectedDay ? ' selected' : ''}" data-date="${key}" aria-label="${key}${events.length ? ', events available' : ''}" aria-pressed="${key === this.selectedDay}" ${events.length ? '' : 'disabled'}><span class="day-num">${d}</span><div class="day-dots">${events.map(e => `<span class="day-dot" style="background:${e.compColor}"></span>`).join('')}</div></button>`;
      }
      return html + '</div></div>';
    }).join('');
    document.getElementById('calCount').textContent = `${filtered.length} matching events`;
  }

  renderEvents(filtered) {
    document.getElementById('listCount').textContent = `${filtered.length} event${filtered.length === 1 ? '' : 's'}`;
    document.getElementById('eventsList').innerHTML = filtered.length ? filtered.map(e =>
      `<a href="${esc(e.website)}" target="_blank" rel="noopener noreferrer" class="event-card"><div class="event-logo" style="background:${e.compBg};color:${e.compColor}">${esc(e.name.charAt(0))}</div><div class="event-info"><h3>${esc(e.name)}</h3><div class="event-meta"><span class="meta-item">${ICONS.calendar}${esc(e.dateStr)}</span><span class="meta-item">${e.virtual ? ICONS.globe : ICONS.pin} ${esc(e.locationStr)}</span><span class="meta-item">${ICONS.clock}${esc(e.durationStr)}</span></div><div class="badges"><span class="badge" style="background:${e.compBg};color:${e.compColor}">${e.compLabel} · estimated</span><span class="badge badge-dur">${esc(e.source)}</span>${e.mlhAssociated ? '<span class="badge badge-mlh">MLH</span>' : ''}${e.hack_club_event ? '<span class="badge badge-hc">Hack Club official</span>' : ''}</div></div><span class="event-link">${ICONS.link}</span></a>`
    ).join('') : `<div class="empty-state">${ICONS.empty}<p>No upcoming events match your filters.</p>${this.selectedDay ? '<button class="btn" onclick="app.clearDayFilter()">Clear day filter</button>' : ''}</div>`;
  }

  clearDayFilter() { this.selectedDay = null; this.render(); }
  showLoading(show) {
    document.getElementById('loadingState').style.display = show ? 'flex' : 'none';
    document.getElementById('content').style.display = show ? 'none' : 'block';
    document.getElementById('refreshBtn').disabled = show;
    document.getElementById('refreshBtn').setAttribute('aria-busy', String(show));
  }
  showError(message) {
    document.getElementById('errorBox').innerHTML = message ? `<div class="error-box">${esc(message)}</div>` : '';
  }
}

var app = new HackathonScanner();
