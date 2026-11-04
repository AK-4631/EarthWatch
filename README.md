# EarthWatch — Planetary Observation System

A cinematic-but-credible global natural-disaster intelligence platform built on
live, keyless public feeds — NASA Earth Observatory Natural Event Tracker
(**EONET**), **USGS** seismic-network summaries and **NOAA** products (NWS
active alerts, NHC tropical cyclones, tsunami bulletins) — with dated NASA
**GIBS** satellite imagery and a fully computed day/night Earth. Python/FastAPI
backend, vanilla JavaScript frontend — no React, no TypeScript, no Node build
chain.

**EarthWatch is an informational monitoring platform, not an official
emergency-warning service.** Data comes from public third-party feeds and may
be delayed, incomplete, or inaccurate. Never rely on EarthWatch for life-safety
decisions; always follow official emergency authorities.

## What the interface does

* **Interactive 3D Earth** — a Three.js globe with a real·astronomy day/night
  shader: the subsolar point is computed from the actual UTC clock (NOAA solar
  approximation) and drives the terminator, ocean sun-glint and twilight band
  through a shared light vector; city lights render on the night side. A
  2°-accurate sun position — not a baked texture offset. Markers encode event
  category **by colour only**; size is constant, so no severity is implied. If
  WebGL or the Three.js CDN is unavailable, a 2D equirectangular canvas map
  preserves data, selection and hover, with the same computed terminator
  drawn per cell.
* **Observation rail** — category visibility toggles with live per-category
  counts (now including USGS *Earthquakes*, NWS alert categories and NOAA
  *Tsunami*), the optional GIBS daily mosaic, the subsolar readout, and feed
  metadata.
* **Intelligence panel** — four tabs:
  * **Event** — the source-grounded record (source, category, observation
    dates, coordinates, geometry count) plus a deterministic analytical
    summary with full provenance.
  * **Briefing** — *Ask EarthWatch*: a rule-based analyst over the records
    this backend retrieved (see below). It parses categories, regions and
    time windows, computes figures, and cites the evidence used. No language
    model; unmatched questions return explicit limitations.
  * **Analytics** — dashboard stats and Chart.js views (records per day,
    category distribution, source recency).
  * **Sources** — the source registry, imagery provenance, retrieval scope
    and an explicit "what this platform does not do" statement.
* **Temporal navigation** — the timeline scrubber selects an *as-of* date over
  the coverage span of the retrieved records' source observation dates.
  Preset windows (24H/7D/30D/ALL) restrict the view; playback steps the as-of
  date. Records are never fabricated: where a window is empty, the globe and
  counts show nothing rather than invented data.
* Global search over retrieved records (`/` focuses it), UTC clock,
  retrieval-refresh cadence with an honest stale-data banner, and
  preferences (ambient effects, auto-rotate — **off by default**) stored in
  the browser only.

## Project structure

```
EarthWatch/
├── app/                         # Python FastAPI backend
│   ├── main.py                  # App init, CORS, static serving, error handlers
│   ├── config.py                # Environment-based settings (pydantic-settings)
│   ├── cache.py                 # In-memory TTL cache with SQLite fallback
│   ├── database.py              # SQLite persistence + ingestion log
│   ├── api/
│   │   └── routes.py            # All /api endpoints + analyst rate limiting
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response schemas
│   └── services/
│       ├── eonet_client.py      # NASA EONET client (timeouts, retries, backoff)
│       ├── feed_client.py       # Shared HTTP plumbing for all public feeds
│       ├── usgs_client.py       # USGS M2.5+ earthquake summary feeds
│       ├── nws_client.py        # NOAA/NWS active alerts + category rule table
│       ├── noaa_client.py       # NOAA NHC storms + tsunami Atom parser
│       ├── normalization.py     # Upstream → internal schema (all sources)
│       ├── analytics.py         # Explainable analytics (no model claims)
│       └── assistant.py         # Rule-based /api/query analyst
├── frontend/                    # Semantic HTML/CSS/JS served by the backend
│   ├── index.html               # Command-center shell (landmarks, ARIA roles)
│   ├── css/
│   │   ├── tokens.css           # Design tokens (colour, spacing, motion)
│   │   ├── shell.css            # Topbar, rail, globe stage, timeline
│   │   ├── panels.css           # Intelligence panel + overlays
│   │   └── effects.css          # Ambient backdrop, reduced-motion guards
│   ├── js/
│   │   ├── app.js               # Orchestrator: data flow, filters, selection,
│   │   │                        #   search, preferences, responsive workspace
│   │   ├── api.js               # Fetch client (AbortController + timeouts)
│   │   ├── globe.js             # Three.js globe, real sun cycle, markers,
│   │   │                        #   GIBS layer, 2D fallback with terminator
│   │   ├── timeline.js          # Coverage/as-of/window temporal navigation
│   │   ├── rail.js              # Category rail + counts
│   │   ├── panel.js             # Panel tabs + event/analysis rendering
│   │   ├── briefing.js          # Ask EarthWatch UI
│   │   ├── charts.js            # Chart.js analytics
│   │   └── effects.js           # Starfield/aurora (progressive, guarded)
│   └── vendor/
│       └── chart.umd.min.js     # Chart.js 4.4.7, vendored (MIT licence, in-file)
├── tests/                       # pytest suite (hermetic temp DB; feeds mocked)
│   ├── conftest.py
│   ├── test_normalization.py    # Live + legacy EONET shapes, polygon guard
│   ├── test_sources.py          # USGS/NWS/NHC/tsunami normalizers + rules
│   ├── test_assistant.py        # Analyst answers, filters, limitations
│   ├── test_eonet_client.py     # Retry/backoff behaviour of the feed client
│   └── test_routes.py           # API behaviour incl. merge, dedupe, statuses
├── verify.py                    # Live API verification (run against a server)
├── requirements.txt
├── .env.example
└── README.md
```

## Technology stack

* **Frontend:** semantic HTML5, modern CSS3, vanilla JavaScript (ES modules).
  Three.js r161 (`three.module.js` wired through an import map) for the 3D
  globe; Chart.js 4.4.7 **vendored locally** (`frontend/vendor/chart.umd.min.js`)
  so the dashboard does not depend on a chart CDN at runtime.
* **Backend:** Python 3.12+, FastAPI, Uvicorn, HTTPX, Pydantic, SQLite.
* Fonts (Inter, JetBrains Mono, Space Grotesk) load from Google Fonts with
  system fallbacks; the app remains fully usable if CDNs are unreachable.

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # macOS/Linux

# 2. Install pinned dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env              # Windows
# cp .env.example .env              # macOS/Linux

# 4. Run the server (database schema is created automatically on first boot)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000 — API docs at `/docs`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Service, cache and database health |
| `GET /api/events` | Merged records from all registered feeds (`category`, `status`, `limit`, `days`, `offset`, `search`) |
| `GET /api/events/{event_id}` | Single event detail (aux sources served from persisted retrievals) |
| `GET /api/categories` | EONET event categories |
| `GET /api/metrics` | Source-derived record counts |
| `GET /api/sources` | Registered data sources and their status |
| `GET /api/imagery/config` | NASA GIBS imagery configuration (no secrets) |
| `GET /api/analytics/summary` | Explainable analytics over retrieved records |
| `POST /api/insights` | Event/category insight with full provenance |
| `POST /api/query` | Natural-language analyst over retrieved records (rate-limited: 20 requests / 60 s per client) |

The frontend requests all records (`status=all`, `limit=500`), which fans out
to every keyless feed (EONET + USGS + NOAA), merges and de-duplicates them, and
labels each response with `source` (a `" · "`-joined label) and
`source_status` — a per-source map of `live` / `cached` / `unavailable`. One
failing source never blocks the others; a source that falls back to its own
persistent cache during an outage is reported as `cached` with a note. Every
count is a count of **feed records retrieved** — never an estimate of
worldwide disaster totals, and absence of a record is not evidence of absence.

## Data sources & provenance

All event feeds are public, keyless HTTP APIs. Shared plumbing in
`app/services/feed_client.py` gives every source connect/read timeouts,
bounded retries with exponential backoff on 5xx/network errors, and a
descriptive User-Agent (required by NWS policy).

### NASA EONET (natural-event catalog; primary)
Public API, no key required (https://eonet.gsfc.nasa.gov/docs/v3).

**Geometry handling (important):** the live EONET v3 feed reports geometry in
a singular `geometry` per event, while archived/legacy payloads use a
`geometries` array. EarthWatch's normaliser accepts **both**, preferring the
live singular key, and derives:

* the first known coordinate pair (for the globe marker),
* the observation date from the earliest dated geometry,
* the latest source-reported date.

Point records map to markers directly. For polygon sources, EarthWatch
**rejects the geometry rather than inventing a centroid** — markers only ever
come from real source coordinates. Events without coordinates remain fully
visible in the panel, labelled *unavailable* on the globe.

**Timeline semantics:** coverage and steps come from source observation dates
(`event_date`, falling back to `updated_at`); the scrubber shows records
observed within `[as-of − window, as-of]`. Records without any source date
cannot be placed on the timeline and are excluded from time-filtered views —
nothing is inferred.

### USGS earthquake feeds (M2.5+)
Public GeoJSON summary feeds (https://earthquake.usgs.gov/feeds/), no key.
Under `status=all`, EarthWatch pulls the **day/week/month** M2.5+ summary
windows (bounded to the strongest events so retrieval size stays predictable)
and files each quake as category *Earthquakes*. Non-"earthquake" feature types
(e.g. quarry blasts) are skipped. Magnitudes below the M2.5 floor absent from
the retrieval are a documented **scope decision**, not data loss.

### NOAA / National Weather Service active alerts
Public CAP alert feed (https://api.weather.gov/alerts/active), no key; a
descriptive User-Agent is sent per API policy. EarthWatch retrieves only the
alerts the source itself grades **Extreme** or **Severe** (routine watches are
out of retrieval scope), and maps the source's own `event` vocabulary to
EarthWatch categories via an explicit rule table in `nws_client.py`
(`NWS_CATEGORY_RULES`): unmatched alert names keep their source title under
*Other*. Alert polygons are stored as geometry and **never converted** to
point markers.

### NOAA NHC — active tropical cyclones
Public `CurrentStorms.json` (https://www.nhc.noaa.gov/) pinned to the storms
active in the current NHC product; a calm basin contributes zero records — a
valid observational fact, not an outage. Storm coordinates go through a
documented tenths-correction guard (e.g. `125` → `12.5°`) for the feed's
integer degree×10 form.

### NOAA Tsunami Program — Pacific bulletins
PTWC PAAQ Atom feed (https://www.tsunami.gov/events/xml/PAAQAtom.xml), parsed
with stdlib XML. Bulletin products carry publication delay and the category is
*Tsunami*; official warning guidance always comes from tsunami.gov and
national agencies. Bulletins without a reported point remain records without
markers.

### Cross-source de-duplication
Earthquakes are frequently co-reported by EONET and the global seismic
networks, so merged results are de-duplicated with **list-order priority**
(EONET first): two earthquake records within 2° of each other and ≤ 60 minutes
apart are collapsed, keeping the higher-priority record. Records are never
merged across sources; the later reporter is simply not repeated.

### Stale / cached semantics
Every `/api/events` call tries each source live first. A source's cache is
used **only** when that source is unreachable, and the response reports
`source_status[name] = "cached"` plus a note naming the fallback. The global
`stale`/`cached` flags apply when the primary source is cache-served. A total
outage with no cache anywhere returns HTTP 503; a legitimately empty result
set from answering sources returns 200 with zero records — absence is a fact.

### NASA GIBS (imagery)
Optional *Daily satellite mosaic* layer drapes a VIIRS true-colour composite
for the **previous UTC day** onto the globe, labelled with that UTC date.
Acquisition and publication are delayed — it is dated imagery, never
real-time, and the UI states this wherever the layer is offered.

### NASA FIRMS (optional, server-side credential)
Enabled only with `FIRMS_API_KEY` in the server-side `.env`. The key is never
sent to the browser; `/api/sources` reports whether it is configured.

## The deterministic analyst (`/api/query`)

A documented rule set — no language model, no external calls — parses
categories, a literal region gazetteer, and natural time windows ("last 7
days", "this quarter"), computes counts over the **records this backend
retrieved**, and returns:

* `answer` — plain language, naturally pluralised,
* `kind` — `ANALYZED` when computable, `UNAVAILABLE` (with reasons) when the
  question cannot be grounded (e.g. a comparison without a time window),
* `filters` — what was matched (category, region, window, counts),
* `evidence` — the records used, clickable in the UI,
* `limitations` — always present, honest about feed incompleteness and
  gazetteer limitations.

EarthWatch never predicts events, never sizes casualties/damage/severity, and
never ranks hazards.

## Insight provenance (event panel)

Each analytical summary reports the conclusion, the data used, the method,
the uncertainty, explicit limitations and the analysis time. Label lifecycle:
**Pending → Analyzing → ANALYZED | UNAVAILABLE**.

## Accessibility & fallbacks

* Full keyboard support: `/` focuses search, combobox semantics with
  ArrowUp/Down/Enter/Escape, ARIA tabs with ArrowLeft/Right/Home/End, labelled
  timeline slider with `aria-valuetext` (dates read "As of YYYY-MM-DD").
* `prefers-reduced-motion` disables ambient effects, auto-rotation and
  fly-to animations. The day/night pass is a computed light position, not an
  animation; the 2D fallback refreshes its terminator once a minute.
* Touch layouts (coarse pointers) enlarge interactive targets and switch the
  globe hint to "Drag to rotate · pinch to zoom · tap a marker".
* Responsive command-center shell down to phone widths (rail and panel become
  sheets); no horizontal page scrolling.
* Graceful degradation: WebGL/Three.js-unavailable browsers get the 2D canvas
  map with identical data, markers, selection and tooltips.

## Security

* Credentials (optional FIRMS key) live only in server-side environment
  variables; nothing is exposed to the frontend.
* Source-derived values are rendered via `textContent`; `innerHTML` is never
  used with untrusted data.
* CORS is configurable (`CORS_ORIGINS`); `*` is the local-development
  default — restrict it in production.
* Pydantic-validated inputs; bounded query parameters; rate-limited analyst.
* Errors return generic JSON bodies — no stack traces or internals leak.
* No URL-fetching endpoints (no SSRF vector); dependencies are pinned.

## Testing

```bash
python -m pytest -q
```

No network and no real database required: every feed (EONET, USGS, NWS, NOAA
NHC/tsunami) is mocked, and a hermetic fixture points SQLite at a temp
directory per session. Coverage includes live singular-`geometry` payloads,
legacy plural `geometries`, polygon rejection, USGS/NWS/NHC/tsunami
normalisers (fixtures of the sources' own shapes, no network), the NWS
category rule table, cross-source merge + de-duplication, per-source
`source_status` honesty (live/cached fallback), aux detail served from
persisted storage, analyst behaviour (parametrised questions), route filters
and validation, and query 422 handling. **Current result: 67 passed.**

### Live verification (optional; server + network)

```bash
python verify.py [host] [port]     # defaults: 127.0.0.1 8000
```

Asserts structure and provenance (health, retrieval shape, **per-source
`source_status` values**, merged source label, category filtering, event and
aux-record detail endpoints, the expanded source registry, imagery notes,
insight kinds and error codes, analyst kinds) — never specific counts. Current
run: **40 checks passed** against the live feeds.

## Known limitations (honest disclosure)

* No feed is a complete census of global events; EONET records may omit
  geometry and are shown without markers (never invented). USGS coverage is
  M2.5+ only; NWS retrieval is limited to Extreme/Severe alerts; the NHC feed
  shows only storms active in the current product and the tsunami feed covers
  Pacific-area bulletins.
* Dates and imagery are subject to source acquisition/publication delay.
* The analyst region matcher is a literal gazetteer, not a geocoder; records
  without place names are not matched.
* Single-process Uvicorn is for local development and small deployments;
  production should front it with a reverse proxy and more workers.
* No predictive hazard models exist here by design; summaries are
  descriptive only.

## Migration path to PostgreSQL/PostGIS

All SQL is isolated in `app/database.py`. Change `DATABASE_URL`, replace the
SQLite helpers with an async PostgreSQL driver, and replay the `CREATE TABLE`
statements as migrations (add PostGIS columns if spatial queries are needed).
Services, routes and the frontend require no changes.

## Attribution & licences

* Data: NASA EONET (public API), USGS earthquake feeds (public domain),
  NOAA/NWS active alerts, NOAA NHC current storms and NOAA tsunami.gov
  bulletins (public domain, National Weather Service data), NASA GIBS imagery
  (NASA EOSDIS) — used per the respective terms.
* Earth day/night textures: NASA visible-Earth imagery distributed with the
  three.js example asset set (three.js r161, MIT licence — loaded via import
  map from unpkg.com).
* Chart.js 4.4.7 — MIT licence, vendored at
  `frontend/vendor/chart.umd.min.js` (licence header retained in the file).
