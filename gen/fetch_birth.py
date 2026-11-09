# -*- coding: utf-8 -*-
"""为全部少将补充出生地/军衔 card 字段，写入 baike_birth.json"""
import json, time, io, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://baike.baidu.com/api/openapi/BaikeLemmaCardApi?scope=103&format=json&appid=379020&bk_length=600&bk_key="
HDRS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"}

names = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/shaojiang_names.txt', encoding='utf-8') if l.strip()]
names = sorted(set(names))
print('待抓取:', len(names), flush=True)

def api_call(key):
    req = urllib.request.Request(API + urllib.parse.quote(key), headers=HDRS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

def card_field(card, kw):
    for c in card or []:
        if kw in (c.get('name') or ''):
            return (c.get('value') or [''])[0]
    return ''

def clean(s):
    return re.sub(r'<[^>]+>', '', s or '')
import re

def fetch(name):
    for t in range(2):
        try:
            d = api_call(name)
            if (d.get('key') or '') != name:
                return name, None
            birth = clean(card_field(d.get('card'), '出生地'))
            rank = clean(card_field(d.get('card'), '军衔'))
            return name, {'birth': birth, 'rank': rank}
        except Exception:
            time.sleep(1.5 * (t + 1))
    return name, None

out = {}
with ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(fetch, n): n for n in names}
    for i, f in enumerate(as_completed(futs), 1):
        n, r = f.result()
        if r:
            out[n] = r
        if i % 200 == 0:
            print(f'{i}/{len(names)} 完成{len(out)}', flush=True)

io.open('/root/.codebuddy/artifact/data/baike_birth.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=0))
print('完成', len(out), flush=True)
