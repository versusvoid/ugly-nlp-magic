#!/usr/bin/env python

import re
import os
import sys
import xml.etree.ElementTree as ET
import extract_pages
import requests

'''
Converts html template table to plaintext table and saves it
'''
def render(template_name, text, dest_dir):
    parser = ET.XMLPullParser(events=("start", "end"))
    parser.feed('<fakeroot>')
    parser.feed(text)

    filename = os.path.join(dest_dir, template_name.replace('Шаблон:', '').replace('/', '%') + '.table')
    of = open(filename, 'w')

    table = False

    try:
        for event, elem in parser.read_events():
            if event == 'start' and elem.tag == 'table' and 'style' in elem.attrib and re.match('float *: *right;', elem.attrib['style']):
                table = True

            if table and event == 'end' and elem.tag == 'table':
                break

            if table and event == 'end' and elem.tag == 'tr':
                print('', file=of)

            if table and event == 'end' and (elem.tag == 'th' or elem.tag == 'td'):
                text = elem.text
                if text is None:
                    a = elem.find('a')
                    if a is not None: text = a.text
                if text is None:
                    text = ''
                print(text.strip(), '|', end=' ', file=of)

            if not table and event == 'end':
                elem.clear()
    except ET.ParseError as e:
        print(e)
        os.remove(filename)
        exit(1)

    of.close()


'''
Extracts template table pages, asks wiktionary.org to render it to html
and then converts html to plaintext
'''
def extract_and_render(filename='ruwiktionary.xml', dest_dir='tables'):
    print('Parsing wiktionary dump for templates, be patient')
    template_names = extract_pages.extract('Шаблон:(прич|сущ|гл|мест|прил|числ) ru', filename)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for template_name in template_names:
        params = {
            'action': 'render',
            'title': template_name
        }
        print('Rendering html for', template_name)
        r = requests.get('http://ru.wiktionary.org/w/index.php', params=params)

        if r.status_code == 200:
            render(template_name, r.text, dest_dir)
        else:
            print("Can't get", template_name, "template from wiktionary =\\")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extracts and renders template tables from ruwiktionary in plain text')
    parser.add_argument('-f', '--filename', default='ruwiktionary.xml', help='wiktionary dump file')
    parser.add_argument('-d', '--dest-dir', default='tables', help='directory to extract tables into')
    args = parser.parse_args()

    extract_and_render(args.filename, args.dest_dir)
