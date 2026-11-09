# -*- coding: utf-8 -*-
"""合并名单与简介，生成 assets/data.js（含省份、革命根据地分类）"""
import re, html, json, sys, io
sys.path.insert(0, '/root/.codebuddy/artifact/gen')
from bios1 import YUANSHUAI, DAJIANG
from bios2 import SHANGJIANG
from bios3 import ZHONGJIANG, SHAOJIANG
from bios4 import SHAOJIANG2

SHAOJIANG = {**SHAOJIANG, **SHAOJIANG2}

# 百度百科摘要（少将）
try:
    BAIKE = json.load(io.open('/root/.codebuddy/artifact/data/baike.json', encoding='utf-8'))
except Exception:
    BAIKE = {}
try:
    BIRTH = json.load(io.open('/root/.codebuddy/artifact/data/baike_birth.json', encoding='utf-8'))
except Exception:
    BIRTH = {}
try:
    SOGOU = json.load(io.open('/root/.codebuddy/artifact/data/sogou.json', encoding='utf-8'))
except Exception:
    SOGOU = {}
AGENT = {}
for _i in range(1, 5):
    try:
        AGENT.update(json.load(io.open(f'/root/.codebuddy/artifact/data/agent_bios_{_i}.json', encoding='utf-8')))
    except Exception:
        pass
try:
    BFULL = json.load(io.open('/root/.codebuddy/artifact/data/baike_full.json', encoding='utf-8'))
except Exception:
    BFULL = {}
SENIOR = {}
for _i in range(1, 9):
    try:
        SENIOR.update(json.load(io.open(f'/root/.codebuddy/artifact/data/senior_bios_{_i}.json', encoding='utf-8')))
    except Exception:
        pass
for _alt, _main in [('周恒', '周桓'), ('黄新延', '黄新廷'), ('陈士渠', '陈士榘')]:
    if _alt in SENIOR and _main not in SENIOR:
        SENIOR[_main] = SENIOR[_alt]

def page_text(fn):
    raw = open(fn, 'rb').read()
    t = raw.decode('gb18030', errors='ignore')
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'[\s\u3000]+', ' ', t)

p1 = page_text('/root/.codebuddy/artifact/data/crt.html')
p2 = page_text('/root/.codebuddy/artifact/data/crt2.html')

def seg(src, a, b=None):
    i = src.find(a)
    if i < 0: raise RuntimeError('anchor missing: ' + a)
    i += len(a)
    if b is None: return src[i:]
    j = src.find(b, i)
    return src[i:j]

ys  = [n.strip() for n in seg(p1, '十位元帅', '十位大将').split() if n.strip()]
ds  = [n.strip() for n in seg(p1, '十位大将', '五十七位上将').split() if n.strip()]
sj  = [n.strip() for n in seg(p1, '五十七位上将', '一百七十七位中将').split() if n.strip()]
zj  = [n.strip() for n in seg(p1, '一百七十七位中将', '一千三百六十位少将').split() if n.strip()]

# 名录用字校正
FIX = {'周恒': '周桓', '黄新延': '黄新廷', '陈士渠': '陈士榘'}
ys = [FIX.get(x, x) for x in ys]
ds = [FIX.get(x, x) for x in ds]
sj = [FIX.get(x, x) for x in sj]
zj = [FIX.get(x, x) for x in zj]

full = seg(p1, '一千三百六十位少将')
a = full.find('丁盛'); b = full.find('周九银'); b = full.find(' ', b)
part1 = full[a:b]
q2 = seg(p2, '开国将帅名录（组图）——中红网 首页 >> 英雄报道 中国人民解放军开国将帅名录（组图）', '| 1 2')
c = q2.find('周吉一'); d = q2.find('瞿道文'); d = q2.find(' ', d)
part2 = q2[c:d]
allsha = (part1 + ' ' + part2).replace('郭 强', '郭强').replace('高 锐', '高锐')

sha = []
cur_year = '1955年授予'
for tok in allsha.split():
    m = re.fullmatch(r'(\d{4})年(?:授予|晋升)少将军衔', tok)
    if m:
        cur_year = m.group(1) + '年授晋'
        continue
    if re.fullmatch(r'[\u4e00-\u9fa5·]+', tok):
        sha.append({'n': tok, 'y': cur_year})

# 名录用字校正（原始名单字形有误）
NAME_FIX = {'延懋': '廷懋', '何延一': '何廷一'}
for x in sha:
    x['n'] = NAME_FIX.get(x['n'], x['n'])

# ---------- 省份提取 ----------
PROVS = ["黑龙江","内蒙古","北京","天津","上海","重庆","河北","山西","辽宁","吉林",
         "江苏","浙江","安徽","福建","江西","山东","河南","湖北","湖南","广东","广西",
         "海南","四川","贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆","台湾"]
def prov_of(text):
    """从文本提取省份：优先匹配 'XX省YY人' 句式，否则取首个出现的省份"""
    if not text: return None
    head = text[:42]
    for p in PROVS:
        if p in head:
            return p
    m = re.search(r'((?:' + '|'.join(PROVS) + r')[\u4e00-\u9fa5]{0,5})人', text)
    if m:
        frag = m.group(1)
        for p in PROVS:
            if frag.startswith(p):
                return p
    return None

# ---------- 革命根据地（山头）自动归类 ----------
R1='井冈山·中央苏区（红一方面军）'
R2='湘鄂西·湘鄂川黔（红二方面军）'
R4='鄂豫皖·川陕（红四方面军）'
RS='陕北·陕甘（西北红军）'
RB='百色·左右江（红七军）'
RN='宁都起义·红五军团'
RF='南方游击·新四军（华中）'
RQ='琼崖纵队（海南）'
RD='东北抗联·东北'
RQY='起义将领'
RO='其他（特殊经历·民族代表·院校）'

REGION_RULES = [
 (RQY, ['和平起义','阵前起义','驾机起义','率部起义','率25艘','巡洋舰起义','东北军出身','原国民党']),
 (RQ,  ['琼崖']),
 (RB,  ['百色起义','红七军']),
 (RD,  ['抗联','义勇军']),
 (RN,  ['宁都起义']),
 (R4,  ['红四方面军','鄂豫皖','川陕','黄麻起义','西路军','129师','386旅','385旅','红二十五军','红十五军团']),
 (R2,  ['红二方面军','红二军团','湘鄂西','湘鄂川黔','120师','359旅','红六军团','黔东']),
 (RS,  ['陕北红军','陕甘','西北革命','创建剿匪']),
 (R1,  ['红一方面军','红三军团','红一军团','井冈山','中央苏区','秋收起义','南昌起义','115师','平型关','红五军团','红七军团','红九军团','红三十军']),
 (RF,  ['三年游击','南方游击','新四军','东江纵队','浙东','闽西','闽东','粤赣','沙家浜']),
]
def region_of(bio, name):
    if not bio: return None
    for cat, kws in REGION_RULES:
        for kw in kws:
            if kw in bio:
                return cat
    return None

REGION_MANUAL = {
 '朱德':R1,'彭德怀':R1,'林彪':R1,'刘伯承':R1,'贺龙':R2,'陈毅':R1,'罗荣桓':R1,'徐向前':R4,'聂荣臻':R1,'叶剑英':R1,
 '粟裕':R1,'徐海东':R4,'黄克诚':R1,'陈赓':R1,'谭政':R1,'萧劲光':R1,'张云逸':RB,'罗瑞卿':R1,'王树声':R4,'许光达':R2,
 '王震':R2,'萧克':R2,'李克农':R1,'许世友':R4,'韩先楚':R4,'刘震':R4,'吕正操':RQY,'乌兰夫':RO,'赛福鼎·艾则孜':RO,
 '阿沛·阿旺晋美':RO,'周纯全':R4,'郭天民':R1,'周士第':R1,'傅钟':R1,'宋任穷':R1,'杨至成':R1,'洪学智':R4,
 '李涛':R1,'赖传珠':R1,'陈奇涵':R1,'王宏坤':R4,'苏振华':R1,'周桓':R1,'朱良才':R1,'唐亮':R1,'钟期光':R1,
 '傅秋涛':R1,'王平':R1,'李志民':R1,'赵尔陆':R1,'甘泗淇':R2,'李达':RN,'张宗逊':R1,'陈伯钧':R1,'陈锡联':R4,
 '陈士榘':R1,'宋时轮':R1,'杨得志':R1,'杨成武':R1,'邓华':R1,'黄永胜':R1,'李天佑':RB,'杨勇':R1,'王新亭':R4,
 '陈再道':R4,'彭绍辉':R1,'贺炳炎':R2,'阎红彦':RS,'谢富治':R4,'韦国清':RB,'叶飞':RF,'刘亚楼':R1,
 '董其武':RQY,'陈明仁':RQY,'陶峙岳':RQY,'王建安':R4,'李聚奎':R1,
 '洪水':RO,'唐铎':RO,'曾泽生':RQY,'孔从洲':RQY,'韩练成':RQY,'廖运周':RQY,'邓兆祥':RQY,'刘善本':RQY,'万毅':RQY,
 '周桓':R1,
 # —— 中将"其他"人工校正 ——
 '丁秋生':R1,'王近山':R4,'王道邦':R1,'王紫峰':R1,'文年生':R1,'方强':R1,'孔石泉':R1,'皮定均':R4,
 '匡裕民':R1,'向仲华':R1,'刘忠':R1,'刘少文':R1,'刘金轩':R1,'刘昌毅':R4,'刘浩天':R1,'杜平':R1,
 '杨国夫':R4,'杨梅生':R1,'李天焕':R4,'李成芳':R4,'李作鹏':R1,'肖向荣':R1,'旷伏兆':R1,'吴克华':R1,
 '吴信泉':R1,'吴瑞林':R4,'邱创成':R1,'张才千':R4,'张天云':R4,'张令彬':R1,'张贤约':R4,'张国华':R1,
 '张经武':R1,'张祖谅':R4,'陈康':R4,'陈先瑞':R4,'范朝利':R4,'罗元发':R1,'罗舜初':R1,'周彪':R1,
 '周玉成':R1,'周希汉':R4,'周志坚':R4,'周赤萍':R1,'钟赤兵':R1,'袁升平':R1,'莫文骅':RB,'聂凤智':R4,
 '顿星云':R2,'徐斌洲':R4,'郭化若':R1,'黄新廷':R2,'康志强':R1,'梁从学':R4,'韩伟':R1,'温玉成':R1,
 '曾绍山':R4,'曾思玉':R1,'谢有法':R1,'廖容标':R1,'谭冠三':R1,'饶子健':R1,
 '朵噶·彭措饶杰':RO,'张翼翔':R4,'饶正锡':R1,'姚喆':R1,'钱钧':R4,'唐延杰':R1,'常乾坤':RO,
 '李贞':R2,'王诤':R1,'傅连暲':R1,'聂鹤亭':R1,'贺诚':R1,'倪志亮':R4,
}

def find_bio(bios, n):
    """返回 (简介, 匹配到的字典键)"""
    cands = [n, n.replace('肖', '萧'), n.replace('锺', '钟'),
             n.replace('士渠', '士榘'), n.replace('新延', '新廷'),
             n.replace('仁麟', '仁麒'), n.replace('恒', '桓')]
    for c in cands:
        if c in bios:
            return bios[c], c
    for k, v in bios.items():
        if k.replace('肖', '萧') == n.replace('肖', '萧'):
            return v, k
    return None, None

def build(rank, names, bios, jmap=None):
    """jmap: 元帅/大将用结构化籍贯"""
    out = []
    for x in names:
        if isinstance(x, dict):
            n, y = x['n'], x.get('y')
        else:
            n, y = x, None
        p = {'n': n, 'y': y}
        hb, hbkey = find_bio(bios, n)   # 手写简介：元帅/大将为 dict，其余为 str
        bk = BAIKE.get(n)
        bio = None
        if hb:
            if isinstance(hb, dict):     # 元帅/大将结构化条目
                if hb.get('j'):  p['j'] = hb['j']
                if hb.get('bd'): p['bd'] = hb['bd']
                bio = hb.get('bio')
                if hb.get('gj'): p['gj'] = hb['gj']
            else:
                bio = hb
        if not bio and bk and bk.get('desc'):
            bio = bk['desc']
        sv = SENIOR.get(n)
        if sv and sv.get('desc') and len(sv['desc']) >= 60:
            bio = sv['desc']
        bf = BFULL.get(n)
        if bf and bf.get('desc') and (not bio or len(bio) < 40):
            bio = bf['desc']
            if not bk:
                p['bk'] = bf.get('url')
        if not bio:
            ag = AGENT.get(n)
            if ag and ag.get('desc'):
                bio = ag['desc']
        if not bio:
            sg = SOGOU.get(n)
            if sg and sg.get('desc'):
                bio = sg['desc']
                for stop in (' 全文 ', ' 中文名 ', ' 大家还在搜 ', ' 相关搜索 ', ' 打开QQ浏览器 ', ' 查看更多 '):
                    j = bio.find(stop)
                    if j > 40:
                        bio = bio[:j]
                bio = bio.strip()
        if bio:
            p['bio'] = bio
        if bk:
            p['bk'] = bk['url']
        if 'bk' not in p:
            ag = AGENT.get(n)
            if ag and ag.get('url'):
                p['bk'] = ag['url']
        prov = None
        if jmap and n in jmap:
            prov = prov_of(jmap[n])
        if not prov and sv and sv.get('prov'):
            prov = sv['prov']
        if not prov and bio:
            prov = prov_of(bio)
        if not prov and bk:
            prov = prov_of(bk.get('birth') or '') or prov_of(bk.get('desc', ''))
        if not prov:
            bc = BIRTH.get(n)
            if bc:
                prov = prov_of(bc.get('birth') or '')
        if not prov:
            ag = AGENT.get(n)
            if ag and ag.get('prov'):
                prov = ag['prov']
        if not prov and bio:
            prov = prov_of(bio)
        if prov:
            p['prov'] = prov
        reg = None
        for key in (n, hbkey):
            if key and key in REGION_MANUAL:
                reg = REGION_MANUAL[key]; break
        if not reg and bio:
            reg = region_of(bio, n)
        if reg:
            p['reg'] = reg
        out.append(p)
    return {'rank': rank, 'list': out}

DATA = [
    build('元帅', ys, {x['n']: x for x in YUANSHUAI}, {x['n']: x['j'] for x in YUANSHUAI}),
    build('大将', ds, {x['n']: x for x in DAJIANG}, {x['n']: x['j'] for x in DAJIANG}),
    build('上将', sj, SHANGJIANG),
    build('中将', zj, ZHONGJIANG),
    build('少将', sha, SHAOJIANG),
]
for d in DATA:
    print(d['rank'], len(d['list']),
          '简介:', sum(1 for p in d['list'] if 'bio' in p),
          '省份:', sum(1 for p in d['list'] if 'prov' in p),
          '老区:', sum(1 for p in d['list'] if 'reg' in p))

ABOUT = """
<h2>授衔背景</h2>
<p>1955年2月8日，第一届全国人大常委会第六次会议通过《中国人民解放军军官服役条例》，我军正式实行军衔制。1955年9月27日，中南海怀仁堂举行授衔授勋典礼：毛泽东主席为朱德、彭德怀、林彪、刘伯承、贺龙、陈毅、罗荣桓、徐向前、聂荣臻、叶剑英十位元帅授衔；周恩来总理同日向在京将官授衔。各地驻军随后分别举行授衔仪式。</p>
<p>评衔主要依据1952年军队级别评定，同时综合考虑资历、战功、职务以及各革命历史时期的代表性与平衡。授衔对象涵盖土地革命战争、抗日战争、解放战争三个时期的功勋将领，并有陈明仁、董其武、陶峙岳等起义将领和乌兰夫、赛福鼎·艾则孜、阿沛·阿旺晋美等少数民族代表。</p>
<h2>各衔级规模</h2>
<p>1955年共授予元帅10人、大将10人、上将57人（含1956年补授王建安、1958年补授李聚奎）、中将177人（含1956年补授聂鹤亭、1958年补授贺诚）、少将798人（1955年）。此后至1965年军衔制取消前又陆续晋升、补授少将共1360人，合计通称"开国将帅"1614位。</p>
<h2>按省份划分</h2>
<p>开国将帅籍贯分布高度集中，涌现出一批著名"将军县"：湖北红安（黄安）、江西兴国、湖南平江、安徽金寨、江西吉安（永新）、湖南浏阳、河南新县等。江西、湖北、湖南三省合计占了开国将帅的大半。本应用已为元帅、大将、上将、中将全部人员及有生平资料的少将标注籍贯省份，可在名录页用"按省份"下拉筛选。</p>
<h2>按革命老区（山头）划分</h2>
<p>我军从游击战争中成长，按主要建军根据地和方面军序列，习惯上分为几大"山头"：井冈山与中央苏区（红一方面军）、湘鄂西与湘鄂川黔（红二方面军）、鄂豫皖与川陕（红四方面军）、陕北与陕甘（西北红军）、百色与左右江（红七军）、南方三年游击战争与新四军（华中）、琼崖纵队（海南）、东北抗联（东北），另有宁都起义、以及陈明仁等起义将领。1955年授衔时对各大山头的代表人物均予适当平衡。本应用已按主要革命根据地（山头）为绝大多数将帅归类，可在名录页用"按革命老区"下拉筛选。</p>
<h2>让衔佳话</h2>
<p>主持评衔工作的徐立清本可授上将，主动申请降为中将；许光达多次请求降衔未获批准，毛泽东称赞他"是一面明镜"。这些让衔故事成为我军官兵一致、不计名位精神的生动写照。</p>
<h2>女将军与外籍将军</h2>
<p>李贞是唯一获授军衔的女性（1955年少将）；洪水是唯一的外籍将军（越南籍，同时是越南人民军少将）；唐铎、刘善本、邓兆祥等则代表了特殊的起义与归国经历。</p>
<h2>关于校官</h2>
<p>1955年与将官授衔同时，我军还授予大批大校、上校、中校、少校军衔。校官数量庞大（以万计），且没有完整公开的权威名单，故本应用不设校官总名录，仅收录部分1955年获授大校军衔的知名人物生平以供参考。少将名录中1961年后授晋者，多为1955年的大校。</p>
<h2>资料说明</h2>
<p>本应用名单依据公开史料整理，并与中红网等来源交叉核对。生平简介来源：少将主要摘编自百度百科词条摘要，部分来自人民网、搜狗百科快照，并参照《中国人民解放军将帅名录》的体例整理为籍贯、生卒、任职经历三段式；元帅、大将、上将、中将为按党史资料编写的简编生平。同名少将的词条摘要在个别情况下可能存在混同，敬请留意。深度查询请参考《中国人民解放军将帅名录》。个别早年史料可能与最新党史文献表述存在差异。</p>
<h2>1955年大校代表人物</h2>
<p>肖锋（江西泰和人，1916—1991）：红一军团团政委，金门战斗时任第28军副军长，1955年授大校、1961年晋升少将，数十年坚持写日记达百万字，是重要军史资料。<br>尹先炳（湖北汉川人，1915—1983）：红二方面军团长，第16军首任军长，抗美援朝参战，1955年授大校。后因个人生活作风问题受处分，成为我军严肃军纪的典型案例。</p>
"""

with io.open('/root/.codebuddy/artifact/app/assets/data.js', 'w', encoding='utf-8') as f:
    f.write('const DATA=')
    f.write(json.dumps(DATA, ensure_ascii=False, separators=(',', ':')))
    f.write(';\nconst ABOUT=`')
    f.write(ABOUT.replace('`', '\\`'))
    f.write('`;\n')
print('data.js written')
