from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    pg = ctx.new_page()
    pg.goto('https://baike.baidu.com/item/%E4%B8%81%E5%85%88%E5%9B%BD', timeout=30000, wait_until='domcontentloaded')
    pg.wait_for_timeout(1500)
    print('TITLE:', pg.title())
    txt = pg.inner_text('body')
    print('LEN:', len(txt))
    print(txt[:300].replace('\n',' / '))
    b.close()
