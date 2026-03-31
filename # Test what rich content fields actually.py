API_URL = "https://api.ted.europa.eu/v3/notices/search"

FIELDS = [
    # Identity
    "publication-number",
    "notice-type",
    "publication-date",
    "form-type",
    "legal-basis",

    # Buyer
    "buyer-name",
    "buyer-country",
    "buyer-city",
    "buyer-legal-type",

    # What is being procured — THE RICH FIELDS
    "notice-title",
    "title-lot",
    "description-lot",
    "additional-information-lot",
    "classification-cpv",
    "contract-nature",
    "procedure-type",

    # Requirements & criteria
    "selection-criterion-description-lot",
    "selection-criterion-name-lot",
    "award-criterion-description-lot",
    "award-criterion-type-lot",
    "exclusion-grounds-description",

    # Value & duration
    "estimated-value-lot",
    "estimated-value-glo",
    "contract-duration-period-lot",
    "duration-period-value-lot",
    "duration-period-unit-lot",

    # Deadline & place
    "deadline-receipt-request",
    "deadline-receipt-tender-date-lot",
    "place-of-performance",
    "place-of-performance-country-lot",
    "place-of-performance-city-lot",

    # Winner info
    "winner-name",
    "winner-country",
    "winner-city",
    "winner-selection-status",

    # SME & GPA flags
    "sme-lot",
    "gpa-lot",
    "electronic-submission-lot",
    "subcontracting-obligation-lot",
]

def fetch_notices_batch(page: int, limit: int = 100) -> dict:
    payload = {
        "query": "notice-type IN [cn-standard, can-standard, cn-social] AND publication-date >= 20240101",
        "fields": FIELDS,
        "limit": limit,
        "page": page,
        "scope": "ACTIVE",
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code}: {response.text[:300]}")
        response.raise_for_status()
    return response.json()

# Drop and re-ingest
collection.drop()
clean_collection.drop()
print("🗑️  Dropped old collections")

MAX_PAGES = 10
inserted_total = 0

for page in range(1, MAX_PAGES + 1):
    print(f"Fetching page {page}/{MAX_PAGES}...", end=" ")
    try:
        data = fetch_notices_batch(page=page, limit=100)
        notices = data.get("notices", [])
        if not notices:
            print("No more results.")
            break
        for notice in notices:
            collection.update_one(
                {"publication-number": notice.get("publication-number")},
                {"$setOnInsert": notice},
                upsert=True
            )
        inserted_total += len(notices)
        print(f"✅ {len(notices)} notices. Total: {inserted_total}")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Error on page {page}: {e}")
        break

print(f"\n🎉 Done! Total in MongoDB: {collection.count_documents({})}")