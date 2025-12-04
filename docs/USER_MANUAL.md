# Nyx OSINT User Manual

## Table of Contents

1. [Getting Started](#getting-started)
2. [GUI Usage](#gui-usage)
3. [CLI Usage](#cli-usage)
4. [Investigation Workflows](#investigation-workflows)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- Python 3.12 or higher
- 4GB RAM minimum (8GB recommended)
- 1GB disk space
- Internet connection
- Tesseract-OCR (optional, for OCR features)

### Installation

1. **Clone or download Nyx:**

```bash
cd /path/to/installation
```

2. **Install dependencies with Poetry:**

```bash
poetry install
```

3. **Copy configuration templates:**

```bash
cp config/settings.yaml config/settings.local.yaml
cp .env.example .env.local
```

4. **Edit configuration:**

```bash
nano config/settings.local.yaml
```

### First Launch

**GUI Mode:**

```bash
poetry run nyx
```

**CLI Mode:**

```bash
poetry run nyx-cli --help
```

---

## GUI Usage

### Main Interface

The GUI is divided into several sections:

1. **Sidebar** - Navigation menu
2. **Content Area** - Main workspace
3. **Status Bar** - Activity indicators

### Starting a Search

1. Click "Search" in sidebar
2. Enter username, email, or phone number
3. Configure options:
   - Exclude NSFW platforms
   - Set timeout
   - Choose categories
4. Click "Start Search"

### Viewing Results

Results are displayed with:
- Platform name
- Profile URL
- Response time
- Additional metadata

Click on a result for detailed view.

### Exporting Reports

1. Complete a search
2. Click "Export" button
3. Choose format:
   - HTML (Interactive report)
   - PDF (Printable document)
   - JSON (Structured data)
   - CSV (Spreadsheet)
4. Select output location
5. Configure redaction (optional)

---

## CLI Usage

### Basic Commands

**Search for username:**

```bash
poetry run nyx-cli search john_doe
```

**Exclude NSFW platforms:**

```bash
poetry run nyx-cli search john_doe --exclude-nsfw
```

**Set custom timeout:**

```bash
poetry run nyx-cli search john_doe --timeout 30
```

### Email Investigation

```bash
poetry run nyx-cli email user@example.com
```

Output includes:
- Email validation
- Breach status
- Registered services
- Reputation score

### Phone Investigation

```bash
poetry run nyx-cli phone "+14155552671"
```

With region hint:

```bash
poetry run nyx-cli phone "4155552671" --region US
```

Output includes:
- Phone validation
- Country/location
- Carrier information
- Line type
- Formatted numbers

### Smart Search

**Smart search from free-form text:**

```bash
poetry run nyx-cli smart "John Doe from NY uses handle @johnny_d on social and email john@example.com"
```

**With region hint:**

```bash
poetry run nyx-cli smart "Jane Smith 415-555-2671" --region US
```

**JSON output for automation:**

```bash
poetry run nyx-cli smart "target info" -o json
```

**Persist results to database:**

```bash
poetry run nyx-cli smart "target info" --persist
```

Smart search features:
- Automatically extracts usernames, emails, phone numbers, and names
- Runs all applicable intelligence modules in parallel
- Performs web searches for additional context
- Produces scored candidate profiles with confidence ratings
- Optionally persists results to database for investigation tracking

### Platform Management

**List all platforms:**

```bash
poetry run nyx-cli platforms
```

**Filter by category:**

```bash
poetry run nyx-cli platforms --category social_media
poetry run nyx-cli platforms --category professional
```

**Platform statistics:**

```bash
poetry run nyx-cli stats
```

---

## Investigation Workflows

### Basic Username Investigation

1. **Initial Search:**

```bash
poetry run nyx-cli search target_username --exclude-nsfw
```

2. **Review Results:**
   - Note active profiles
   - Collect profile URLs
   - Identify common patterns

3. **Export Findings:**
   - Generate HTML report
   - Save JSON for further analysis

### Comprehensive Target Investigation

1. **Collect Identifiers:**
   - Username(s)
   - Email address(es)
   - Phone number(s)

2. **Run Searches:**

```bash
# Username search
poetry run nyx-cli search username123

# Email investigation
poetry run nyx-cli email target@example.com

# Phone investigation
poetry run nyx-cli phone "+1234567890"
```

3. **Analyze Correlations:**
   - Use GUI or Python API
   - Build relationship graphs
   - Identify shared attributes

4. **Generate Report:**
   - Export comprehensive report
   - Include all findings
   - Redact sensitive data

### Batch Investigation

For multiple targets:

```python
from nyx.filters.batch import BatchProcessor

processor = BatchProcessor()
results = await processor.process_usernames([
    "user1", "user2", "user3"
])
```

---

## Advanced Features

### Saved Searches

**Create saved search:**

```python
from nyx.filters.saved_searches import SavedSearchManager

manager = SavedSearchManager()
search = manager.create(
    name="Social Media Only",
    query="category:social_media",
    filters=[...],
    tags=["social", "quick"]
)
```

**Reuse saved search:**

```python
search = manager.get(search_id)
# Apply search.filters to new query
```

### Advanced Filtering

**Query syntax examples:**

```
# Username contains "john"
username~john

# Age greater than 25
age>25

# Status not inactive
status!=inactive

# Email matches pattern
email=/.*@gmail\.com/

# Multiple conditions
username~john age>25 status:active
```

### Relationship Graphs

**Generate graph:**

```python
from nyx.analysis.graphs import RelationshipGraph

graph = RelationshipGraph()
graph.build_from_profiles(profiles)

# Export as JSON
json_data = graph.export_json()

# Export as Graphviz
dot_data = graph.export_graphviz()

# Find clusters
clusters = graph.find_clusters()
```

### Timeline Analysis

**Analyze temporal patterns:**

```python
from nyx.analysis.timeline import TimelineAnalyzer

timeline = TimelineAnalyzer()
timeline.build_from_profiles(profiles)

# Find patterns
patterns = timeline.find_temporal_patterns()

# Get statistics
stats = timeline.get_statistics()
```

---

## Best Practices

### Legal & Ethical

1. **Always obtain proper authorization** before investigations
2. **Comply with local laws** and regulations
3. **Respect platform terms of service**
4. **Use responsibly** for legitimate purposes only
5. **Maintain confidentiality** of investigation data

### Operational

1. **Use rate limiting** to avoid detection/blocking
2. **Enable caching** to reduce redundant requests
3. **Verify findings** from multiple sources
4. **Document methodology** in reports
5. **Redact sensitive data** in shared reports

### Performance

1. **Exclude NSFW platforms** if not relevant
2. **Use batch processing** for multiple targets
3. **Set appropriate timeouts** based on network
4. **Enable L2 cache** for better performance
5. **Adjust concurrent limits** based on system resources

### Security

1. **Use Tor/proxies** for anonymity
2. **Enable encryption** for stored data
3. **Set master password** for sensitive investigations
4. **Regularly update** Nyx and dependencies
5. **Review logs** for anomalies

---

## Configuration

### Database

**SQLite (Default):**

```yaml
database:
  url: sqlite:///./nyx.db
```

**PostgreSQL (Production):**

```yaml
database:
  url: postgresql://user:pass@localhost/nyx
  pool_size: 20
  max_overflow: 40
```

### Caching

```yaml
cache:
  enabled: true
  ttl: 3600  # 1 hour
  max_size: 1000
  backend: memory  # or 'disk'
```

### HTTP Client

```yaml
http:
  timeout: 10
  retries: 3
  max_concurrent_requests: 100
  user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0
```

### Tor Integration

```yaml
tor:
  enabled: true
  socks_host: 127.0.0.1
  socks_port: 9050
  control_host: 127.0.0.1
  control_port: 9051
```

### Proxy Support

```yaml
proxy:
  enabled: true
  http_proxy: http://proxy:8080
  https_proxy: https://proxy:8080
  socks_proxy: socks5://proxy:1080
```

---

## Troubleshooting

### Common Issues

**1. "No platforms found"**

- Check database initialization
- Verify platform database loaded
- Run: `poetry run nyx-cli platforms`

**2. "Connection timeout"**

- Increase timeout in config
- Check internet connection
- Verify proxy/Tor settings

**3. "Rate limit exceeded"**

- Reduce concurrent requests
- Increase delays between requests
- Enable caching

**4. "Database locked"**

- Close other Nyx instances
- Check file permissions
- Consider PostgreSQL for multi-user

**5. "Import error"**

- Reinstall dependencies: `poetry install`
- Check Python version (3.12+)
- Verify virtual environment activated

### Debug Mode

Enable debug logging:

```bash
poetry run nyx --debug
poetry run nyx-cli --debug search username
```

Check logs:

```bash
tail -f logs/nyx.log
```

### Performance Issues

1. **Reduce concurrent requests:**

```yaml
http:
  max_concurrent_requests: 50  # Lower from 100
```

2. **Enable disk cache:**

```yaml
cache:
  backend: disk
  ttl: 86400  # 24 hours
```

3. **Exclude platforms:**

```bash
poetry run nyx-cli search username --exclude-nsfw
```

### Reset Database

**Backup first:**

```bash
cp nyx.db nyx.db.backup
```

**Reset:**

```bash
rm nyx.db
poetry run nyx  # Will recreate
```

---

## Support

### Documentation

- API Documentation: `docs/API.md`
- Project Status: `PROJECT_STATUS.md`
- README: `README.md`

### Community

- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share tips

### Responsible Disclosure

For security issues:
1. Do NOT create public issue
2. Email security concerns privately
3. Provide detailed description
4. Allow time for fix before disclosure

---

## Appendix

### Platform Categories

- `social_media` - Twitter, Instagram, Facebook, etc.
- `professional` - LinkedIn, GitHub, Stack Overflow
- `dating` - Tinder, Bumble, OkCupid
- `gaming` - Steam, Discord, Twitch
- `forums` - Reddit, Hacker News
- `blogging` - Medium, WordPress
- `photography` - Flickr, Pixelfed
- `messaging` - Telegram, Discord
- `streaming` - YouTube, Twitch
- `crypto` - Blockchain explorers
- `shopping` - eBay, Etsy
- `adult` - 140+ adult platforms
- `other` - Miscellaneous

### Keyboard Shortcuts (GUI)

- `Ctrl+N` - New search
- `Ctrl+S` - Save results
- `Ctrl+E` - Export report
- `Ctrl+F` - Filter results
- `Ctrl+Q` - Quit

### File Locations

- Configuration: `config/settings.local.yaml`
- Database: `./nyx.db`
- Logs: `logs/nyx.log`
- Cache: `.cache/nyx/`
- Exports: `./exports/`

---

**Version:** 0.1.0
**Last Updated:** 2025-11-23
**Support:** See GitHub repository
