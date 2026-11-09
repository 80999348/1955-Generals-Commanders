import asyncio, json, re, io, os, random, time
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
print('total', len(names), 'done', len(done), 'todo', len(todo), flush=True)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
GOOD = re.compile(r'少将|中将|上将|将军|红军|八路军|新四军|军区|军长|政委|纵队|兵团|革命')
BAD_DESC = re.compile(r'游戏|演员|歌手|作家|画家|书法|影视|小说|动漫|足球|篮球|教授|董事长|市长|县长|主持人')


def clean(t):
    t = re.sub(r'\[\d+(-\d+)?\]', '', t)
    t = t.replace('\u200b', '').replace('\xa0', ' ')
    t = re.sub(r'\s*\n\s*', ' ', t)
    t = re.sub(r'\s{2,}', ' ', t)
    return t.strip()


async def get_summary(pg, url):
    r = await pg.goto(url, timeout=25000, wait_until='domcontentloaded')
    await pg.wait_for_timeout(500)
    title = await pg.title()
    if '安全验证' in title:
        return 'CAPTCHA', title
    if '百度百科' not in title:
        return None, title
    for sel in ['div[class*="lemmaSummary"]', 'div[class*="summary"]']:
        el = await pg.query_selector(sel)
        if el:
            t = clean(await el.inner_text())
            if len(t) > 25:
                return t, title
    return None, title


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
        ctx = await b.new_context(user_agent=UA, viewport={'width': 1280, 'height': 900})
        pg = await ctx.new_page()
        fails = []
        cnt = 0
        for name in todo:
            cnt += 1
            try:
                url = BASE + name
                r = await pg.goto(url, timeout=25000, wait_until='domcontentloaded')
                title = await pg.title()
                if '安全验证' in title:
                    print('CAPTCHA at', name, 'sleep 90', flush=True)
                    await asyncio.sleep(150)
                    r = await pg.goto(url, timeout=25000, wait_until='domcontentloaded')
                    await pg.wait_for_timeout(600)
                    if '安全验证' in await pg.title():
                        fails.append(name); continue
                await pg.wait_for_timeout(400)
                html = await pg.content()
                subs = re.findall(r'"lemmaId":(\d+),"lemmaTitle":"([^"]*)","lemmaDesc":"([^"]*)"', html)
                best = None
                for lid, lt, ld in subs:
                    if '少将' in ld and not BAD_DESC.search(ld):
                        if '开国' in ld:
                            best = (lid, ld); break
                        if not best:
                            best = (lid, ld)
                got = False
                if best:
                    desc, t2 = await get_summary(pg, f'{BASE}{name}/{best[0]}')
                    if desc == 'CAPTCHA':
                        await asyncio.sleep(150)
                        desc, t2 = await get_summary(pg, f'{BASE}{name}/{best[0]}')
                    if desc and desc != 'CAPTCHA' and GOOD.search(desc):
                        done[name] = {'desc': desc[:400], 'url': f'{BASE}{name}/{best[0]}', 'sub': best[1]}
                        got = True
                if not got:
                    for sel in ['div[class*="lemmaSummary"]', 'div[class*="summary"]']:
                        el = await pg.query_selector(sel)
                        if el:
                            t = clean(await el.inner_text())
                            if len(t) > 25 and GOOD.search(t):
                                done[name] = {'desc': t[:400], 'url': url}
                                got = True
                            break
                if not got:
                    fails.append(name)
            except Exception as e:
                fails.append(name)
            if cnt % 25 == 0:
                json.dump(done, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
                print('progress', cnt, '/', len(todo), 'ok', len(done), flush=True)
            await asyncio.sleep(random.uniform(1.6, 2.6))
        json.dump(done, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        print('FINISHED ok', len(done), 'fails', len(fails), flush=True)
        io.open('/root/.codebuddy/artifact/data/baike_fail_names.txt', 'w', encoding='utf-8').write('\n'.join(fails))
        await b.close()


asyncio.run(main())
