#!/usr/bin/env python

import xml.etree.ElementTree as ET
import re

import os
import sys

'''
Reports and optionaly saves page if it matches given pattern
'''
def handle_page(pattern, text, title, dest_dir):
    if not pattern.match(title):
        return

    if dest_dir is None:
        return title
    else:
        filename = os.path.join(dest_dir, title.replace('/', '-').replace(' ', '_'))
        if not os.path.exists(os.path.dest_dir(filename)):
            os.makedirs(os.path.dest_dir(filename))

        f = open(filename, 'a')
        f.write(text)
        f.close()

        return (title, filename)

'''
Extracts pages with titles matching given pattern.
If dest_dir is given, extracts pages content to dest_dir/%title%
'''
def extract(pattern, filename='ruwiktionary.xml', dest_dir=None):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    page = False
    title = ''
    text = ''

    pattern = re.compile(pattern)

    namespace = '{http://www.mediawiki.org/xml/export-0.8/}'
    for event, elem in context:
        if elem.tag == namespace + 'page':
            if event == 'start':
                page = True
                continue
            else:
                try:
                    extracted_page = handle_page(pattern, text, title, dest_dir)
                    if extracted_page is not None:
                        yield extracted_page
                except:
                    print(title, text)

        if page and event == "end" and elem.tag == namespace + 'title':
            title = elem.text

        if page and event == 'end' and elem.tag == namespace + 'text':
            text = elem.text

        if event == 'end':
            elem.clear()

    root.clear()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract pages from ruwiktionary dump according to regexp')
    parser.add_argument('pattern', help='Regexp to search')
    parser.add_argument('-f', '--filename', default='ruwiktionary.xml', help='wiktionary dump file')
    parser.add_argument('-d', '--dest-dir', help='directory to extract pages into (default is none, meaning no extraction will be made)')
    args = parser.parse_args()

    extracted = extract(args.pattern, args.filename, args.dest_dir)
    print(*extracted, sep='\n')
