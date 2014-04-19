#!/usr/bin/env python

import xml.etree.ElementTree as ET
import re
import sys

''' 
Extracting stress meta-symbol to remove it from pages.
This may look funny, but I know no other way.
'''
stress = 'и́'[1]

''' 
Extracts usage of single template from page.
Template suppose to start from template_start_re regexp.
'''
def extract_template(text, template_start_re):
    template = re.search(template_start_re, text)
    if not template:
        return

    text = list(text)
    n = 1
    i = template.start() + 1
    while i < len(text) and n > 0:
        if text[i] == '{':
            n = n + 1
        if text[i] == '}':
            n = n - 1
        if n > 2 and text[i] == '|':
            text[i] = '№'
        i = i + 1

    if n != 0:
        return

    return ''.join(text[template.start():i])

# TODO handle multiple {-ru-} per page
'''
Process single wiktionary page
'''
def handle_page(text, word):
    word = word.replace(stress, '')
    if not text or not re.match('[А-ЯЁ]?[а-яё]+', word):
        return
    word = word.lower()

    ru = re.search('{{-ru-}}', text)
    if not ru:
        return

    text = text[ru.start() + len('{{-ru-}}'):]

    other = lang.search(text)
    if other:
        text = text[:other.start()]

    text = text.replace(stress, '')

    morf = extract_template(text, '{{морфо')
    if morf is None:
        return
    morf = morf.lower()

    """ FIXME добавить поддержку j """
    if re.search('[^}{а-яё1-5|=-]', morf):
        return
    if re.match('{{морфо(\|+[а-я-]+[1-5]?=)+}}', morf) or re.match('{{морфо\|+}}', morf):
#        print('skipping', word, morf)
        return

    table_template_call = extract_template(text, '{{(прич|сущ|гл|мест|прил|числ) ru ')
    if table_template_call is None:
#        print('no table call for', word)
        return

    template_name = table_template_call[2:table_template_call.index('|')].strip()
    template_params = table_template_call[2:-2].lower().replace('\n', '').replace(' ', '').split('|')[1:]
    filtered_params = filter(lambda s: re.match('основа[1-5]?=[а-яё-]+', s) or re.match('[а-яё-]+$', s), template_params)
    filtered_params = list(filtered_params)
    if len(filtered_params) == 0:
        return

    return (morf, template_name, filtered_params)

'''
Extracts {{{морфо}}} template and stems from wiktionary dump
'''
def extract_meta_partitions(filename='ruwiktionary.xml'):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    page = False
    word = ''
    text = ''

    lang = re.compile('{{-[a-z]{2,3}-}}')

    namespace = '{http://www.mediawiki.org/xml/export-0.8/}'
    for event, elem in context:
        if elem.tag == namespace + 'page':
            if event == 'start':
                page = True
                continue
            else:
                try:
                    extracted = handle_page(text, word)
                    if extracted is not None:
                        yield extracted
                except Exception as e:
                    print('exception', e, word, text)
                    input()

        if page and event == "end" and elem.tag == namespace + 'title':
            word = elem.text

        if page and event == 'end' and elem.tag == namespace + 'text':
            text = elem.text

        if event == 'end':
            elem.clear()

    root.clear()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extracts meta information about partition from ruwiktionary dump')
    parser.add_argument('-f', '--filename', default='ruwiktionary.xml', help='wiktionary dump file')
    args = parser.parse_args()
    extracted = extract_meta_partitions(args.filename)
    for morf, template_name, template_params in extracted:
        print(morf, template_name, *template_params, sep=';')
