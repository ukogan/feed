# Open States API v3: CA State Legislature

## What this is

Open States tracks bills, votes, and legislators for all 50 US state legislatures. The API v3 provides structured access to California's legislative data including bill text, roll call votes with individual legislator positions, committee assignments, and legislator contact info. This is the best programmatic source for answering "how did my state legislator vote?" and "what bills are moving on topic X?"

Data is scraped from the official CA Legislature website (leginfo.legislature.ca.gov) and normalized into a consistent schema across all states.

## Base URL

```
https://v3.openstates.org/
```

Interactive docs: `https://v3.openstates.org/docs/`

## Authentication

API key required. Get one free at:
```
https://open.pluralpolicy.com/
```

Pass via header or query parameter:
```
X-API-KEY: {your_key}
# or
?apikey={your_key}
```

## Rate limits

| Tier | Per Minute | Per Day | Notes |
|------|-----------|---------|-------|
| Default (free) | 10 | 500 | Sufficient for interactive queries, not bulk |
| Bronze | 40 | 5,000 | |
| Silver | 80 | 50,000 | |
| Unlimited | 240 | 1,000,000,000 | Contact contact@openstates.org |

For bulk analysis, use the CSV/JSON/PostgreSQL dumps instead of the API (see Bulk Data section below).

## Endpoints

### Bills

**Search bills:**
```
GET /bills?jurisdiction=California&session=2025-2026&q=housing
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `jurisdiction` | string | `California` or OCD jurisdiction ID |
| `session` | string | e.g., `2023-2024`, `2025-2026` |
| `chamber` | string | `upper` (Senate) or `lower` (Assembly) |
| `identifier` | string[] | Bill number, e.g., `AB 1234` |
| `classification` | string | `bill`, `resolution`, `constitutional amendment` |
| `subject` | string[] | Filter by subject tags |
| `q` | string | Full-text search |
| `sponsor` | string | Sponsor name or person ID |
| `updated_since` | string | ISO date, e.g., `2025-01-01` |
| `action_since` | string | Bills with actions after this date |
| `created_since` | string | Bills introduced after this date |
| `sort` | string | `updated_desc`, `latest_action_desc`, `first_action_asc`, etc. |
| `include` | string[] | `sponsorships`, `actions`, `votes`, `documents`, `versions`, `abstracts`, `sources` |
| `page` | int | Default: 1 |
| `per_page` | int | Default: 10 |

**Get specific bill:**
```
GET /bills/California/2023-2024/AB 1234?include=votes&include=sponsorships
```

**Bill response fields:**
- `id`, `identifier`, `title`, `session`
- `classification`, `subject`
- `first_action_date`, `latest_action_date`, `latest_action_description`, `latest_passage_date`
- `created_at`, `updated_at`
- `openstates_url`
- When `include=votes`: array of VoteEvent objects
- When `include=sponsorships`: array of sponsor objects with person details

### Votes (via bill include)

Votes are included inline when you request `include=votes` on a bill query. Each VoteEvent contains:

- `motion_text` - What was being voted on
- `start_date` - When the vote occurred
- `result` - `pass` or `fail`
- `organization` - Which chamber
- `counts` - Array of `{option, value}` (e.g., `{option: "yes", value: 52}`)
- `votes` - Array of individual `{voter_name, option}` records

### People (Legislators)

**Search legislators:**
```
GET /people?jurisdiction=California&org_classification=legislature
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `jurisdiction` | string | `California` |
| `name` | string | Case-insensitive name search |
| `org_classification` | string | `legislature`, `upper`, `lower`, `executive` |
| `district` | string | District number, e.g., `21` |
| `include` | string[] | Additional data to include |

**Geo lookup (find legislators by address):**
```
GET /people.geo?lat=37.485&lng=-122.236
```

### Committees

```
GET /committees?jurisdiction=California
GET /committees/{committee_id}
```

### Jurisdictions

```
GET /jurisdictions
GET /jurisdictions/ocd-jurisdiction/country:us/state:ca/government
```

## How to use

### Search for housing bills in current session

```python
import httpx

API_KEY = "your_key_here"
BASE = "https://v3.openstates.org"

async def search_bills(query: str, session: str = "2025-2026"):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE}/bills",
            params={
                "jurisdiction": "California",
                "session": session,
                "q": query,
                "include": ["sponsorships", "actions"],
                "per_page": 20,
                "sort": "latest_action_desc",
            },
            headers={"X-API-KEY": API_KEY},
        )
        data = resp.json()
        for bill in data["results"]:
            print(f"{bill['identifier']}: {bill['title']}")
            print(f"  Last action: {bill['latest_action_description']}")
            print(f"  Date: {bill['latest_action_date']}")
        return data
```

### Get roll call votes for a specific bill

```python
async def get_bill_votes(session: str, bill_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE}/bills/California/{session}/{bill_id}",
            params={"include": ["votes", "sponsorships"]},
            headers={"X-API-KEY": API_KEY},
        )
        bill = resp.json()
        for vote_event in bill.get("votes", []):
            print(f"\nVote: {vote_event['motion_text']}")
            print(f"Result: {vote_event['result']}")
            for count in vote_event["counts"]:
                print(f"  {count['option']}: {count['value']}")
            # Individual legislator votes
            for vote in vote_event["votes"]:
                print(f"  {vote['voter_name']}: {vote['option']}")
        return bill

# Example: SB 9 (housing duplex bill)
# await get_bill_votes("2021-2022", "SB 9")
```

### Find your legislators by address

```python
async def find_legislators(lat: float, lng: float):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE}/people.geo",
            params={"lat": lat, "lng": lng},
            headers={"X-API-KEY": API_KEY},
        )
        for person in resp.json()["results"]:
            role = person["current_role"]
            print(f"{person['name']} - {role['title']} District {role['district']}")
            print(f"  Party: {person['party']}")
        return resp.json()

# Example: Redwood City
# await find_legislators(37.485, -122.236)
```

## Bulk data (alternative to API)

For analysis requiring more than 500 queries/day, use bulk downloads:

```
https://open.pluralpolicy.com/data/
```

Available formats:
- **CSV** by session (bills, votes, people)
- **JSON** by session (includes full bill text)
- **PostgreSQL dump** (monthly, complete database)

Download pattern:
```
https://data.openstates.org/{YYYY-MM}-public.pgdump
```

## What questions this answers

- How did my state legislator vote on a specific bill?
- What bills have been introduced on a topic (housing, education, public safety)?
- Who sponsored a bill and what party are they in?
- What is the status of a bill -- has it passed committee? Floor vote?
- Which legislators represent my address?
- What committees exist and who sits on them?
- How does a legislator's voting record align with their campaign promises?

### Combining with other data

Join legislator voting records with campaign finance data (CAL-ACCESS) to see if donors correlate with votes. Join bill subjects with spending data to understand whether legislative priorities match budget allocations. Use legislator district info with Census demographics to understand who bills affect.

## Gotchas

- **Session format is `YYYY-YYYY`**: California uses 2-year sessions. Current session (2025-2026) is `2025-2026`. Prior session is `2023-2024`.
- **Bill identifiers include spaces**: Use `AB 1234`, not `AB1234`.
- **`include` must be specified per request**: Votes and sponsorships are not returned by default. Always add `include=votes&include=sponsorships` when you need them.
- **Rate limit is tight on free tier**: 10 req/min and 500/day. Cache aggressively. Use bulk data for analysis.
- **Not real-time**: Data is scraped from leginfo.legislature.ca.gov periodically. There may be a lag of hours to days for new actions.
- **Vote `option` values**: `yes`, `no`, `not voting`, `absent`, `abstain`, `excused`. Different from a simple yes/no.
- **Jurisdiction ID**: You can use either `California` (human-readable) or `ocd-jurisdiction/country:us/state:ca/government` (OCD format).
- **Pagination**: Default is 10 results per page. Maximum is not documented but likely 50-100. Always paginate for comprehensive queries.
- **Subject tags are inconsistent**: Not all bills have subject tags. Full-text search (`q` parameter) is more reliable for topic-based queries.
