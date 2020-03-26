#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 expandtab number
"""
将mathcha中的 `\textcolor` 格式改成 mathjax兼容的 `color`格式
同时提供为一个命令行工具

Authors: qianweishuo<qianweishuo@bytedance.com>
Date:    2020/3/27 12:03 上午
"""
import re
import sys
from typing import Match


def _rep_fn(m: Match):
    hex_color = '#' + ''.join([f"{int(float(g) * 255):02X}" for g in m.groups()])
    return r'\color{%s}' % hex_color


def conv(latex_in):
    """ 将mathcha中的 `\textcolor` 格式改成 mathjax兼容的 `color`格式 """
    latex_out = re.sub(r"\\textcolor\[rgb\]\{([\d\.]+),([\d\.]+),([\d\.]+)\}", _rep_fn, latex_in)
    return latex_out


if __name__ == '__main__':
    sys.stdout.write(conv(sys.stdin.read()))
    sys.stdout.flush()
