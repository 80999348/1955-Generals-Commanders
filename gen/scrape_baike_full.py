import asyncio, json, re, io, os
from playwright.async_api import async_playwright

BASE = 'https://baike.baidu.com/item/'
OUT = '/root/.codebuddy/artifact/data/baike_full.json'
names = json.load(io.open('/root/.codebuddy/artifact/data/short_names.json', encoding='utf-8'))
done = {}
if os.path.exists(OUT):
    try:
        done = json.load(io.open(OUT, encoding='utf-8'))
    except Exception:
        done = {}
todo = [n for n in names if n not in done]
print('total', len(names), 'todo', len(todo), flush=True)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
GOOD = re.compile(r'少将|中将|上将|将军|红军|八路军|新四军|军区|军长|政委|纵队|兵团|革命')
BAD_DESC = re.compile(r'游戏|演员|歌手|作家|画家|书法|影视|小说|动漫|足球|篮球|教授|董事长|市长|县长|歌手|主持人|烈士陵园')


def clean(t):
    t = re.sub(r'\[\d+(-\d+)?\]', '', t)
    t = t.replace('\u200b', '').replace('\xa0', ' ')
    t = re.sub(r'\s*\n\s*', ' ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()


async def summary_of(pg, url):
    await pg.goto(url, timeout=25000, wait_until='domcontentloaded')
    await pg.wait_for_timeout(600)
    title = await pg.title()
    if '安全验证' in title or '百度百科' not in title:
        return None, None
    for sel in ['div[class*="lemmaSummary"]', 'div[class*="summary"]']:
        el = await pg.query_selector(sel)
        if el:
            t = clean(await el.inner_text())
            if len(t) > 25:
                return t, title
    return None, title


async def one(ctx, name, sem, buf):
    async with sem:
        pg = await ctx.new_page()
        try:
            await pg.goto(BASE + name, timeout=25000, wait_until='domcontentloaded')
            await pg.wait_for_timeout(500)
            html = await pg.content()
            subs = re.findall(r'"lemmaId":(\d+),"lemmaTitle":"([^"]*)","lemmaDesc":"([^"]*)"', html)
            best = None
            for lid, lt, ld in subs:
                if '少将' in ld and not BAD_DESC.search(ld):
                    if '开国' in ld:
                        best = (lid, ld); break
                    if not best:
                        best = (lid, ld)
            if best:
                url = f'{BASE}{name}/{best[0]}'
                desc, title = await summary_of(pg, url)
                if desc and GOOD.search(desc) and ('少将' in html or '1955' in desc):
                    buf[name] = {'desc': desc[:400], 'url': url, 'sub': best[1]}
                    return
            # 默认页本身就是本人
            desc = None
            for sel in ['div[class*="lemmaSummary"]', 'div[class*="summary"]']:
                el = await pg.query_selector(sel)
                if el:
                    t = clean(await el.inner_text())
                    if len(t) > 25:
                        desc = t; break
            if desc and GOOD.search(desc) and ('少将' in (await pg.content()) or '1955' in desc):
                buf[name] = {'desc': desc[:400], 'url': BASE + name}
        except Exception:
            pass
        finally:
            await pg.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
        ctx = await b.new_context(user_agent=UA, viewport={'width': 1280, 'height': 900})
        sem = asyncio.Semaphore(4)
        buf = {}
        tasks = [asyncio.create_task(one(ctx, n, sem, buf)) for n in todo]
        for i in range(0, len(tasks), 40):
            await asyncio.gather(*tasks[i:i + 40], return_exceptions=True)
            done.update(buf); buf.clear()
            json.dump(done, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
            print('progress', len(done), '/', len(names), flush=True)
        json.dump(done, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        print('FINISHED', len(done), flush=True)
        await b.close()


asyncio.run(main())
