#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 expandtab number
"""
doctest非常脑残；无法正确理解python string中的转义
只好写 pytest单测

Authors: qianweishuo<qianweishuo@bytedance.com>
Date:    2020/3/26 11:51 下午
"""
from ankdown.ankdown import textcolor2color


def test_textcolor2color():
    latex_in = r"a \textcolor[rgb]{0.82,0.01,0.11}{f(x)} b"
    latex_out = textcolor2color(latex_in)
    assert latex_out == r"a \color{#D1021C}{f(x)} b"
