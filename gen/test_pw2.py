from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    pg = ctx.new_page()
    pg.goto('https://baike.baidu.com/item/%E4%B8%81%E5%85%88%E5%9B%BD', timeout=30000, wait_until='domcontentloaded')
    pg.wait_for_timeout(1200)
    for sel in ['div.lemma-summary','div[class*="lemmaSummary"]','div.J-lemma-summary','div[class*="summary"]']:
        try:
            el = pg.query_selector(sel)
            print(sel, '->', (el.inner_text()[:160].replace('\n',' ') if el else 'None'))
        except Exception as e:
            print(sel,'ERR',str(e)[:50])
    # 人物生平首段
    try:
        paras = pg.query_selector_all('div[class*="para"]')
        print('para count', len(paras))
        if paras: print('para1:', paras[0].inner_text()[:150].replace('\n',' '))
    except Exception as e: print('para ERR', e)
    # 取 h2 人物生平 之后
    txt = pg.inner_text('body')
    i = txt.find('人物生平')
    print('生平段:', txt[i:i+260].replace('\n',' '))
    b.close()
