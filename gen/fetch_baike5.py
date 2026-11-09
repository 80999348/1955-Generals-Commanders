# -*- coding: utf-8 -*-
"""第五轮补抓：用 card 字段（军衔/出生地）做校验与籍贯提取"""
import json, re, time, io, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://baike.baidu.com/api/openapi/BaikeLemmaCardApi?scope=103&format=json&appid=379020&bk_length=600&bk_key="
HDRS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"}
VALID = re.compile(r'少将|中将|上将|将军|解放军|红军|八路军|新四军|军区|军长|政委|军委|司令|参谋|军队|军人|革命|干部|共产党')

def card_field(card, name_kw):
    for c in card or []:
        if name_kw in (c.get('name') or ''):
            return (c.get('value') or [''])[0]
    return ''

def good(d, name):
    if not d: return False
    title = d.get('key') or d.get('title') or ''
    if title != name: return False
    card = d.get('card') or []
    rank = card_field(card, '军衔')
    career = card_field(card, '职业')
    if rank and ('少将' in rank or '中将' in rank or '上将' in rank):
        return True
    desc = d.get('desc') or ''
    if VALID.search(desc) and ('军人' in career or not career):
        return True
    return False

result = json.load(io.open('/root/.codebuddy/artifact/data/baike.json', encoding='utf-8'))
extra = {}   # 出生地信息补充
names = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/shaojiang_names.txt', encoding='utf-8') if l.strip()]
todo = sorted(set(names) - set(result.keys()))
print('待抓取:', len(todo), flush=True)

def api_call(key):
    req = urllib.request.Request(API + urllib.parse.quote(key), headers=HDRS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

def fetch(name):
    for key in (name, name + "（中国人民解放军少将）", name + "（开国少将）"):
        for t in range(2):
            try:
                d = api_call(key)
                if good(d, name):
                    birth = card_field(d.get('card'), '出生地')
                    return name, {'title': d.get('key') or '', 'desc': d.get('desc') or '',
                                  'birth': birth,
                                  'url': 'https://baike.baidu.com/item/' + urllib.parse.quote(key)}
                break
            except Exception:
                time.sleep(1.5 * (t + 1))
        time.sleep(0.3)
    return name, None

with ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(fetch, n): n for n in todo}
    for i, f in enumerate(as_completed(futs), 1):
        n, r = f.result()
        if r:
            result[n] = r
        if i % 60 == 0:
            print(f'{i}/{len(todo)} 累计{len(result)}', flush=True)

io.open('/root/.codebuddy/artifact/data/baike.json', 'w', encoding='utf-8').write(
    json.dumps(result, ensure_ascii=False, indent=0))
failed = sorted(set(names) - set(result.keys()))
io.open('/root/.codebuddy/artifact/data/baike_failed.txt', 'w', encoding='utf-8').write('\n'.join(failed))
print('总成功', len(result), '失败', len(failed), flush=True)
