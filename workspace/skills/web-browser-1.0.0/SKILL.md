---
name: Web Browser (Playwright Python)
description: Automates web browser interactions using Playwright Python API: login, click, scrape specific elements, fill forms, take screenshots, and extract structured data from web pages. Use when needing to automate a website, scrape data, interact with a web UI, or perform browser automation tasks via Python code.
read_when:
  - Automating web interactions with Python
  - Scraping structured data from pages via Python
  - Filling forms programmatically with Python
  - Taking screenshots of web pages
metadata: {"clawdbot":{"emoji":"🐍"}}
---

# Web Browser Skill (Playwright Python)

Automates browser interactions via Playwright Python API. Complements `agent-browser` (CLI) — use this when you need Python code integration or complex data processing pipelines.

## Setup

```bash
pip install playwright
# If chromium download fails due to network restrictions, use system Chrome (see below)
playwright install chromium
```

> **macOS**: If `playwright install chromium` fails (network/DNS issue), use system Chrome directly:
> `executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`

## Launch browser

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        # Uncomment if Chromium not installed:
        # executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )
    page = browser.new_page()
    page.goto("https://example.com")
    # ... actions ...
    browser.close()
```

## Login

```python
page.fill("#username", "your_user")
page.fill("#password", "your_pass")
page.click("button[type='submit']")
page.wait_for_load_state("networkidle")
```

## Scrape elements

```python
# Single element
text = page.inner_text(".target-class")

# Multiple elements
items = page.query_selector_all(".list-item")
data = [el.inner_text() for el in items]

# Table to list
rows = page.query_selector_all("table tbody tr")
table = [[c.inner_text() for c in row.query_selector_all("td")] for row in rows]
```

## Wait for dynamic content

```python
page.wait_for_selector(".dynamic-element", timeout=10000)
page.wait_for_load_state("networkidle")
```

## Screenshot

```python
page.screenshot(path="output.png", full_page=True)
```

## Selector priority
1. `data-testid` / `data-id` (most stable)
2. `#id`
3. `.class` (specific ones)
4. XPath last resort: `//button[text()='Submit']`

## Output convention

Return summary dict, not raw HTML:
```python
import json
result = {"status": "success", "records_found": len(data), "sample": data[:3]}
print(json.dumps(result, ensure_ascii=False, indent=2))
```
