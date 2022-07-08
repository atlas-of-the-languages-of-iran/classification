import io
import re
import shutil
import pathlib
import collections

from lxml import etree

from clldutils.misc import slug

PREFIXES = collections.defaultdict(int)
MD_TMPL = """# -*- coding: utf-8 -*-
[core]
name = {}
level = family

[classification]

[altnames]
ali =
{} 
"""


def glottocode(n):
    n = slug(n)
    prefix = n[:4].rjust(4, n[-1])
    PREFIXES[prefix] += 1
    return prefix + str(10000 - PREFIXES[prefix])


def level(e):
    l = 0
    p = e.getparent()
    while p and p.tag:
        if p.tag == 'ul':
            l += 1
        p = p.getparent()
    return l


def span_and_sup(e):
    # must stop lookin for text at <ul>
    # tex an also be in font!
    span, sup = '', ''

    for node in etree.ElementDepthFirstIterator(e):
        if node.tag == 'ul':
            break
        if getattr(node, 'tag', None) and node.text:
            if node.tag == 'sup':
                sup += node.text
            else:
                span += node.text
    return re.sub(r'\s+', ' ', span).strip(), sup


def names(n):
    name, alt = n, []
    n = n.replace('(0)', '')
    if '(' in n:
        name, _, rem = n.partition('(')
        for nn in re.split(',|;', rem.replace(')', '')):
            if nn.strip():
                alt.append(nn.strip())
    return name, '\n'.join('\t{}'.format(nn) for nn in alt)


def parse(p):
    d = etree.parse(io.StringIO(pathlib.Path(p).read_text(encoding='utf8')), etree.HTMLParser())
    body = d.xpath('.//body')[0]

    out = pathlib.Path(__file__).resolve().parent.parent / 'languoids' / 'tree'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    currdir, currlevel = out, 0
    for li in body.xpath('.//li'):
        l = level(li)
        if l > currlevel:
            assert l == currlevel + 1
        else:
            for _ in range(currlevel + 1 - l):
                currdir = currdir.parent
        text, fn = span_and_sup(li)
        gc = glottocode(text)
        if not text.startswith('['):
            #print('{}{} {} {}'.format('  ' * l, gc, text, fn))
            currdir.joinpath(gc).mkdir()
            currdir.joinpath(gc, 'md.ini').write_text(MD_TMPL.format(*names(text)), encoding='utf8')
        #if text.startswith('Caspian'):
        #    break
        currdir = currdir / gc
        currlevel = l


if __name__ == '__main__':
    parse('atlas_classification.html')
