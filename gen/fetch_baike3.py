# -*- coding: utf-8 -*-
"""补抓失败词条：合并模式 + 低并发 + 退避重试"""
import json, re, time, io, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://baike.baidu.com/api/openapi/BaikeLemmaCardApi?scope=103&format=json&appid=379020&bk_length=600&bk_key="
HDRS = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"}
VALID = re.compile(r'少将|中将|上将|将军|解放军|红军|八路军|新四军|军区|军长|政委|军委|司令|参谋|军队|军人|革命|干部|共产党')

try:
    result = json.load(io.open('/root/.codebuddy/artifact/data/baike.json', encoding='utf-8'))
except Exception:
    result = {}
old_ok = set(result.keys())

names = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/shaojiang_names.txt', encoding='utf-8') if l.strip()]
todo = sorted(set(names) - old_ok)
print('待补抓:', len(todo), flush=True)

def api_call(key):
    url = API + urllib.parse.quote(key)
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

def fetch(name):
    attempts = [(name, 1), (name + "少将", 1), (name + "（中国人民解放军少将）", 1), (name + "（开国少将）", 1), (name, 2), (name + " 开国少将", 1), (name, 3)]
    for key, tries in attempts:
        for t in range(tries):
            try:
                d = api_call(key)
                desc = d.get('desc') or ''
                if desc and VALID.search(desc):
                    return name, {'title': d.get('key') or '', 'desc': desc,
                                  'url': 'https://baike.baidu.com/item/' + urllib.parse.quote(key)}
                break  # 词条命中但非开国少将 → 换下一个查询词
            except Exception:
                time.sleep(1.5 * (t + 1))
        time.sleep(0.3)
    return name, None

with ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(fetch, n): n for n in todo}
    done = 0
    for f in as_completed(futs):
        n, r = f.result()
        if r:
            result[n] = r
        done += 1
        if done % 60 == 0:
            print(f'进度 {done}/{len(todo)} 累计成功{len(result)}', flush=True)

io.open('/root/.codebuddy/artifact/data/baike.json', 'w', encoding='utf-8').write(
    json.dumps(result, ensure_ascii=False, indent=0))
failed = sorted(set(names) - set(result.keys()))
io.open('/root/.codebuddy/artifact/data/baike_failed2.txt', 'w', encoding='utf-8').write('\n'.join(failed))
print('完成: 总成功', len(result), '最终失败', len(failed), flush=True)
print('最终失败:', ' '.join(failed[:80]), flush=True)
