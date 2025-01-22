#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 expandtab number
"""
doctest非常脑残；无法正确理解python string中的转义
只好写 pytest单测

Authors: qianweishuo<qianweishuo@bytedance.com>
Date:    2020/3/26 11:51 下午
"""
from ankdown.ankdown import compile_field, textcolor2color


def test_textcolor2color():
    latex_in = r"a \textcolor[rgb]{0.82,0.01,0.11}{f(x)} b"
    latex_out = textcolor2color(latex_in)
    assert latex_out == r"a \color{#D1021C}{f(x)} b"


def test_surrounded_bold():
    mkd_in = r"a *bold1* b, c*bold2*d"
    mkd_out = compile_field(mkd_in, is_markdown=True)
    assert mkd_out == r"a <em>bold1</em> b, c<em>bold2</em>d"
