#!/usr/bin/env python3
#
# quick-n-dirty formatter for SPDX licenses in XML format
#
# Copyright (c) 2017 Alexios Zavras
# SPDX-License-Identifier: MIT
#

#-----------------------------------------------------------------
# configuration parameters, self-explanatory :-)
# they are simply defaults; can be overwritten by command-line options

INDENT = 2
LINE_LENGTH = 80

# which tags are inline and which appear on their own lines
TAGS_inline = [
        'alt',
        'b',
        'br',
        'copyright',
        'url',

        'crossRef',
        'bullet',

    ]
TAGS_block = [
        'body',
        'header',
        'li',
        'license',
        'list',
        'notes',
        'optional',
        'p',
        'SPDX',
        'title',
        'urls',

        'SPDXLicenseCollection',
        'license',
        'crossRefs',
        'standardLicenseHeader',
        'notes',
        'titleText',
        'item',
        'copyrightText',
        'text'

    ]

# attributes for tags, in the order we want them to appear
ATTRS_SEQ = {
        'SPDXLicenseCollection': [
            'xmlns',
        ],
        'license': [
            'isOsiApproved',
            'licenseId',
            'name',
            'listVersionAdded',
        ],
        'alt': [
            'name',
            'match',
        ],
    }

# namespace for all tags
NAMESPACE_URL = 'http://www.spdx.org/license'
NAMESPACE='{http://www.spdx.org/license}'

#-----------------------------------------------------------------

VERSION = '1.0'

import argparse
import datetime
import logging
import re
import shutil
import sys
import xml.etree.ElementTree as et

NL = '\n'
XML_PROLOG = """<?xml version="1.0" encoding="UTF-8"?>"""

logging.basicConfig(filename="error.log", format="%(levelname)s : %(asctime)s : %(message)s")
logger = logging.getLogger()

def process(fname):
    tree = et.parse(fname)
    root = tree.getroot()
    if root.tag == 'spdx':
        root.tag = 'SPDX'
        logger.error('changing root element to SPDX (capital letters)')
    #ts = '{:%Y%m%d%H%M%S%z}'.format(datetime.datetime.now())
    root.set('xmlns', NAMESPACE_URL)
    blocks = pretty(root, 0)
    ser = fmt(blocks)
    
    with open(fname, 'w') as f:
        f.write(XML_PROLOG+"\n")
        f.write(ser)
    


def pretty(node, level):
    ser = ''
    tag = node.tag
    if tag.startswith(NAMESPACE):
        tag = tag[len(NAMESPACE):]
    text = singlespaceline(node.text)
    tail = singlespaceline(node.tail)
    # print("\t", level, tag, 'text=', text, 'tail=', tail, node.attrib)
    start_tag = "<" + tag
    if node.attrib and tag in ATTRS_SEQ:
        for a in ATTRS_SEQ[tag]:
            if a in node.attrib:
                start_tag += ' {}="{}"'.format(a, node.attrib[a])
                del node.attrib[a]
        if node.attrib:
            logger.error('more attrs remaining in {}: {}'.format(tag, node.attrib.keys()))
    start_tag += ">"
    end_tag = "</" + tag + ">"
    if tag in config['block']:
        child_level = level + 1
        before = '{0}{1}#{2}{0}{3}#'.format(NL, level, start_tag, child_level)
        after = '{0}{1}#{2}{0}'.format(NL, level, end_tag)
    elif tag in config['inline']:
        child_level = level
        before = start_tag
        after = '{1}{0}{2}#'.format(NL, end_tag, level)
    else:
        logger.error('Tag "{}" neither block nor inline!'.format(tag))
        child_level = level
        before = start_tag
        after = end_tag
    ser += before
    if text:
        text = text.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;')
        ser += text
    for child in node:
        ser += pretty(child, child_level)
    ser += after
    if tail:
        ser += tail
    ser = ser.replace('\n\n', '\n')
    return ser

def fmt(blocks):
    bregexp = re.compile(r'((?P<level>\d+)#)?(?P<paragraph>.*)')
    ser = ''
    for line in blocks.split('\n'):
        if line == '':
            continue
        m = bregexp.match(line)
        if m.group('level'):
            l = int(m.group('level'))
        else:
            logger.error('Block without level: "{}"'.format(line))
        par = m.group('paragraph')
        if par == '':
            continue
        indent = l * config['lvl_indent']
        width = config['max_width'] - indent
        for fmtline in to_lines(par, width):
            ser += indent * ' ' + fmtline + '\n'
    return ser


def to_lines(text, width):
    words = text.split()
    count = len(words)
    last_offset = 0
    offsets = [last_offset]
    for w in words:
        last_offset += len(w)
        offsets.append(last_offset)

    cost = [0] + [10 ** 20] * count
    breaks = [0] + [0]      * count
    for i in range(count):
        j = i + 1
        while j <= count:
            w = offsets[j] - offsets[i] + j - i - 1
            if w > width:
                break
            penalty = cost[i] + (width - w) ** 2
            if penalty < cost[j]:
                cost[j] = penalty
                breaks[j] = i
            j += 1
    lines = []
    last = count
    while last > 0:
        first = breaks[last]
        lines.append(' '.join(words[first:last]))
        last = first
    lines.reverse()
    return lines


def singlespaceline(txt):
    if txt:
        txt = txt.strip()
        txt = re.sub(r'\s+', ' ', txt)
    return txt


# main program

if NAMESPACE:
    full_TAGS_inline = list(NAMESPACE+e for e in TAGS_inline)
    full_TAGS_block = list(NAMESPACE+e for e in TAGS_block)
    full_ATTRS_SEQ = dict((NAMESPACE+k, v) for k,v in ATTRS_SEQ.items())

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description='Indent XML file(s)')
    parser.add_argument('filename', nargs='+',
            help='the XML files to process')
    parser.add_argument('-w', '--width', action='store', type=int,
            default = LINE_LENGTH,
            help='the maximum width of the lines in output')
    parser.add_argument('-i', '--indent', action='store', type=int,
            default = INDENT,
            help='the number of spaces each level is indented')
    parser.add_argument('--inline-tags', action='store',
            help='space-separated list of tags to be rendered inline')
    parser.add_argument('--block-tags', action='store',
            help='space-separated list of tags to be rendered as blocks')
    parser.add_argument('-V', '--version', action='version',
            version='%(prog)s ' + VERSION,
            help='print the program version')

    args = parser.parse_args()

    config = dict()
    config['inline'] = TAGS_inline
    config['block'] = TAGS_block
    config['max_width'] = args.width
    config['lvl_indent'] = args.indent
    if args.inline_tags:
        config['inline'] = args.inline_tags.split()
    if args.block_tags:
        config['block'] = args.block_tags.split()

    for fname in args.filename:
        try:
            process(fname)
        except et.ParseError as e:
            logger.error('XML Parse Error: ' + str(e))
            print('XML Parse Error: ' + str(e))
