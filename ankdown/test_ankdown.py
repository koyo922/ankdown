#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 expandtab number
"""
doctest非常脑残；无法正确理解python string中的转义
只好写 pytest单测

Authors: qianweishuo<qianweishuo@bytedance.com>
Date:    2020/3/26 11:51 下午
"""
from ankdown.ankdown import compile_field
from ankdown.textcolor2color import conv as textcolor2color


def test_textcolor2color():
    latex_in = r"a \textcolor[rgb]{0.82,0.01,0.11}{f(x)} b"
    latex_out = textcolor2color(latex_in)
    assert latex_out == r"a \color{#D1021C}{f(x)} b"


def test_surrounded_bold():
    mkd_in = r"a *bold1* b, c*bold2*d, L=$2*\pi*r$"
    mkd_out = compile_field(mkd_in, is_markdown=True)
    assert mkd_out == r"<p>a <em>bold1</em> b, c<em>bold2</em>d, L=$2*\pi*r$</p>&#10;"


def test_multiline_math():
    mkd_in = r"""Here's a multiline equation:
$$
\begin{align*}
y &= x^2 + 2x + 1 \\
  &= (x+1)^2
\end{align*}
$$
And some text after."""
    mkd_out = compile_field(mkd_in, is_markdown=True)
    expected = r"""<p>Here's a multiline equation:&#10;$$&#10;\begin{align*}&#10;y &= x^2 + 2x + 1 \\&#10;  &= (x+1)^2&#10;\end{align*}&#10;$$&#10;And some text after.</p>&#10;"""
    assert mkd_out == expected


def test_mermaid():
    mkd_in = r"""
```mermaid
graph TD
    A --> B
    B --> C
    C --> D
    D --> A
```
"""
    mkd_out = compile_field(mkd_in, is_markdown=True)
    expected = "<div class='mermaid'>&#10;graph TD&#10;    A --> B&#10;    B --> C&#10;    C --> D&#10;    D --> A&#10;</div>&#10;"
    assert mkd_out == expected
