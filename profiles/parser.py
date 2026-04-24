"""
Rule-based natural language parser for profile queries.

Supported keywords and their mappings:
  Gender:
    "male", "males", "man", "men", "boy", "boys"       → gender=male
    "female", "females", "woman", "women", "girl", "girls" → gender=female

  Age group keywords:
    "young", "youth"                                    → min_age=16, max_age=24
    "child", "children", "kid", "kids"                  → age_group=child
    "teenager", "teenagers", "teen", "teens", "adolescent" → age_group=teenager
    "adult", "adults"                                   → age_group=adult
    "senior", "seniors", "elderly", "old"               → age_group=senior

  Age phrases:
    "above N", "over N", "older than N"                → min_age=N
    "below N", "under N", "younger than N"             → max_age=N
    "between N and M"                                  → min_age=N, max_age=M
    "aged N"                                           → min_age=N, max_age=N

  Country phrases:
    "from <country>", "in <country>", "of <country>"  → country_id=<ISO2>

  Combined example:
    "young males from nigeria"  → gender=male, min_age=16, max_age=24
    "adult females above 30"    → gender=female, age_group=adult, min_age=30
"""

import re

# Country name → ISO 2-letter code mapping (African + common countries)
COUNTRY_MAP = {
    # Africa
    'nigeria': 'NG', 'nigerian': 'NG',
    'ghana': 'GH', 'ghanaian': 'GH',
    'kenya': 'KE', 'kenyan': 'KE',
    'ethiopia': 'ET', 'ethiopian': 'ET',
    'south africa': 'ZA', 'south african': 'ZA',
    'tanzania': 'TZ', 'tanzanian': 'TZ',
    'uganda': 'UG', 'ugandan': 'UG',
    'angola': 'AO', 'angolan': 'AO',
    'senegal': 'SN', 'senegalese': 'SN',
    'cameroon': 'CM', 'cameroonian': 'CM',
    'ivory coast': 'CI', "cote d'ivoire": 'CI', 'côte divoire': 'CI',
    'mali': 'ML', 'malian': 'ML',
    'burkina faso': 'BF',
    'niger': 'NE', 'nigerien': 'NE',
    'benin': 'BJ', 'beninese': 'BJ',
    'togo': 'TG', 'togolese': 'TG',
    'guinea': 'GN', 'guinean': 'GN',
    'guinea-bissau': 'GW',
    'sierra leone': 'SL',
    'liberia': 'LR', 'liberian': 'LR',
    'gambia': 'GM', 'gambian': 'GM',
    'cape verde': 'CV',
    'mauritania': 'MR',
    'morocco': 'MA', 'moroccan': 'MA',
    'algeria': 'DZ', 'algerian': 'DZ',
    'tunisia': 'TN', 'tunisian': 'TN',
    'libya': 'LY', 'libyan': 'LY',
    'egypt': 'EG', 'egyptian': 'EG',
    'sudan': 'SD', 'sudanese': 'SD',
    'south sudan': 'SS',
    'somalia': 'SO', 'somali': 'SO',
    'djibouti': 'DJ',
    'eritrea': 'ER', 'eritrean': 'ER',
    'rwanda': 'RW', 'rwandan': 'RW',
    'burundi': 'BI', 'burundian': 'BI',
    'mozambique': 'MZ', 'mozambican': 'MZ',
    'zambia': 'ZM', 'zambian': 'ZM',
    'zimbabwe': 'ZW', 'zimbabwean': 'ZW',
    'malawi': 'MW', 'malawian': 'MW',
    'botswana': 'BW', 'motswana': 'BW',
    'namibia': 'NA', 'namibian': 'NA',
    'lesotho': 'LS',
    'eswatini': 'SZ', 'swaziland': 'SZ',
    'madagascar': 'MG', 'malagasy': 'MG',
    'comoros': 'KM',
    'mauritius': 'MU', 'mauritian': 'MU',
    'seychelles': 'SC',
    'democratic republic of congo': 'CD', 'dr congo': 'CD', 'drc': 'CD',
    'republic of congo': 'CG', 'congo': 'CG',
    'gabon': 'GA', 'gabonese': 'GA',
    'equatorial guinea': 'GQ',
    'sao tome': 'ST',
    'central african republic': 'CF',
    'chad': 'TD', 'chadian': 'TD',
    # Rest of world
    'usa': 'US', 'united states': 'US', 'america': 'US', 'american': 'US',
    'uk': 'GB', 'united kingdom': 'GB', 'britain': 'GB', 'british': 'GB',
    'canada': 'CA', 'canadian': 'CA',
    'australia': 'AU', 'australian': 'AU',
    'france': 'FR', 'french': 'FR',
    'germany': 'DE', 'german': 'DE',
    'italy': 'IT', 'italian': 'IT',
    'spain': 'ES', 'spanish': 'ES',
    'portugal': 'PT', 'portuguese': 'PT',
    'brazil': 'BR', 'brazilian': 'BR',
    'india': 'IN', 'indian': 'IN',
    'china': 'CN', 'chinese': 'CN',
    'japan': 'JP', 'japanese': 'JP',
    'south korea': 'KR', 'korean': 'KR',
    'indonesia': 'ID', 'indonesian': 'ID',
    'pakistan': 'PK', 'pakistani': 'PK',
    'bangladesh': 'BD', 'bangladeshi': 'BD',
    'mexico': 'MX', 'mexican': 'MX',
    'argentina': 'AR', 'argentinian': 'AR',
    'colombia': 'CO', 'colombian': 'CO',
}

MALE_TERMS = {'male', 'males', 'man', 'men', 'boy', 'boys'}
FEMALE_TERMS = {'female', 'females', 'woman', 'women', 'girl', 'girls'}

CHILD_TERMS = {'child', 'children', 'kid', 'kids'}
TEEN_TERMS = {'teenager', 'teenagers', 'teen', 'teens', 'adolescent', 'adolescents'}
ADULT_TERMS = {'adult', 'adults'}
SENIOR_TERMS = {'senior', 'seniors', 'elderly', 'old'}
YOUNG_TERMS = {'young', 'youth'}


def parse_natural_language_query(query: str) -> dict | None:
    """
    Parse a plain-English query into filter kwargs.
    Returns a dict of filters, or None if the query cannot be interpreted.
    """
    if not query or not query.strip():
        return None

    q = query.lower().strip()
    filters = {}
    matched_something = False

    # --- Gender ---
    words = set(re.findall(r'\b\w+\b', q))
    if words & MALE_TERMS:
        filters['gender'] = 'male'
        matched_something = True
    if words & FEMALE_TERMS:
        # "male and female" → both, so remove gender filter
        if 'gender' in filters:
            del filters['gender']
        else:
            filters['gender'] = 'female'
        matched_something = True

    # --- Age group / Young mapping ---
    if words & YOUNG_TERMS:
        filters['min_age'] = 16
        filters['max_age'] = 24
        matched_something = True
    elif words & CHILD_TERMS:
        filters['age_group'] = 'child'
        matched_something = True
    elif words & TEEN_TERMS:
        filters['age_group'] = 'teenager'
        matched_something = True
    elif words & ADULT_TERMS:
        filters['age_group'] = 'adult'
        matched_something = True
    elif words & SENIOR_TERMS:
        filters['age_group'] = 'senior'
        matched_something = True

    # --- Age phrases ---
    # "between N and M"
    between_match = re.search(r'\bbetween\s+(\d+)\s+and\s+(\d+)\b', q)
    if between_match:
        filters['min_age'] = int(between_match.group(1))
        filters['max_age'] = int(between_match.group(2))
        matched_something = True

    # "above N", "over N", "older than N"
    above_match = re.search(r'\b(?:above|over|older than)\s+(\d+)\b', q)
    if above_match:
        filters['min_age'] = int(above_match.group(1))
        matched_something = True

    # "below N", "under N", "younger than N"
    below_match = re.search(r'\b(?:below|under|younger than)\s+(\d+)\b', q)
    if below_match:
        filters['max_age'] = int(below_match.group(1))
        matched_something = True

    # "aged N"
    aged_match = re.search(r'\baged?\s+(\d+)\b', q)
    if aged_match:
        age_val = int(aged_match.group(1))
        filters['min_age'] = age_val
        filters['max_age'] = age_val
        matched_something = True

    # --- Country ---
    # Try multi-word country names first (longest match wins)
    sorted_countries = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)

    country_phrase_match = re.search(
        r'\b(?:from|in|of)\s+(.+?)(?:\s+(?:and|with|who|where|above|below|over|under)|$)', q
    )
    if country_phrase_match:
        candidate = country_phrase_match.group(1).strip().rstrip('s')  # rough desuffix
        # Try exact match and stripped versions
        for name in sorted_countries:
            if candidate == name or q.find(name) != -1:
                filters['country_id'] = COUNTRY_MAP[name]
                matched_something = True
                break
    else:
        # Fallback: scan for any known country name in query
        for name in sorted_countries:
            if re.search(r'\b' + re.escape(name) + r'\b', q):
                filters['country_id'] = COUNTRY_MAP[name]
                matched_something = True
                break

    if not matched_something:
        return None

    return filters
