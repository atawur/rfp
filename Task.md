# RFP Scraping System — Long-Term Architecture & LLM Cost Optimization

## 1. Objective

We currently scrape approximately 500 websites per day to discover RFP / Request for Proposal / tender / procurement opportunities.

The current architecture calls the LLM individually while processing websites, which creates a significant API billing impact.

I want to refactor the system into a scalable, production-quality pipeline that minimizes LLM usage while preserving or improving extraction accuracy.

### Current flow

```text
Website
   ↓
Playwright / BeautifulSoup
   ↓
LLM
   ↓
Structured RFP
   ↓
Validation
   ↓
Database
```

### Target flow

```text
500 Websites
      ↓
Scraping
      ↓
Dynamic Content Normalization
      ↓
RFP Candidate Discovery
      ↓
Content Fingerprint / SHA-256 Hash
      ↓
Check Previous Version
      │
      ├── UNCHANGED → SKIP
      │
      └── NEW/CHANGED
              ↓
      Deterministic Extraction
              ↓
          Validation
              ↓
        Confidence Check
          /          \
       HIGH          LOW
        ↓             ↓
      SAVE       LLM QUEUE
                      ↓
                Batch Processing
                      ↓
                     LLM
                      ↓
          RFP + Category Extraction
                      ↓
                  Validation
                      ↓
                     SAVE
```

The most important architectural requirement is:

> **The LLM must NOT be called inside the main loop that scrapes the 500 websites.**

The scraper should collect and prepare the work first. LLM processing should happen afterward through a queue/batch layer.

---

# 2. First inspect the existing project

Before modifying code, inspect the existing implementation thoroughly.

Identify:

* scraper entry points
* Playwright implementation
* BeautifulSoup implementation
* website configuration
* RFP page configuration
* URL discovery
* current LLM calls
* OpenAI/Gemini integration
* current prompts
* current RFP schema
* category schema
* validation
* database models
* duplicate handling
* scheduling
* retries
* caching
* logging
* existing website-specific selectors/parsers
* current UI fields and their backend sources

Do not assume the architecture.

Do not immediately rewrite the system.

First understand the existing implementation and identify the minimum safe migration path.

---

# 3. Do NOT create one parser for every website

There are approximately 500 websites and they have different HTML structures.

Do NOT build:

```text
CityBankParser
Bank2Parser
Bank3Parser
...
500 custom parsers
```

as the primary solution.

Instead build a generic extraction/normalization layer that works across arbitrary websites.

The website may expose information through:

* `<title>`
* `<h1>`
* `<h2>`
* `<main>`
* `<article>`
* `<section>`
* tables
* JSON-LD
* Schema.org
* OpenGraph metadata
* links
* visible text
* PDF links
* downloadable documents

The system must dynamically discover these.

---

# 4. Create a normalized internal document

After Playwright loads the page, obtain the rendered HTML.

Use BeautifulSoup to normalize it.

Create a generic internal representation such as:

```json
{
  "source": {
    "url": "...",
    "domain": "...",
    "website_name": "..."
  },
  "page": {
    "title": "...",
    "headings": [],
    "text": "...",
    "metadata": {}
  },
  "links": [
    {
      "text": "...",
      "url": "...",
      "type": "html|pdf|doc|docx|other"
    }
  ]
}
```

This is an INTERNAL normalized representation.

It does NOT mean that every website has fields named:

* title
* content
* links

in the same HTML location.

The normalization layer dynamically derives those values.

---

# 5. Dynamic title extraction

Implement generic title extraction.

Recommended fallback order:

1. `<title>`
2. `<h1>`
3. OpenGraph title
4. useful metadata
5. empty value

For Playwright, `page.title()` may be used.

For BeautifulSoup:

```python
title_tag = soup.find("title")
```

If no `<title>` exists, try meaningful headings and metadata.

Do not create website-specific selectors for basic title extraction.

---

# 6. Dynamic content extraction

Do not send raw HTML to the LLM.

Create a generic content-cleaning layer.

Remove irrelevant content where appropriate:

* script
* style
* advertisements
* tracking
* cookie banners
* navigation
* repeated menus
* irrelevant sidebars
* irrelevant footer content

Preserve:

* headings
* paragraphs
* tables
* lists
* relevant visible text
* important metadata
* document links

Prefer semantic elements:

```text
main
article
section
h1-h6
table
```

When semantic structure is unavailable, use a generic content-density approach.

The goal is to produce compact, meaningful RFP content.

---

# 7. Dynamic link extraction

Extract links generically from the DOM.

For each relevant link capture:

```json
{
  "text": "...",
  "url": "...",
  "type": "pdf"
}
```

Normalize relative URLs into absolute URLs.

Detect document types such as:

* PDF
* DOC
* DOCX
* XLS
* XLSX
* HTML

Use generic signals to identify likely RFP/tender documents.

Examples of URL keywords:

```text
rfp
tender
procurement
proposal
bid
notice
```

Examples of link text:

```text
RFP
Request for Proposal
Request for Quotation
Tender
Tender Notice
Procurement
Proposal
Bid Document
Download RFP
Download Tender
```

These should be used for candidate discovery, not final semantic classification.

---

# 8. Separate discovery from extraction

The system must distinguish:

### RFP discovery

Find pages/documents that potentially contain RFP information.

### RFP extraction

Extract the structured fields from those candidates.

Do not call the LLM simply because a website was scraped.

The scraper should first determine whether there is potentially relevant RFP content.

---

# 9. Content normalization before hashing

This is critical.

Do NOT calculate the hash directly from raw HTML.

Use:

```text
Raw HTML
    ↓
Remove noise
    ↓
Extract relevant content
    ↓
Normalize whitespace
    ↓
Normalize URLs
    ↓
Normalize text
    ↓
Normalized relevant content
    ↓
SHA-256
```

The normalized content should avoid volatile information where practical, including:

* tracking IDs
* random HTML attributes
* irrelevant timestamps
* advertisements
* navigation
* counters
* dynamically changing unrelated content

The hash should represent the meaningful RFP content.

---

# 10. SHA-256 content fingerprinting

For every candidate RFP/page, calculate a stable fingerprint:

```text
content_hash = SHA256(normalized_relevant_content)
```

Persist at least:

```text
source_url
normalized_url
content_hash
first_seen_at
last_seen_at
last_processed_at
extraction_version
parser_version
```

The hash is a core part of the architecture.

---

# 11. Change detection behavior

For every scraped candidate:

### Case 1 — New URL

```text
URL does not exist
        ↓
NEW
        ↓
Process
```

### Case 2 — Existing URL + same hash

```text
URL exists
+
hash unchanged
        ↓
UNCHANGED
        ↓
SKIP
```

Do NOT call the LLM.

Reuse the existing extracted result.

### Case 3 — Existing URL + different hash

```text
URL exists
+
hash changed
        ↓
CHANGED
        ↓
Process again
```

This means a deadline change, title change, description change, or newly added RFP can trigger reprocessing.

---

# 12. Explicit hash tests

Implement tests for:

### Same content

```text
Run 1 → hash ABC
Run 2 → hash ABC
```

Expected:

```text
UNCHANGED
LLM NOT CALLED
```

### Deadline changes

```text
Run 1:
Deadline = Sep 30

Run 2:
Deadline = Oct 5
```

Expected:

```text
Different hash
LLM processing required
```

### Navigation/tracking changes

If only irrelevant content changes:

```text
tracking ID changed
navigation changed
ad changed
```

but meaningful RFP content is identical:

Expected:

```text
Same normalized content
Same hash
LLM NOT CALLED
```

### New RFP added

If an RFP listing page contains one additional RFP:

Expected:

```text
Meaningful normalized content changes
Different hash
Reprocess
```

If practical, prefer identifying individual RFP/document URLs and hashing individual RFP content so that adding one RFP does not unnecessarily reprocess unrelated RFPs.

---

# 13. Prefer RFP-level change detection where possible

If the page contains a list of multiple RFPs, do not necessarily treat the entire page as one document.

Prefer:

```text
RFP listing page
       ↓
discover individual RFP links
       ↓
individual RFP/document
       ↓
individual content hash
```

Example:

```text
City Bank RFP page
    ├── RFP A → hash A
    ├── RFP B → hash B
    └── RFP C → hash C
```

Tomorrow:

```text
RFP A → same hash → SKIP
RFP B → same hash → SKIP
RFP C → changed hash → PROCESS
RFP D → new → PROCESS
```

This is much more cost-efficient than hashing and reprocessing the entire listing page every day.

Use the page-level hash only when individual RFP-level identification is not possible.

---

# 14. Deterministic extraction before LLM

Before adding content to the LLM queue, try deterministic extraction.

Use:

* JSON-LD
* Schema.org
* HTML tables
* headings
* labels
* metadata
* dates
* email addresses
* phone numbers
* document links
* reference number patterns
* deadline patterns

Potential RFP fields:

```json
{
  "title": "",
  "reference_number": "",
  "organization": "",
  "category": "",
  "description": "",
  "published_date": null,
  "submission_deadline": null,
  "opening_date": null,
  "contact_name": "",
  "contact_email": "",
  "contact_phone": "",
  "document_urls": [],
  "source_url": "",
  "status": ""
}
```

Use the existing application's schema if it already exists.

Do not create a conflicting second RFP schema.

---

# 15. Category information is REQUIRED

The existing UI requires category information.

The category currently contains information such as:

```text
Category:
Cybersecurity

Confidence:
90%

Type:
Product

Scope:
SOC
```

Another RFP may show:

```text
Category:
Hardware

Confidence:
90%

Type:
Product

Scope:
power management
```

The new architecture MUST preserve this information.

Do not optimize scraping in a way that removes category classification.

---

# 16. Controlled category taxonomy

Do not allow the LLM to freely invent categories.

Create/use a controlled taxonomy from the existing application.

Conceptually:

```text
Cybersecurity
Hardware
Software
Networking
Cloud
Telecommunications
Professional Services
Consulting
Construction
...
```

Use the actual existing category list if one exists.

The LLM must select the category from the application's allowed taxonomy.

If no suitable category exists, use the application's existing fallback behavior rather than inventing arbitrary categories.

---

# 17. Category extraction schema

The extraction result should support the UI requirements.

Conceptually:

```json
{
  "category": {
    "name": "Cybersecurity",
    "confidence": 0.90,
    "type": "Product",
    "scope": [
      "SOC"
    ]
  }
}
```

For example:

```json
{
  "category": {
    "name": "Hardware",
    "confidence": 0.90,
    "type": "Product",
    "scope": [
      "power management"
    ]
  }
}
```

Reuse the existing backend/category model if available.

Do not create duplicate category concepts.

---

# 18. Category confidence

The confidence value must represent the confidence of the classification.

Do not allow the LLM to generate an arbitrary high confidence just because it is uncertain.

Prefer a controlled methodology.

If possible, validate confidence using deterministic evidence or calibrated evaluation rather than treating an LLM-generated number as ground truth.

At minimum, store:

```text
category
category_confidence
category_type
category_scope
```

---

# 19. LLM responsibility

The LLM should perform tasks that require semantic understanding.

The LLM may be responsible for:

* identifying the actual RFP title
* understanding ambiguous RFP descriptions
* extracting fields from unstructured text
* identifying the appropriate category
* identifying product/service type
* identifying scope/subcategory
* resolving ambiguous dates/fields

The LLM should NOT be responsible for:

* parsing raw HTML
* removing scripts
* extracting every `<a>`
* resolving relative URLs
* calculating hashes
* detecting whether content changed
* simple regex extraction
* database deduplication

Those should be deterministic application responsibilities.

---

# 20. LLM queue

During scraping:

```python
for website in websites:

    scrape()

    normalize()

    discover_rfp()

    calculate_hash()

    check_hash()

    if unchanged:
        continue

    deterministic_extract()

    validate()

    if high_confidence:
        save()
    else:
        llm_queue.append(...)
```

Do not call the LLM here.

After all websites have been scraped:

```python
process_llm_queue()
```

---

# 21. LLM batching

Do NOT make one huge LLM request containing all 500 websites.

Instead:

```text
500 websites
     ↓
new/changed/low-confidence RFPs
     ↓
LLM queue
     ↓
manageable batches
     ↓
LLM
```

Example:

```text
Batch 1
Batch 2
Batch 3
...
```

Batch size must be configurable.

Choose the batch size based on:

* model context limits
* average document size
* API limits
* expected output size
* reliability
* retry behavior

Do not assume that fewer HTTP requests automatically means lower token cost.

---

# 22. LLM input optimization

The LLM should receive the normalized relevant RFP content.

Do NOT send:

* raw HTML
* JavaScript
* CSS
* navigation
* advertisements
* cookie banners
* irrelevant footer
* tracking information
* duplicated content

Prefer:

```json
{
  "source": {
    "url": "...",
    "domain": "..."
  },
  "page": {
    "title": "...",
    "headings": [],
    "text": "..."
  },
  "links": []
}
```

This significantly reduces unnecessary input tokens.

---

# 23. LLM structured output

Use structured output / JSON schema support from the currently configured OpenAI/Gemini integration.

The LLM must return the application's structured RFP schema.

Conceptually:

```json
{
  "title": "",
  "reference_number": "",
  "organization": "",
  "description": "",
  "published_date": null,
  "submission_deadline": null,
  "document_urls": [],
  "category": {
    "name": "",
    "confidence": 0.0,
    "type": "",
    "scope": []
  }
}
```

Use the actual existing schema if different.

Do not introduce an incompatible response format.

---

# 24. LLM caching

Before an LLM request, check whether the normalized content has already been processed.

Cache key should incorporate:

```text
content_hash
+
prompt_version
+
schema_version
+
model/version if necessary
```

If the exact content has already been successfully processed with the same relevant versions:

```text
reuse previous LLM result
```

Do NOT call the LLM again.

---

# 25. Extraction versioning

Version:

* normalized content logic
* deterministic extraction
* parser
* prompt
* RFP schema
* category taxonomy

Example:

```text
normalizer_version = 2
parser_version = 3
prompt_version = 5
schema_version = 2
```

If the prompt/schema changes, old LLM results should not incorrectly satisfy the new version.

---

# 26. Website-specific parser registry

Create an extensible parser architecture.

Conceptually:

```text
ExtractionParser
    ├── GenericParser
    ├── JSONLDParser
    ├── TableParser
    └── WebsiteSpecificParser
```

The core pipeline should not know individual parser implementation details.

Do not create parsers for all 500 websites.

Instead:

```text
Generic parser
     ↓
failure metrics
     ↓
identify frequently failing websites
     ↓
create dedicated parser only where justified
```

This allows the system to become cheaper over time.

---

# 27. Validation

Both deterministic and LLM extraction must use the same validation layer.

Validate:

* required fields
* dates
* deadline
* URLs
* email addresses
* reference numbers
* organization
* category
* category type
* category confidence
* scope
* duplicate RFPs

Do not trust an LLM response simply because it is valid JSON.

```text
Valid JSON ≠ Valid RFP
```

---

# 28. Duplicate detection

Do not create duplicate RFP records.

Use appropriate identifiers where available:

* normalized source URL
* document URL
* reference number
* content hash
* organization
* title
* other existing identifiers

Inspect the current database and reuse existing deduplication mechanisms where possible.

---

# 29. Database changes

Inspect the existing schema first.

Only add fields/tables where necessary.

The system should be able to persist:

```text
source_url
normalized_url
content_hash
extracted_rfp
category
category_confidence
category_type
category_scope
extraction_method
confidence
parser_version
extraction_version
first_seen_at
last_seen_at
last_processed_at
```

Do not duplicate existing entities.

Use migrations if schema changes are required.

---

# 30. Observability

Add metrics that clearly show the cost reduction.

At minimum:

```text
total_websites
successful_scrapes
failed_scrapes

rfp_candidates
new_rfps
changed_rfps
unchanged_rfps

deterministic_extractions
llm_queue_size
llm_extractions

llm_calls
llm_cache_hits

validation_failures
extraction_failures
```

Track LLM usage where available:

```text
provider
model
input_tokens
output_tokens
latency
```

At the end of a run, produce something like:

```text
Websites: 500
Successful: 492
Failed: 8

RFP candidates: 140

Unchanged: 90
New: 35
Changed: 15

Deterministic extraction: 32
LLM fallback: 18

LLM batches: 4
LLM cache hits: 7
```

This allows actual measurement rather than assumptions.

---

# 31. Error handling

A failed website must not stop the other 499 websites.

A failed LLM batch must not invalidate successful batches.

Use existing retry mechanisms where possible.

Avoid infinite retries.

Persist failures for later investigation.

---

# 32. Performance

Do not unnecessarily serialize the entire scraping process.

The architecture should allow:

```text
Scraping phase
    ↓
queue new/changed items
    ↓
LLM processing phase
```

The scraping phase may continue using the existing concurrency model.

The LLM processing phase should have configurable concurrency/rate limiting appropriate for the provider.

Do not create uncontrolled parallel LLM requests.

---

# 33. Testing

Create tests covering multiple website structures.

Test:

### Generic extraction

* `<title>`
* `<h1>` fallback
* OpenGraph title
* semantic main content
* article content
* table content
* links
* relative URL normalization
* PDF detection
* JSON-LD

### Change detection

* new URL
* unchanged content
* changed deadline
* changed title
* changed document
* irrelevant navigation change
* tracking change
* newly added RFP

### LLM pipeline

* queue creation
* batching
* structured output
* validation
* cache hit
* cache miss
* failed batch
* retry
* partial failure

### Category

* valid category
* invalid category
* category confidence
* Product type
* Service type
* scope
* controlled taxonomy enforcement

Use multiple representative HTML fixtures.

Do not test only City Bank.

---

# 34. Migration strategy

Do this incrementally.

## Phase 1

Introduce normalized scraped document.

Do not change LLM behavior yet.

```text
scrape
→ normalize
→ existing LLM
```

Verify output remains unchanged.

## Phase 2

Add normalized content hashing.

```text
scrape
→ normalize
→ hash
→ detect change
→ existing LLM
```

Verify unchanged content is skipped.

## Phase 3

Move LLM processing outside the scraping loop.

```text
scrape all
→ queue
→ LLM batches
```

## Phase 4

Add deterministic extraction.

```text
scrape
→ normalize
→ hash
→ deterministic extraction
→ LLM only when needed
```

## Phase 5

Add confidence scoring.

## Phase 6

Add LLM cache.

## Phase 7

Add parser registry.

## Phase 8

Add complete cost/quality monitoring.

After each phase:

* run existing tests
* run new tests
* compare RFP output
* compare category output
* verify database integrity
* verify existing application behavior

---

# 35. Backward compatibility

Do not break:

* Playwright scraping
* BeautifulSoup processing
* existing website configuration
* existing RFP schema
* category information
* existing validation
* existing database behavior
* existing scheduling
* existing API
* existing frontend

The UI must continue to display information such as:

```text
RFP Title & Reference
Category & Scope
Organization
Budget
Deadline
Date Crawled
Status
Actions
```

And category information must continue to support:

```text
Category
Confidence
Type
Scope
```

Do not remove existing fields merely to simplify the extraction pipeline.

---

# 36. Important cost principle

Do not optimize only for API request count.

The real objective is:

```text
Lower token cost
+
fewer LLM calls
+
high extraction accuracy
+
high reliability
```

The main cost reductions should come from:

1. Skip unchanged content using normalized SHA-256 hashing.
2. Prefer RFP-level hashing when possible.
3. Do not send raw HTML.
4. Remove irrelevant content before LLM.
5. Extract obvious fields deterministically.
6. Send only new/changed/low-confidence content to the LLM.
7. Batch LLM requests.
8. Cache successful LLM results.
9. Use an appropriate-cost model.
10. Add website-specific parsers only for frequently failing websites.

---

# 37. Important distinction: batching vs cost reduction

Do NOT claim that:

```text
500 LLM calls
→ 5 LLM calls
```

automatically means the cost has dropped by 99%.

If the same amount of content is sent, token consumption may remain similar.

The actual optimization should be:

```text
500 scraped
      ↓
unchanged → SKIP
      ↓
irrelevant → FILTER
      ↓
deterministic → EXTRACT WITHOUT LLM
      ↓
only difficult items
      ↓
compact content
      ↓
batch
      ↓
LLM
```

That is the actual long-term cost optimization.

---

# 38. Final target architecture

The final architecture should be:

```text
                         500 Websites
                              │
                              ▼
                    Playwright / HTTP
                              │
                              ▼
                       Rendered HTML
                              │
                              ▼
                        BeautifulSoup
                              │
                              ▼
                  Generic Normalization
                              │
                              ▼
                    RFP Candidate Discovery
                              │
                              ▼
                 Normalize Relevant Content
                              │
                              ▼
                         SHA-256 Hash
                              │
                              ▼
                    Compare Previous Hash
                         /           \
                        /             \
                UNCHANGED          NEW/CHANGED
                    │                   │
                    ▼                   ▼
                   SKIP          Deterministic Extraction
                                        │
                                        ▼
                                    Validation
                                        │
                                        ▼
                                   Confidence
                                  /          \
                                HIGH          LOW
                                 │             │
                                 ▼             ▼
                                SAVE       LLM QUEUE
                                               │
                                               ▼
                                         Batch Processing
                                               │
                                               ▼
                                               LLM
                                               │
                               ┌───────────────┴───────────────┐
                               │                               │
                               ▼                               ▼
                         RFP Extraction                  Classification
                               │                               │
                               │                         Category
                               │                         Confidence
                               │                         Type
                               │                         Scope
                               │                               │
                               └───────────────┬───────────────┘
                                               ▼
                                          Validation
                                               │
                                               ▼
                                            Database
                                               │
                                               ▼
                                               UI
```

---

# 39. Final success criteria

The implementation is successful when:

### Cost

The majority of daily scraped content does not require an LLM call.

### Change detection

Unchanged RFP content is detected using normalized SHA-256 hashing and skipped.

### Extraction

Different website structures can be handled without manually creating a parser for every website.

### LLM

The LLM is used for semantic extraction/classification rather than HTML parsing.

### Category

The existing category information is preserved:

* category
* confidence
* type
* scope

### Reliability

One website or LLM batch failure does not stop the entire run.

### Measurement

The system can report actual:

* LLM calls
* input tokens
* output tokens
* cache hits
* deterministic extraction rate
* LLM fallback rate
* extraction failures
* validation failures

### Scalability

The architecture should work for 500 websites/day and be capable of growing significantly beyond that without requiring a fundamental redesign.

---

# 40. Final implementation report

After implementation, provide:

1. Current architecture discovered.
2. Files changed.
3. Components/classes/functions added.
4. How dynamic normalization works.
5. How title extraction works.
6. How content extraction works.
7. How link extraction works.
8. How RFP discovery works.
9. Exactly how normalized content is generated.
10. Exactly what is included/excluded from the SHA-256 hash.
11. How unchanged content is detected.
12. How new content is detected.
13. How changed content is detected.
14. Whether RFP-level hashing is supported.
15. How deterministic extraction works.
16. How confidence is calculated.
17. Exactly when the LLM is called.
18. How batching works.
19. How LLM caching works.
20. How category classification works.
21. How category confidence works.
22. How Product/Service type works.
23. How scope/subcategory works.
24. How validation works.
25. Database changes.
26. Metrics added.
27. Tests added.
28. Before/after LLM call count.
29. Before/after token usage if measurable.
30. Actual or estimated cost impact based on measurements.
31. Remaining bottlenecks.
32. Recommended future improvements.

Do not claim cost savings without measurements.

## Core principle

The final system must follow:

```text
SCRAPE
  ↓
NORMALIZE
  ↓
DISCOVER
  ↓
HASH
  ↓
SKIP UNCHANGED
  ↓
DETERMINISTIC EXTRACTION
  ↓
QUEUE ONLY NEW/CHANGED/UNCERTAIN ITEMS
  ↓
BATCH LLM
  ↓
RFP + CATEGORY EXTRACTION
  ↓
VALIDATE
  ↓
SAVE
```

Do not return to:

```text
500 websites
   ↓
500 LLM calls
```

The LLM should be an intelligent semantic fallback, not the default mechanism for processing every scraped website.
