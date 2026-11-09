# -*- coding: utf-8 -*-
"""用搜狗搜索为剩余少将补生平（网页快照含百科摘要）"""
import json, re, io, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

H = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"}

def sogou(q, tries=2):
    url = "https://www.sogou.com/web?query=" + urllib.parse.quote(q)
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=20) as r:
                return r.read().decode('utf-8', errors='ignore')
        except Exception:
            time.sleep(2 * (t + 1))
    return ''

def text_of(raw):
    raw = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
    txt = re.sub(r'<[^>]+>', ' ', raw)
    return re.sub(r'\s+', ' ', txt)

def extract(name):
    txt = text_of(sogou(f"{name} 开国少将"))
    m = re.search(re.escape(name) + r'[（(](.{20,340})', txt)
    if not m:
        # 退而求其次：取名字后到"相关搜索"前的内容
        i = txt.find(name, 30000)
        if i > 0:
            seg = txt[i:i + 340]
            if ('少将' in seg or '将军' in seg) and re.search(r'19\d\d', seg):
                return seg.strip()
        return None
    seg = m.group(1)
    # 截断到疑似下一条结果/噪声
    for stop in (' 相关搜索 ', ' 百科 ', ' 打开QQ浏览器 ', ' 图片 '):
        j = seg.find(stop)
        if j > 40:
            seg = seg[:j]
    if ('少将' in seg or '将军' in seg or re.search(r'(军区|红军|八路军|解放军|纵队|军长|政委|司令)', seg)):
        return ('（' + seg).strip()
    return None

def fetch_one(name):
    r = extract(name)
    if not r:
        time.sleep(0.5)
        txt = text_of(sogou(f"{name} 少将 简介"))
        m = re.search(re.escape(name) + r'[（(](.{20,340})', txt)
        if m and ('少将' in m.group(1) or '将军' in m.group(1)):
            r = ('（' + m.group(1)).strip()
    return name, ({'desc': r, 'src': '搜狗·百科快照'} if r else None)

if __name__ == '__main__':
    names = [l.strip() for l in io.open('/root/.codebuddy/artifact/data/baike_failed.txt', encoding='utf-8') if l.strip()]
    print('待抓取:', len(names), flush=True)
    result = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(fetch_one, n): n for n in names}
        for i, f in enumerate(as_completed(futs), 1):
            n, r = f.result()
            if r:
                result[n] = r
            if i % 30 == 0:
                print(f'{i}/{len(names)} 成功{len(result)}', flush=True)
            time.sleep(0.4)
    io.open('/root/.codebuddy/artifact/data/sogou.json', 'w', encoding='utf-8').write(
        json.dumps(result, ensure_ascii=False, indent=0))
    print('完成', len(result), flush=True)
