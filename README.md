# Ankdown 魔改版

A simple way to write Anki decks in Markdown.
加强了对公式和连续花括号的支持.

## Installing

`pip3 install git+https://github.com/koyo922/ankdown.git`

## Writing Cards

Cards are written in the following format:

```markdown
Expected Value of $f(x)$

%

$$\mathbb{E}[f(x)] = \sum_x p(x)f(x)$$

%

math, probability

---
```

Each of the solitary `%` signs is a field separator: the first
field is the front of the card by default, the second field is
the back of the card, and subsequent fields can contain whatever
you want them to (all fields after the second are optional).

Each of the `---` (or double `%%`) signs represent a card boundary.

The tool only needs these separators to be alone on their own lines,
but most markdown editors will work better if you separate them from
other text with empty lines, so that they're treated as their own
paragraphs.

## Running Ankdown

1. 在马克飞象等编辑器中编辑markdown
    - 如果要从mathcha->mathjax拷贝含有字体颜色的公式, 会遇到 `\textcolor`转换问题
    - 可以 `pbpaste | python -m ankdown.textcolor2color | tee >(pbcopy) | head -c 100`
2. 在马克飞象中`cmd+C`复制感兴趣的内容段
3. 编译至`txt`文件; `pbpaste | ankdown -u -i /dev/stdin -o /dev/stdout | tee anki.txt | head`
4. To add them to Anki, go to `File > Import`, and select the file you created
	- 注意分隔符是`\t`而非`<comma>`
	- 记得勾选`Allow HTML`
