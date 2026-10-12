# -*- coding: utf-8 -*-
"""
Internet Doctor - online help: find fixes on the web when local repairs fail.
دکتر اینترنت - کمک آنلاین: جستجوی راه‌حل در وب وقتی تعمیرهای داخلی کافی نبودند
"""
import base64
import html as html_mod
import re
import urllib.parse
import urllib.request

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/120.0 Safari/537.36")}


def _fetch(url, data=None, timeout=8):
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def _clean_ddg(href):
    if "uddg=" in href:
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            return urllib.parse.unquote(m.group(1))
    if href.startswith("http"):
        return href
    return None


def _ddg(query, max_results, timeout):
    data = urllib.parse.urlencode({"q": query}).encode()
    page = _fetch("https://html.duckduckgo.com/html/", data=data, timeout=timeout)
    out = []
    blocks = re.finditer(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        page, re.S)
    snippets = [re.sub(r"<[^>]+>", "", s.group(1)).strip()
                for s in re.finditer(r'class="result__snippet"[^>]*>(.*?)</a>',
                                     page, re.S)]
    for idx, m in enumerate(blocks):
        url = _clean_ddg(m.group(1))
        title = html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(2)).strip())
        if url and title:
            snippet = snippets[idx] if idx < len(snippets) else ""
            out.append({"title": title, "url": url,
                        "snippet": html_mod.unescape(snippet)[:280],
                        "source": "duckduckgo"})
        if len(out) >= max_results:
            break
    return out


def _decode_bing(url):
    """Bing wraps result URLs in a redirect; decode the base64 'u' parameter."""
    if "bing.com/ck/a" in url:
        m = re.search(r"[?&]u=a1([^&]+)", url)
        if m:
            raw = m.group(1)
            try:
                pad = "=" * (-len(raw) % 4)
                decoded = base64.urlsafe_b64decode(raw + pad).decode("utf-8", "ignore")
                if decoded.startswith("http"):
                    return decoded
            except Exception:
                pass
            return None
    return url


def _bing(query, max_results, timeout):
    page = _fetch("https://www.bing.com/search?q=" + urllib.parse.quote(query),
                  timeout=timeout)
    out = []
    for m in re.finditer(
            r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>(.*?)(?=<h2|<li class="b_algo"|</ol|$)',
            page, re.S):
        url = _decode_bing(html_mod.unescape(m.group(1)))
        title = html_mod.unescape(re.sub(r"<[^>]+>", "", m.group(2)).strip())
        sm = re.search(r"<p[^>]*>(.*?)</p>", m.group(3), re.S)
        snippet = ""
        if sm:
            snippet = html_mod.unescape(re.sub(r"<[^>]+>", "", sm.group(1))).strip()
        if url and url.startswith("http") and title:
            out.append({"title": title, "url": url, "snippet": snippet[:280],
                        "source": "bing"})
        if len(out) >= max_results:
            break
    return out


def search_web(query, max_results=5, timeout=8):
    """Search DuckDuckGo then Bing. Returns [] when both fail (offline)."""
    results = []
    try:
        results = _ddg(query, max_results, timeout)
    except Exception:
        results = []
    if not results:
        try:
            results = _bing(query, max_results, timeout)
        except Exception:
            results = []
    return results[:max_results]


def fallback_links(query):
    """Always-available links that open the query in an external browser."""
    q = urllib.parse.quote(query)
    return [
        {"title": "Google Search - %s" % query,
         "url": "https://www.google.com/search?q=%s" % q,
         "snippet": "Open the search results in your browser",
         "source": "link"},
        {"title": "Microsoft Q&A - community answers",
         "url": "https://answers.microsoft.com/en-us/search/search?SearchTerm=%s" % q,
         "snippet": "Search Microsoft's official support community",
         "source": "link"},
        {"title": "DuckDuckGo Search - %s" % query,
         "url": "https://duckduckgo.com/?q=%s" % q,
         "snippet": "Open DuckDuckGo results in your browser",
         "source": "link"},
    ]
