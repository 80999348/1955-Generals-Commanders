# -*- coding: utf-8 -*-
"""v2：优先用搜索摘要content拼生平，其次抓正文"""
import json, re, io, time, sys
sys.path.insert(0, '/root/.codebuddy/artifact/gen')
from fetch_cpc import search, page_text, extract_bio, GOOD_HOST, http, SEARCH, HDRS
from concurrent.futures import ThreadPoolExecutor, as_completed

def clean(s):
    return re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', s or ''))

BIO_KW = re.compile(r'生于|出生|年参加(中国工农)?红军|参加革命|加入中国共产党|历任|授予少将|晋升|军区|军长|政委|司令员|副司令|参谋长|逝世|将军|开国少将')

def snippet_bio(name):
    """从搜索摘要拼接生平"""
    seen, parts = set(), []
    for kw in (f"{name}", f"开国少将{name}", f"{name} 将军"):
        for r in search(name, kw):
            u = r.get('url') or ''
            if not GOOD_HOST.search(u):
                continue
            t = clean(r.get('title', ''))
            c = clean(r.get('content', ''))
            text = c if name in c else (t if name in t and BIO_KW.search(t) else '')
            if not text:
                continue
            for seg in re.split(r'[。；]', text):
                seg = seg.strip()
                if len(seg) >= 15 and (name in seg or '少将' in seg) and BIO_KW.search(seg) and seg not in seen:
                    seen.add(seg); parts.append(seg)
            if len(parts) >= 4:
                break
        time.sleep(0.2)
        if len(parts) >= 3:
            break
    if not parts:
        return None
    bio = '。'.join(parts[:5]) + '。'
    return bio if len(bio) >= 30 else None

def fetch_one(name):
    bio = snippet_bio(name)
    if bio and len(bio) >= 60:
        return name, {'desc': bio, 'src': '人民网搜索摘要'}
    # 抓正文兜底
    recs = search(name, f"{name} 少将") + search(name, f"{name} 将军")
    urls = [r['url'] for r in recs if name in re.sub('<[^>]+>', '', r.get('title', '')) and GOOD_HOST.search(r.get('url', ''))]
    for u in urls[:2]:
        txt = page_text(u)
        if name in txt and ('少将' in txt or '将军' in txt):
            bio = extract_bio(name, txt)
            if len(bio) >= 40:
                return name, {'desc': bio, 'src': '人民网', 'url': u}
        time.sleep(0.2)
    return name, None

if __name__ == '__main__':
    missing = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/baike_failed.txt', encoding='utf-8') if l.strip()]
    print('待补抓:', len(missing), flush=True)
    result = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch_one, n): n for n in missing}
        for i, f in enumerate(as_completed(futs), 1):
            n, r = f.result()
            if r:
                result[n] = r
            if i % 40 == 0:
                print(f'{i}/{len(missing)} 成功{len(result)}', flush=True)
    io.open('/root/.codebuddy/artifact/data/cpc.json', 'w', encoding='utf-8').write(
        json.dumps(result, ensure_ascii=False, indent=0))
    print('完成', len(result), flush=True)
    print('名单:', ' '.join(result.keys()), flush=True)
