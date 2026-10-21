---
name: playwright-browser-agent
description: >-
  Headless browser automation, dynamic web scraping, UI verification, and DOM extraction
  using Playwright. Use this skill when scraping dynamic single-page applications (SPAs),
  taking verification screenshots for multimodal evaluation, interacting with forms,
  or verifying web frontends autonomously.
---

# Playwright Browser Automation & Web Agent

This skill provides reliable, headless browser execution patterns for crawling JavaScript-rendered web pages, capturing evidence screenshots, and extracting structured DOM content.

---

## 1. Minimal Async Playwright Scraper

```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_page(url: str, screenshot_path: str = None) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Navigate and wait for network to settle
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Capture screenshot if requested (for vision models)
        if screenshot_path:
            await page.screenshot(path=screenshot_path, full_page=True)
            
        # Extract clean visible text
        text_content = await page.evaluate("() => document.body.innerText")
        
        await browser.close()
        return text_content

if __name__ == "__main__":
    content = asyncio.run(scrape_page("https://example.com", "screenshot.png"))
    print(content[:500])
```

---

## 2. Interactive Actions (Form Submission & Click)

```python
# Click a button
await page.click("button#submit-btn")

# Fill form field
await page.fill("input[name='search']", "query text")

# Wait for selector or dynamic element
await page.wait_for_selector(".results-container", timeout=10000)
```

---

## 3. Best Practices for Agent Scraping

1. **Avoid Bot Blocks**: Always pass a realistic desktop `user_agent`.
2. **Network Idle Wait**: Use `wait_until="networkidle"` for React/Vue/Angular apps that fetch initial data via client-side fetch/XHR.
3. **Graceful Timeouts**: Always wrap navigations in `try...except TimeoutError` with a 30s ceiling.
