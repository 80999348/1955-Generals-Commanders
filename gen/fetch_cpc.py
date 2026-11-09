# -*- coding: utf-8 -*-
"""从人民网（cpc.people.com.cn 等党网系）新闻中提取少将生平段落"""
import json, re, io, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

SEARCH = "http://search.people.cn/search-platform/front/search"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://search.people.cn/", "Content-Type": "application/json"}
GOOD_HOST = re.compile(r'(cpc\.people\.com\.cn|dangshi\.people\.(com\.cn|cn)|military\.people\.com\.cn|theory\.people\.com\.cn|81\.cn)')
BIO_KW = re.compile(r'生于|出生|年参加(中国工农)?红军|参加革命|加入中国共产主义青年团|加入中国共产党|历任|被授予(少将|将军)|晋升为少将|授予少将军衔|军区|军长|政委|司令员|逝世')
SENT_SPLIT = re.compile(r'[。；;]')

def http(url, data=None, timeout=15):
    req = urllib.request.Request(url, headers=HDRS, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    for enc in ('utf-8', 'gb18030'):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode('utf-8', errors='ignore')

def search(name, kw):
    body = json.dumps({"key": kw, "page": 1, "limit": 10, "hasTitle": True,
                       "hasContent": True, "isFuzzy": True, "type": 0,
                       "sortType": 2, "startTime": 0, "endTime": 0}).encode()
    try:
        d = json.loads(http(SEARCH, body))
        return d.get('data', {}).get('records', []) or []
    except Exception:
        return []

def page_text(url):
    try:
        raw = http(url)
    except Exception:
        return ''
    raw = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
    txt = re.sub(r'<[^>]+>', '', raw)
    txt = re.sub(r'[\s\u3000]+', '', txt)
    return txt

def extract_bio(name, txt):
    sents = [s for s in SENT_SPLIT.split(txt) if name in s and BIO_KW.search(s)]
    if not sents:
        sents = [s for s in SENT_SPLIT.split(txt) if BIO_KW.search(s) and len(s) > 20 and ('少将' in s or '将军' in s)]
    out, seen = [], set()
    for s in sents:
        s = s.strip()[:150]
        if s and s not in seen:
            seen.add(s); out.append(s)
        if len('。'.join(out)) > 420: break
    return '。'.join(out) + ('。' if out else '')

def fetch_one(name):
    cands = {}
    for kw in (f"{name} 少将", f"{name} 将军", f"开国少将{name}"):
        for r in search(name, kw):
            t = re.sub('<[^>]+>', '', r.get('title', ''))
            u = r.get('url') or ''
            if name in t and GOOD_HOST.search(u):
                cands[u] = t
        if len(cands) >= 3:
            break
        time.sleep(0.2)
    for u in list(cands)[:3]:
        txt = page_text(u)
        if name in txt and ('少将' in txt or '将军' in txt):
            bio = extract_bio(name, txt)
            if len(bio) >= 40:
                return name, {'desc': bio, 'url': u}
        time.sleep(0.2)
    return name, None

if __name__ == '__main__':
    missing = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/baike_failed.txt', encoding='utf-8') if l.strip()]
    # 排除已有手写简介的
    HAND = set()
    try:
        sys_ = json.load(io.open('/root/.codebuddy/artifact/data/hand_bios.json', encoding='utf-8'))
        HAND = set(sys_)
    except Exception:
        pass
    todo = [n for n in missing if n not in HAND]
    print('待补抓:', len(todo), flush=True)
    result = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_one, n): n for n in todo}
        for i, f in enumerate(as_completed(futs), 1):
            n, r = f.result()
            if r:
                result[n] = r
            if i % 30 == 0:
                print(f'{i}/{len(todo)} 成功{len(result)}', flush=True)
    io.open('/root/.codebuddy/artifact/data/cpc.json', 'w', encoding='utf-8').write(
        json.dumps(result, ensure_ascii=False, indent=0))
    print('完成', len(result), flush=True)
