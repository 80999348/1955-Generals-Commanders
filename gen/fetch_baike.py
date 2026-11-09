# -*- coding: utf-8 -*-
"""从百度百科开放接口批量抓取开国少将词条摘要"""
import json, re, time, sys, io
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.parse

API = "https://baike.baidu.com/api/openapi/BaikeLemmaCardApi?scope=103&format=json&appid=379020&bk_length=600&bk_key="
HDRS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"}

def api_call(key):
    url = API + urllib.parse.quote(key)
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

VALID = re.compile(r'开国少将|中国人民解放军.{0,6}少将|解放军.{0,6}少将|一九五五年授衔|1955年授衔')

def fetch(name):
    # 依次尝试三种查询词
    for key in (name, name + "（开国少将）", name + " 开国少将"):
        try:
            d = api_call(key)
        except Exception:
            time.sleep(0.5)
            continue
        desc = d.get('desc') or ''
        title = d.get('key') or d.get('title') or ''
        if desc and VALID.search(desc):
            return {'title': title, 'desc': desc, 'url': 'https://baike.baidu.com/item/' + urllib.parse.quote(key)}
        time.sleep(0.2)
    return None

names = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/shaojiang_names.txt', encoding='utf-8') if l.strip()]
names = sorted(set(names))
print('待抓取:', len(names), flush=True)

result, failed = {}, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch, n): n for n in names}
    done = 0
    for f in as_completed(futs):
        n = futs[f]
        r = f.result()
        if r:
            result[n] = r
        else:
            failed.append(n)
        done += 1
        if done % 100 == 0:
            print(f'进度 {done}/{len(names)} 成功{len(result)} 失败{len(failed)}', flush=True)

io.open('/root/.codebuddy/artifact/data/baike.json', 'w', encoding='utf-8').write(
    json.dumps(result, ensure_ascii=False, indent=0))
io.open('/root/.codebuddy/artifact/data/baike_failed.txt', 'w', encoding='utf-8').write('\n'.join(failed))
print('完成: 成功', len(result), '失败', len(failed), flush=True)
print('失败名单:', ' '.join(failed[:50]), flush=True)
