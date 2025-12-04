# Nyx OSINT API Documentation

## Table of Contents

1. [Intelligence Modules](#intelligence-modules)
2. [Search & Filtering](#search--filtering)
3. [Analysis & Correlation](#analysis--correlation)
4. [Export & Reporting](#export--reporting)

---

## Intelligence Modules

### Smart Search

#### `SmartSearchService`

High-level orchestration service for free-form target information processing.

```python
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService

service = SmartSearchService()
input_obj = SmartSearchInput(raw_text="John Doe @johndoe john@example.com", region="US")
result = await service.smart_search(input_obj, persist_to_db=True)
```

**Methods:**

- `smart_search(input: SmartSearchInput, timeout: Optional[int] = 120, persist_to_db: bool = False) -> SmartSearchResult` - Execute Smart search
- `aclose() -> None` - Close underlying resources

**SmartSearchInput:**

```python
@dataclass
class SmartSearchInput:
    raw_text: str
    region: Optional[str] = None
    usernames: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    names: List[str] = field(default_factory=list)
```

**SmartSearchResult:**

```python
@dataclass
class SmartSearchResult:
    input: SmartSearchInput
    identifiers: Dict[str, List[str]]
    username_profiles: Dict[str, Profile]
    email_results: Dict[str, Any]
    phone_results: Dict[str, Any]
    person_results: Dict[str, Any]
    web_results: Dict[str, List[Dict[str, Any]]]
    candidates: List[SmartCandidateProfile]
```

**SmartCandidateProfile:**

```python
@dataclass
class SmartCandidateProfile:
    identifier: str
    identifier_type: str  # username, email, phone, name
    data: Dict[str, Any]
    confidence: float  # 0.0-1.0
    reason: str
```

### Deep Investigation

#### `DeepInvestigationService`

Centralized service for comprehensive investigations.

```python
from nyx.intelligence.deep import DeepInvestigationService

service = DeepInvestigationService()
result = await service.investigate("query", region="US", timeout=120)
```

**Methods:**

- `investigate(query: str, region: Optional[str] = None, timeout: Optional[int] = 120, include_smart: bool = True, include_web_search: bool = True) -> DeepInvestigationResult` - Perform deep investigation
- `aclose() -> None` - Close underlying resources

### Email Intelligence

#### `EmailIntelligence`

Email investigation and validation service.

```python
from nyx.intelligence.email import EmailIntelligence

email_intel = EmailIntelligence()
result = await email_intel.investigate("user@example.com")
```

**Methods:**

- `validate_email(email: str) -> bool` - Validate email format
- `is_disposable(email: str) -> bool` - Check if disposable email
- `get_provider(email: str) -> Optional[str]` - Get email provider
- `check_breach(email: str) -> Dict[str, Any]` - Check breach databases
- `check_email_services(email: str) -> List[str]` - Check registered services
- `calculate_reputation(...) -> float` - Calculate reputation score (0-100)
- `investigate(email: str) -> EmailResult` - Full email investigation

**EmailResult:**

```python
@dataclass
class EmailResult:
    email: str
    valid: bool
    exists: bool
    breached: bool
    breach_count: int
    breaches: List[str]
    providers: List[str]
    disposable: bool
    reputation_score: float
    metadata: Dict[str, Any]
    checked_at: datetime
```

---

### Phone Intelligence

#### `PhoneIntelligence`

Phone number investigation and validation service.

```python
from nyx.intelligence.phone import PhoneIntelligence

phone_intel = PhoneIntelligence()
result = await phone_intel.investigate("+14155552671", region="US")
```

**Methods:**

- `parse_number(phone: str, region: Optional[str]) -> Optional[PhoneNumber]`
- `validate_number(phone: str, region: Optional[str]) -> bool`
- `get_country_code(phone_number: PhoneNumber) -> str`
- `get_location(phone_number: PhoneNumber) -> Optional[str]`
- `get_carrier(phone_number: PhoneNumber) -> Optional[str]`
- `get_timezones(phone_number: PhoneNumber) -> List[str]`
- `get_line_type(phone_number: PhoneNumber) -> str`
- `format_number(phone_number: PhoneNumber, format_type: str) -> str`
- `investigate(phone: str, region: Optional[str]) -> PhoneResult`

**PhoneResult:**

```python
@dataclass
class PhoneResult:
    phone: str
    valid: bool
    country_code: str
    country_name: str
    location: Optional[str]
    carrier: Optional[str]
    line_type: str
    timezones: List[str]
    formatted_international: str
    formatted_national: str
    formatted_e164: str
    reputation_score: float
    metadata: Dict[str, Any]
    checked_at: datetime
```

---

## Search & Filtering

### Advanced Filtering

#### `AdvancedFilter`

Apply complex filters to search results.

```python
from nyx.filters.advanced import AdvancedFilter, FilterRule, FilterOperator

filter = AdvancedFilter()
rule = FilterRule("age", FilterOperator.GREATER_THAN, 25)
results = filter.filter_items(items, [rule])
```

**Filter Operators:**

- `EQUALS` - Exact match
- `NOT_EQUALS` - Not equal
- `CONTAINS` - Contains substring
- `NOT_CONTAINS` - Doesn't contain
- `REGEX` - Regex pattern match
- `GREATER_THAN` - Greater than (numeric)
- `LESS_THAN` - Less than (numeric)
- `IN_LIST` - Value in list
- `NOT_IN_LIST` - Value not in list

#### `QueryParser`

Parse query strings into filter rules.

```python
from nyx.filters.advanced import QueryParser

parser = QueryParser()
rules = parser.parse("name:John age>25 status!=inactive")
```

**Query Syntax:**

- `field:value` - Equals
- `field!=value` - Not equals
- `field~value` - Contains
- `field!~value` - Not contains
- `field>value` - Greater than
- `field<value` - Less than
- `field=/regex/` - Regex match

---

### Saved Searches

#### `SavedSearchManager`

Manage and reuse saved searches.

```python
from nyx.filters.saved_searches import SavedSearchManager

manager = SavedSearchManager()
search = manager.create(
    name="Active Users",
    query="status:active",
    filters=[...],
    tags=["users", "active"]
)
```

**Methods:**

- `create(...) -> SavedSearch` - Create saved search
- `update(search_id, ...) -> Optional[SavedSearch]` - Update search
- `delete(search_id) -> bool` - Delete search
- `get(search_id) -> Optional[SavedSearch]` - Get by ID
- `list_all() -> List[SavedSearch]` - List all
- `search_by_tag(tag) -> List[SavedSearch]` - Search by tag
- `search_by_name(name) -> List[SavedSearch]` - Search by name

---

### Batch Processing

#### `BatchProcessor`

Process multiple searches concurrently.

```python
from nyx.filters.batch import BatchProcessor

processor = BatchProcessor(max_concurrent=10)
results = await processor.process_usernames(
    usernames=["user1", "user2", "user3"],
    exclude_nsfw=True
)
```

**Methods:**

- `process_usernames(usernames, exclude_nsfw, progress_callback) -> Dict`
- `process_emails(emails, progress_callback) -> Dict`
- `process_phones(phones, region, progress_callback) -> Dict`
- `get_job(job_id) -> Optional[BatchJob]`
- `list_jobs() -> List[BatchJob]`

---

## Analysis & Correlation

### Correlation Analyzer

#### `CorrelationAnalyzer`

Analyze relationships between data points.

```python
from nyx.analysis.correlation import CorrelationAnalyzer

analyzer = CorrelationAnalyzer()
correlations = analyzer.correlate_profiles(profiles)
patterns = analyzer.detect_patterns(data)
```

**Methods:**

- `calculate_similarity(data1, data2) -> float` - Similarity score (0-1)
- `find_shared_attributes(profiles) -> Dict[str, List[str]]`
- `correlate_profiles(profiles) -> List[CorrelationScore]`
- `detect_patterns(data) -> List[Pattern]`
- `calculate_confidence_score(data_points, weights) -> float`

---

### Relationship Graphs

#### `RelationshipGraph`

Build and analyze relationship graphs.

```python
from nyx.analysis.graphs import RelationshipGraph

graph = RelationshipGraph()
graph.build_from_profiles(profiles)
clusters = graph.find_clusters()
json_export = graph.export_json()
```

**Methods:**

- `add_node(node_id, label, node_type, attributes)`
- `add_edge(source, target, edge_type, weight, attributes)`
- `build_from_profiles(profiles)`
- `get_neighbors(node_id) -> List[Node]`
- `get_connected_component(node_id) -> Set[str]`
- `calculate_centrality() -> Dict[str, float]`
- `find_clusters() -> List[Set[str]]`
- `export_json() -> str`
- `export_graphviz() -> str`
- `get_statistics() -> Dict[str, Any]`

---

### Timeline Analysis

#### `TimelineAnalyzer`

Analyze temporal patterns.

```python
from nyx.analysis.timeline import TimelineAnalyzer

timeline = TimelineAnalyzer()
timeline.build_from_profiles(profiles)
patterns = timeline.find_temporal_patterns()
```

**Methods:**

- `add_event(event_id, timestamp, event_type, source, title, ...)`
- `build_from_profiles(profiles)`
- `get_events_in_range(start, end) -> List[TimelineEvent]`
- `get_events_by_type(event_type) -> List[TimelineEvent]`
- `get_events_by_source(source) -> List[TimelineEvent]`
- `find_temporal_patterns() -> List[Dict[str, Any]]`
- `export_json() -> str`
- `get_statistics() -> Dict[str, Any]`

---

## Export & Reporting

### HTML Export

#### `HTMLExporter`

Export data to HTML reports.

```python
from nyx.export.html import HTMLExporter

exporter = HTMLExporter()
exporter.export(
    data={"profiles": [...]},
    output_path="report.html",
    title="Investigation Report",
    redact_fields=["ssn", "email"]
)
```

**Methods:**

- `export(data, output_path, title, description, template_name, redact_fields)`

---

### PDF Export

#### `PDFExporter`

Export data to PDF reports.

```python
from nyx.export.pdf import PDFExporter

exporter = PDFExporter(page_size="letter")
exporter.export(
    data={"profiles": [...]},
    output_path="report.pdf",
    title="Investigation Report",
    redact_fields=["ssn"]
)
```

**Methods:**

- `export(data, output_path, title, description, redact_fields)`

---

### JSON Export

#### `JSONExporter`

Export data to JSON format.

```python
from nyx.export.json_export import JSONExporter

exporter = JSONExporter(pretty=True)
exporter.export(data, "output.json", include_metadata=True)
exporter.export_compressed(data, "output.json.gz")
```

**Methods:**

- `export(data, output_path, include_metadata, redact_fields)`
- `export_compressed(data, output_path, include_metadata, redact_fields)`

---

### CSV Export

#### `CSVExporter`

Export data to CSV format.

```python
from nyx.export.csv_export import CSVExporter

exporter = CSVExporter()
exporter.export(data, "output.csv", fieldnames=["name", "email"])
exporter.export_profiles(profiles, "profiles.csv")
```

**Methods:**

- `export(data, output_path, fieldnames, redact_fields)`
- `export_profiles(profiles, output_path, redact_fields)`

---

## Examples

### Complete Investigation Workflow

```python
import asyncio
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.osint.search import SearchService
from nyx.analysis.correlation import CorrelationAnalyzer
from nyx.analysis.graphs import RelationshipGraph
from nyx.export.html import HTMLExporter

async def investigate_target(username, email, phone):
    # Search username
    search_service = SearchService()
    profiles = await search_service.search_username(username)

    # Email intelligence
    email_intel = EmailIntelligence()
    email_result = await email_intel.investigate(email)

    # Phone intelligence
    phone_intel = PhoneIntelligence()
    phone_result = await phone_intel.investigate(phone)

    # Correlate profiles
    analyzer = CorrelationAnalyzer()
    correlations = analyzer.correlate_profiles(list(profiles.values()))

    # Build relationship graph
    graph = RelationshipGraph()
    graph.build_from_profiles(list(profiles.values()))

    # Export report
    exporter = HTMLExporter()
    exporter.export(
        data={
            "profiles": list(profiles.values()),
            "email": email_result,
            "phone": phone_result,
            "correlations": correlations
        },
        output_path="investigation_report.html",
        title=f"Investigation: {username}"
    )

asyncio.run(investigate_target("john_doe", "john@example.com", "+14155552671"))
```

---

## Error Handling

All async methods may raise exceptions. Wrap in try-except:

```python
try:
    result = await email_intel.investigate(email)
except Exception as e:
    logger.error(f"Investigation failed: {e}")
```

---

## Rate Limiting

HTTP requests are rate-limited. Configure in `config/settings.yaml`:

```yaml
http:
  max_concurrent_requests: 100
  timeout: 10
  retries: 3
```

---

## Caching

Results are cached automatically. Configure cache settings:

```yaml
cache:
  enabled: true
  ttl: 3600
  max_size: 1000
  backend: memory
```

---

**Version:** 0.1.0
**Last Updated:** 2025-11-23
