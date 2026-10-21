import sys
import os
import json
import argparse
import urllib.request
import urllib.parse
from html.parser import HTMLParser

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

class DDGLiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.in_link = False
        self.in_snippet = False
        self.current = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '')
        if tag == 'a' and 'result-link' in cls:
            self.in_link = True
            raw_url = attrs_dict.get('href', '').strip()
            # Unquote DDG redirect if present (/l/?kh=-1&uddg=https%3A%2F%2F...)
            if '/l/?' in raw_url and 'uddg=' in raw_url:
                try:
                    parsed = urllib.parse.urlparse(raw_url)
                    params = urllib.parse.parse_qs(parsed.query)
                    clean_url = urllib.parse.unquote(params.get('uddg', [raw_url])[0])
                except Exception:
                    clean_url = raw_url
            else:
                clean_url = raw_url
            self.current = {'title': '', 'url': clean_url, 'snippet': ''}
        elif tag == 'td' and 'result-snippet' in cls:
            self.in_snippet = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.in_link:
            self.in_link = False
        elif tag == 'td' and self.in_snippet:
            self.in_snippet = False
            if self.current.get('title') and self.current.get('url'):
                self.results.append({
                    'title': self.current['title'].strip(),
                    'url': self.current['url'].strip(),
                    'snippet': self.current.get('snippet', '').strip()
                })
                self.current = {}

    def handle_data(self, data):
        if self.in_link:
            self.current['title'] = self.current.get('title', '') + data
        elif self.in_snippet:
            self.current['snippet'] = self.current.get('snippet', '') + data

def search_tavily(query: str, api_key: str, max_results: int = 5):
    url = 'https://api.tavily.com/search'
    payload = json.dumps({
        'api_key': api_key,
        'query': query,
        'search_depth': 'advanced',
        'max_results': max_results,
        'include_answer': True
    }).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json', 'User-Agent': 'TensuraRaphael/1.0'}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def search_duckduckgo_lite(query: str, max_results: int = 5):
    url = 'https://lite.duckduckgo.com/lite/'
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    results = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            parser = DDGLiteParser()
            parser.feed(html)
            results = parser.results[:max_results]
    except Exception as e:
        results = [{'error': str(e), 'query': query}]
    return {'query': query, 'provider': 'duckduckgo_lite', 'results': results}

def main():
    parser = argparse.ArgumentParser(description='Web Search Utility for Tensura Raphael Desktop & Agents')
    parser.add_argument('query', type=str, help='Search query string')
    parser.add_argument('--max-results', type=int, default=5, help='Maximum results to return')
    args = parser.parse_args()

    tavily_key = os.environ.get('TAVILY_API_KEY')
    if tavily_key:
        try:
            res = search_tavily(args.query, tavily_key, args.max_results)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return
        except Exception as e:
            sys.stderr.write(f'Tavily search failed: {e}\nFalling back to DuckDuckGo Lite...\n')

    res = search_duckduckgo_lite(args.query, args.max_results)
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
