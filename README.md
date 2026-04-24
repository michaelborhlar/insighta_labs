# Insighta Labs — Intelligence Query Engine

A Django REST API for querying demographic profile data with advanced filtering, sorting, pagination, and natural language search.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Seed the database (safe to re-run — no duplicates created)
python manage.py seed_profiles --file profiles.json

# 4. Run the server
python manage.py runserver
```

For production:
```bash
gunicorn insighta_labs.wsgi --bind 0.0.0.0:8000
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | (insecure default) | Django secret key |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `DATABASE_URL` | SQLite | Set PostgreSQL URL for production |

---

## API Endpoints

### `GET /api/profiles`

Returns all profiles with support for filtering, sorting, and pagination.

**Filters**

| Parameter | Type | Example |
|---|---|---|
| `gender` | `male` \| `female` | `?gender=male` |
| `age_group` | `child` \| `teenager` \| `adult` \| `senior` | `?age_group=adult` |
| `country_id` | ISO 2-letter code | `?country_id=NG` |
| `min_age` | integer | `?min_age=25` |
| `max_age` | integer | `?max_age=40` |
| `min_gender_probability` | float 0–1 | `?min_gender_probability=0.9` |
| `min_country_probability` | float 0–1 | `?min_country_probability=0.8` |

**Sorting**

| Parameter | Values | Default |
|---|---|---|
| `sort_by` | `age` \| `created_at` \| `gender_probability` | `created_at` |
| `order` | `asc` \| `desc` | `asc` |

**Pagination**

| Parameter | Default | Max |
|---|---|---|
| `page` | `1` | — |
| `limit` | `10` | `50` |

**Example:**
```
GET /api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

**Success Response (200):**
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 482,
  "data": [
    {
      "id": "019500a1-3b2c-7d4e-9f01-23456789abcd",
      "name": "emmanuel",
      "gender": "male",
      "gender_probability": 0.99,
      "age": 34,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.85,
      "created_at": "2026-04-01T12:00:00Z"
    }
  ]
}
```

---

### `GET /api/profiles/search?q=<query>`

Parses a plain-English query and returns matching profiles.

**Example:**
```
GET /api/profiles/search?q=young males from nigeria
GET /api/profiles/search?q=adult females above 30&page=2&limit=20
```

Pagination (`page`, `limit`) also applies here.

---

## Natural Language Parser

### Approach

The parser is **fully rule-based** — no AI or LLMs involved. It works by scanning the query string for specific keywords and phrase patterns using Python string matching and regular expressions, then mapping them to database filter parameters.

Processing steps:
1. Lowercase and tokenize the query
2. Match gender keywords
3. Match age-group keywords or "young/youth" (special mapping)
4. Match age comparison phrases (above, below, between, aged)
5. Match country names/adjectives via a lookup table
6. If nothing matched, return `Unable to interpret query`

### Supported Keywords

**Gender**

| Keywords | Maps to |
|---|---|
| `male`, `males`, `man`, `men`, `boy`, `boys` | `gender=male` |
| `female`, `females`, `woman`, `women`, `girl`, `girls` | `gender=female` |
| `male and female` (both present) | gender filter removed (both) |

**Age groups**

| Keywords | Maps to |
|---|---|
| `young`, `youth` | `min_age=16`, `max_age=24` (not a stored age_group) |
| `child`, `children`, `kid`, `kids` | `age_group=child` |
| `teenager`, `teenagers`, `teen`, `teens`, `adolescent` | `age_group=teenager` |
| `adult`, `adults` | `age_group=adult` |
| `senior`, `seniors`, `elderly`, `old` | `age_group=senior` |

**Age comparisons**

| Phrase | Maps to |
|---|---|
| `above N`, `over N`, `older than N` | `min_age=N` |
| `below N`, `under N`, `younger than N` | `max_age=N` |
| `between N and M` | `min_age=N`, `max_age=M` |
| `aged N` | `min_age=N`, `max_age=N` |

**Countries** — The parser supports ~70 countries by name and common adjective form. Examples:

| Query phrase | Maps to |
|---|---|
| `from nigeria` / `nigerian` | `country_id=NG` |
| `from kenya` / `kenyan` | `country_id=KE` |
| `in south africa` | `country_id=ZA` |
| `from angola` | `country_id=AO` |
| `people from ghana` | `country_id=GH` |

Full country list covers all 54 African nations plus major world countries.

### Example Mappings

| Query | Filters applied |
|---|---|
| `young males` | `gender=male`, `min_age=16`, `max_age=24` |
| `females above 30` | `gender=female`, `min_age=30` |
| `people from angola` | `country_id=AO` |
| `adult males from kenya` | `gender=male`, `age_group=adult`, `country_id=KE` |
| `male and female teenagers above 17` | `age_group=teenager`, `min_age=17` |
| `elderly women in nigeria` | `gender=female`, `age_group=senior`, `country_id=NG` |

---

## Limitations & Known Edge Cases

1. **"young" is not an age_group.** It maps to `min_age=16, max_age=24` for query purposes only. If a profile's `age_group` is `teenager` and age is 20, it will appear in "young" results, but not vice versa.

2. **Ambiguous "old"** — "old" maps to `senior`. The phrase "30-year-old" may partially match. Use `aged 30` or `above 30` instead.

3. **"niger" vs "nigeria"** — The parser tries longest-match first to avoid `niger` matching inside `nigeria`. However, extremely short queries like just `niger` may behave unexpectedly in some edge cases.

4. **No multi-country support** — "from nigeria or kenya" only picks up the first matched country.

5. **No negation** — "not male" or "excluding adults" is not supported; the parser ignores negation words.

6. **No compound age groups** — "teenagers and adults" results in whichever is matched last. Only one age_group filter is applied per query.

7. **No typo tolerance** — Misspelled words (e.g. "nigria", "femal") will not match. Queries must use correct spellings.

8. **No pronoun handling** — "them", "those people", "everyone" are not mapped to any filter and will return `Unable to interpret query` on their own.

9. **Adjective countries without prepositions** — "nigerian males" works. But "males nigerian" (reversed without a preposition) may not reliably match the country if the order is unusual.

10. **"above/below" with age_group** — If both a min_age and an age_group are specified (e.g. `teenagers above 17`), both filters are applied independently. A profile must satisfy both to appear.

---

## Database Schema

```
profiles
├── id               UUID v7       Primary key (time-ordered)
├── name             VARCHAR       Unique
├── gender           VARCHAR       "male" | "female"
├── gender_probability FLOAT
├── age              INT
├── age_group        VARCHAR       child | teenager | adult | senior
├── country_id       VARCHAR(2)    ISO 2-letter code
├── country_name     VARCHAR
├── country_probability FLOAT
└── created_at       TIMESTAMP     UTC, auto-generated
```

Indexes on: `gender`, `age_group`, `country_id`, `age`, `gender_probability`, `country_probability`, `created_at`.

---

## Error Responses

All errors follow this format:
```json
{ "status": "error", "message": "<description>" }
```

| HTTP Code | Meaning |
|---|---|
| 400 | Missing or empty parameter |
| 404 | Profile not found |
| 422 | Invalid parameter type or value |
| 500 | Server error |

---

## Deployment Notes

- **CORS**: All origins are allowed (`Access-Control-Allow-Origin: *`) as required.
- **Timestamps**: All returned in UTC ISO 8601 format.
- **IDs**: UUID v7 (time-ordered) generated server-side.
- **Seeding**: `python manage.py seed_profiles --file profiles.json` is idempotent — safe to run multiple times.
