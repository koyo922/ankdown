#!/usr/bin/env python
"""Ankdown: Convert delimited Markdown files into anki decks.

This is a hacky script that I wrote because I wanted to use
aesthetically pleasing editing tools to make anki cards, instead of
the (somewhat annoying, imo) card editor in the anki desktop app.

The markdown inputs should look like this:

```
First Card Front ![alt_text](local_image.png)

%

First Card Back: $\\text{TeX inline math}$

%

first, card, tags

---

Second Card Front:

$$ \\text{TeX Math environment} $$

%

Second Card Back (note that tags are optional)
```

Usage:
    ankdown.py [-u] [-i INFILE | -r DIR] [-o OUTFILE | -p PACKAGENAME [-d DECKNAME | -D]]

Options:
    -h --help     Show this help message
    --version     Show version

    -u --UTF8     using utf8 for file IO instead of default ASCII

    -i INFILE     Read the input from INFILE, rather than stdin.
    -r DIR        Recursively visit DIR, accumulating cards from `.md` files.

    -o OUTFILE    Put the results in OUTFILE, still as tab-delimited text
    -p PACKAGE    Instead of a .txt file, produce a .apkg file. recommended.
    -d DECKNAME   When producing a .apkg, this is the name of the deck to use.

    -D            Automatically determine deck names, based on file and directory names.
"""

import hashlib
import os
import random
import re
import sys

import misaka
import genanki

from docopt import docopt

from ankdown import textcolor2color

VERSION = "0.4.0"


def simple_hash(text):
    """MD5 of text, mod 2^31. Probably not a great hash function."""
    h = hashlib.md5()
    h.update(text.encode("utf-8"))
    return int(h.hexdigest(), 16) % (1 << 31)


class Card(object):
    """A single anki card."""

    MODEL_NAME = "Ankdown Model"
    MODEL_ID = simple_hash(MODEL_NAME)
    MODEL = genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[
            {"name": "Question"},
            {"name": "Answer"},
            {"name": "Tags"},
        ],
        templates=[
            {
                "name": "Ankdown Card",
                "qfmt": "{{Question}}",
                "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}",
            },
        ],
        css="""
        .card {
            font-family: 'Crimson Text', 'arial';
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
        }

        .latex {
            height: 0.8em;
        }
        """,
    )

    def __init__(self, filename=None, deckname=None):
        self.fields = []
        self.filename = filename
        self.deckname = deckname

    def has_data(self):
        """True if we have any fields filled in."""
        return len(self.fields) > 0

    def has_front_and_back(self):
        """True if we have at least two fields filled in."""
        return len(self.fields) >= 2

    def add_field(self, contents):
        """Add given text to a new field."""
        self.fields.append(contents)

    def finalize(self):
        """Ensure proper shape, for extraction into result formats."""
        if len(self.fields) > 3:
            self.fields = self.fields[:3]
        else:
            while len(self.fields) < 3:
                self.fields.append('')

    def to_character_separated_line(self, separator="\t"):
        """Produce a tab-separated string containing the fields."""
        return separator.join(self.fields) + "\n"

    def to_genanki_note(self, deck_index=None):
        """Produce a genanki.Note with the specified guid."""
        if deck_index is None:
            deck_index = random.randrange(1 << 30, 1 << 31)

        if self.deckname is not None:
            note_id = (simple_hash(self.deckname) + deck_index)
        else:
            note_id = random.randrange(1 << 30, 1 << 31)
        return genanki.Note(model=Card.MODEL, fields=self.fields, guid=note_id)

    def make_absolute_from_relative(self, filename):
        """Take a filename relative to the card, and make it absolute."""
        if os.path.isabs(filename):
            result = filename
        else:
            if self.filename:
                dirname = os.path.dirname(self.filename)
            else:
                dirname = "."
            result = os.path.abspath(os.path.join(dirname, filename))
        return result

    def media_references(self):
        """Find all media references in a card"""
        for field in self.fields:
            # Find HTML images, at least. Maybe some other things.
            for match in re.finditer(r'src="([^"]*?)"', field):
                yield self.make_absolute_from_relative(match.group(1))
            for match in re.finditer(r'\[sound:(.*?)\]', field):
                yield self.make_absolute_from_relative(match.group(1))


class DeckCollection(dict):
    """Defaultdict for decks, but with stored name."""

    def __getitem__(self, deckname):
        if deckname not in self:
            deck_id = random.randrange(1 << 30, 1 << 31)
            self[deckname] = genanki.Deck(deck_id, deckname)
        return super(DeckCollection, self).__getitem__(deckname)


def sub_for_matches(text, match_iter, sentinel):
    """Substitute a sentinel for every match in the iterable.

    Returns the substituted text and the replaced groups. This only works if
    the matches have exactly one match group (so that match.group(1) returns
    exactly that group).
    """
    text_outside_matches = []
    text_inside_matches = []
    last_match_end = 0
    for match in match_iter:
        text_outside_matches.append(text[last_match_end:match.start()])
        text_inside_matches.append(match.groups()[-1])
        last_match_end = match.end()
    text_outside_matches.append(text[last_match_end:])
    text_with_substitutions = sentinel.join(text_outside_matches)
    return text_with_substitutions, text_inside_matches


# def html_from_math_and_markdown(fieldtext):
#     """Turn a math and markdown piece of text into an HTML and Anki-math piece of text."""
#
#     # NOTE(ben): This is the hackiest of the hacky.
#
#     # Basically, we find all the things that look like they're delimited by `$$` signs,
#     # store them, and replace them with a non-printable character that seems very
#     # unlikely to show up in anybody's code.
#     # Then we do the same for things that look like they're delimited by `$` signs, with
#     # a different nonprintable character.
#     # We run the result through the markdown compiler, hoping (well, I checked) that the
#     # nonprintable characters don't get modified or removed, and then we walk the html
#     # string and replace all the instances of the nonprintable characters with their
#     # corresponding (slightly modified) text.
#
#     # This could be slightly DRYer but it's not that bad.
#     ENV_SENTINEL = '\1'
#     INLINE_SENTINEL = '\2'
#
#     # fieldtext_with_envs_replaced, text_inside_envs = sub_for_matches(
#     #     fieldtext, re.finditer(
#     #         r"(?<=  )\$\$([\s\S]+?)\$\$", fieldtext, re.MULTILINE | re.DOTALL), ENV_SENTINEL)
#     #
#     # sentinel_text, text_inside_inlines = sub_for_matches(
#     #     fieldtext_with_envs_replaced, re.finditer(
#     #         r"(?<=  )\$([^\n]*?\S)\$", fieldtext_with_envs_replaced), INLINE_SENTINEL)
#     sentinel_text = fieldtext
#
#     html_with_sentinels = misaka.html(sentinel_text, extensions=('tables', 'fenced-code', 'footnotes', 'autolink',
#                                                                  'strikethrough', 'underline', 'highlight', 'quote',
#                                                                  'no-intra-emphasis',
#                                                                  'space-headers', 'disable-indented-code',))
#
#     reconstructable_text = []
#     env_counter = 0
#     inline_counter = 0
#     for c in html_with_sentinels:
#         if c == ENV_SENTINEL:
#             # reconstructable_text.append("[$$]")
#             # reconstructable_text.append(text_inside_envs[env_counter])
#             # reconstructable_text.append("[/$$]")
#             env_counter += 1
#         elif c == INLINE_SENTINEL:
#             # reconstructable_text.append("[$]")
#             # reconstructable_text.append(text_inside_inlines[inline_counter])
#             # reconstructable_text.append("[/$]")
#             inline_counter += 1
#         else:
#             reconstructable_text.append(c)
#
#     return ''.join(reconstructable_text)


REGEX_LF_BEFORE_CODE_BLOCK = re.compile(r'\n+(?=```\S+\n)')


def compile_field(field_lines, is_markdown):
    """Turn field lines into an HTML field suitable for Anki."""
    fieldtext = ''.join(field_lines)
    if is_markdown:
        # expand/squeeze 1~many '\n'(s) into TWO-consecutive '\n' s
        # so that code blocks got correctly rendered
        fieldtext = REGEX_LF_BEFORE_CODE_BLOCK.sub(r'\n\n', fieldtext)

        # 先保护数学公式
        math_placeholders = {}
        math_counter = 0

        def protect_math(match):
            nonlocal math_counter
            placeholder = f'MATH_PLACEHOLDER_{math_counter}'
            # 保持原始的换行符，不要转换为&#10;
            math_placeholders[placeholder] = match.group(0)
            math_counter += 1
            return placeholder

        # 先匹配多行数学公式 $$...$$，注意用非贪婪模式
        fieldtext = re.sub(r'\$\$(.*?)\$\$', protect_math, fieldtext, flags=re.DOTALL)
        # 再匹配单行数学公式 $...$
        fieldtext = re.sub(r'\$([^\$\n]+?)\$', protect_math, fieldtext)

        # 先保护 mermaid 代码块
        mermaid_placeholders = {}
        mermaid_counter = 0

        def protect_mermaid(match):
            nonlocal mermaid_counter
            placeholder = f'MERMAID_PLACEHOLDER_{mermaid_counter}'
            content = match.group(1).strip()  # 去掉前后的空白
            # 不要在这里创建完整的 div，而是只保存内容
            mermaid_placeholders[placeholder] = content
            mermaid_counter += 1
            return placeholder

        # 匹配 mermaid 代码块
        fieldtext = re.sub(r'```mermaid\n(.*?)```', protect_mermaid, fieldtext, flags=re.DOTALL)

        escape_math = (fieldtext.replace(r'\\', 'AAADOUBLE_SLASHBBB')
                       .replace('_', 'AAAUNDERSCOREBBB')
                       .replace(r'\#', 'AAASLASH_SHARPBBB')
                       .replace(r'\{', 'AAASLASH_LBRACKBBB').replace(r'\}', 'AAASLASH_RBRACKBBB'))

        html = misaka.html(escape_math, extensions=('tables', 'fenced-code', 'footnotes', 'autolink',
                                                    'strikethrough', 'underline', 'highlight', 'quote',
                                                    # 'no-intra-emphasis',  # 关闭这行，否则*包裹周围的字符会影响<em>解析
                                                    'space-headers', 'disable-indented-code',))

        # 下划线容易被markdown当成 <em>; 注意不要用 @@之类的特殊字符，导致语法错误 在code部分容易被 包裹成<span class='err'>
        unescape_math = (html.replace('AAAUNDERSCOREBBB', '_')
                         .replace('AAADOUBLE_SLASHBBB', r'\\')
                         .replace('AAASLASH_SHARPBBB', r'\#')
                         .replace('AAASLASH_LBRACKBBB', r'\{').replace('AAASLASH_RBRACKBBB', r'\}'))

        escape_cloze = unescape_math[:]  # 消除与原生Anki格式的歧
        while '::' in escape_cloze:
            escape_cloze = escape_cloze.replace('::', ': :')  # 注意可能有连续多段
        while '}}' in escape_cloze:
            escape_cloze = escape_cloze.replace('}}', '} }')  # 注意可能有连续多段
        result = escape_cloze.replace('@{', '{{c1::').replace('@}', r'}}').replace('@:', r'::')  # 用新格式换回Anki

        # 恢复数学公式
        for placeholder, math in math_placeholders.items():
            result = result.replace(placeholder, math)

        # 恢复 mermaid 图表 - 在这里才创建完整的 div，并且转换换行符
        for placeholder, content in mermaid_placeholders.items():
            content_with_escaped_newlines = content.replace('\n', '&#10;')
            # 确保最后一行内容后也有换行符
            div = f"<div class='mermaid'>&#10;{content_with_escaped_newlines}&#10;</div>"
            result = result.replace(placeholder, div)

        # 移除由 misaka 添加的多余 <p> 标签
        result = re.sub(r'<p>((?:<div class=\'mermaid\'>[\s\S]*?</div>))</p>', r'\1', result)

        result = textcolor2color.conv(result)
    else:
        result = fieldtext
    result = re.sub(r'(<br/> ){2,}', '', result)  # 去掉连续的多个换行
    return result.replace("\n", "&#10;")


def produce_cards(infile, filename=None, deckname=None):
    """Given the markdown and math in infile, produce the intended result cards."""
    if deckname is None:
        deckname = "Ankdown Deck"
    current_field_lines = []
    current_card = Card(filename, deckname=deckname)
    for line in infile:
        stripped = line.strip()
        if stripped in ["%%", "---", "%"]:
            is_markdown = not current_card.has_front_and_back()
            field = compile_field(current_field_lines, is_markdown=is_markdown)
            current_card.add_field(field)
            current_field_lines = []
            if stripped in ["%%", "---"]:
                yield current_card
                current_card = Card(filename, deckname=deckname)
        else:
            current_field_lines.append(line)

    if current_field_lines:
        is_markdown = not current_card.has_front_and_back()
        field = compile_field(current_field_lines, is_markdown=is_markdown)
        current_card.add_field(field)
    if current_card.has_data():
        yield current_card


def cards_from_dir(dirname, deckname=None):
    """Walk a directory and produce the cards found there, one by one."""
    for parent_dir, _, files in os.walk(dirname):
        for fn in files:
            if fn.endswith(".md") or fn.endswith(".markdown"):
                if deckname is None:
                    if parent_dir == ".":
                        # Fall back on filename if this is invoked from the
                        # directory containing the md file
                        this_deck_name = fn.rsplit(".", 1)[0]
                    else:
                        this_deck_name = os.path.basename(parent_dir)
                else:
                    this_deck_name = deckname
                path = os.path.join(parent_dir, fn)
                with open(os.path.join(parent_dir, fn), "r") as f:
                    for card in produce_cards(f, filename=path, deckname=this_deck_name):
                        yield card


def cards_to_textfile(cards, outfile):
    """Take an iterable of cards, and turn them into a text file that Anki can read."""
    for card in cards:
        outfile.write(card.to_character_separated_line())


def cards_to_apkg(cards, output_name):
    """Take an iterable of the cards, and put a .apkg in a file called output_name."""

    # NOTE(ben): I'd rather have this function take an open file as a parameter
    # than take the filename to write to, but I'm constrained by the genanki API

    decks = DeckCollection()

    media = set()
    for card in cards:
        card.finalize()
        for media_reference in card.media_references():
            media.add(media_reference)
        deck_index = len(decks[card.deckname].notes)
        decks[card.deckname].add_note(card.to_genanki_note(deck_index=deck_index))

    package = genanki.Package(deck_or_decks=decks.values(), media_files=list(media))
    package.write_to_file(output_name)


def main():
    """Run the thing."""
    arguments = docopt(__doc__, version=VERSION)

    from functools import partial
    from builtins import open
    if arguments['--UTF8']:
        open = partial(open, encoding='utf8')

    in_arg = arguments['-i']
    out_arg = arguments['-o']
    pkg_arg = arguments['-p']
    deck_arg = arguments['-d']
    use_filenames_as_decknames = arguments['-D']
    recur_dir = arguments['-r']

    # Make a card iterator to produce cards one at a time
    need_to_close_infile = False
    if recur_dir:
        if use_filenames_as_decknames:
            card_iterator = cards_from_dir(recur_dir)
        else:
            card_iterator = cards_from_dir(recur_dir, deckname=deck_arg)
    else:
        if in_arg:
            infile = open(in_arg, 'r')
            need_to_close_infile = True
        else:
            infile = sys.stdin
        card_iterator = produce_cards(infile, deckname=deck_arg)

    if pkg_arg:
        cards_to_apkg(card_iterator, pkg_arg)
    elif out_arg:
        with open(out_arg, 'w') as outfile:
            return cards_to_textfile(card_iterator, outfile)
    else:
        return cards_to_textfile(card_iterator, sys.stdout)

    if need_to_close_infile:
        infile.close()


if __name__ == "__main__":
    exit(main())
