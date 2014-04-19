#!/usr/bin/env python

import operator
import os
import re
import sys
import extract_meta_partitions as EMP

def lineno():
    import inspect
    return inspect.currentframe().f_back.f_lineno

# ----------- Подготовка -----------------
'''
Apriori known word parts
'''
inflexions = set([''])
suffixies = set()

'''
Loads set of known word parts from file.
If replace == True then 'ь' and 'ъ' are removed from parts
'''
def load_set(set, filename, replace=False):
    f = open(filename, 'r')
    for l in f:
        l = l.strip()
        if l == '' or l[0] == '#':
            continue
        if replace:
            l = l.replace('ь', '').replace('ъ', '')

        set.add(l)

    f.close()

def load_sets(datadir='../data/morfology'):
    load_set(inflexions, os.path.join(datadir, 'окончания'))
    load_set(suffixies, os.path.join(datadir, 'суффиксы'), True)


'''
Partition part ending in inflexion template
after usage of stem, e.g.:
    'ыйся' 
from
    {{{основа1}}}ыйся
'''
def partition_template_ending(ending):
    partitioned_ending = [ending]

    check_for_inflexion = True
    ''' Постфиксы '''
    if len(partitioned_ending[0]) >= 2:
        last_two_letters = partitioned_ending[0][-2:]
        if last_two_letters == 'ся' or last_two_letters == 'сь':
            check_for_inflexion = len(partitioned_ending[0]) > 2
            if check_for_inflexion:
                partitioned_ending = [partitioned_ending[0][:-2], 'частица_' + last_two_letters]
            else:
                partitioned_ending[0] = 'частица_' + last_two_letters

    check_for_suffixies = False
    ''' Окончания '''
    if check_for_inflexion and partitioned_ending[0] in inflexions:
        partitioned_ending[0] = 'оконч_' + partitioned_ending[0]
        check_for_inflexion = False
    if check_for_inflexion and partitioned_ending[0] not in inflexions:
        check_for_suffixies = True
        for i in range(-3,0):
            if partitioned_ending[0][i:] in inflexions:
                ending_suffixies = partitioned_ending[0][:i]
                partitioned_ending[0] = 'оконч_' + partitioned_ending[0][i:]
                partitioned_ending.insert(0, ending_suffixies)
                break

    if check_for_suffixies:
        if partitioned_ending[0] == 'ь':
            check_for_suffixies = False
            partitioned_ending.pop(0)
        else:
            partitioned_ending[0] = partitioned_ending[0].replace('ь', '')

    if check_for_suffixies and partitioned_ending[0] in suffixies:
        partitioned_ending[0] = 'суфф_' + partitioned_ending[0]
        check_for_suffixies = False
    if check_for_suffixies and not partitioned_ending[0] in suffixies:
        ending_suffixies = partitioned_ending[0]
        suffixies_partition_found = False
        for i in range(1,len(ending_suffixies)):
            if ending_suffixies[:i] in suffixies and ending_suffixies[i:] in suffixies:
                partitioned_ending[0] = 'суфф_' + ending_suffixies[i:]
                partitioned_ending.insert(0, 'суфф_' + ending_suffixies[:i])
                suffixies_partition_found = True
                break

        if not suffixies_partition_found:
            raise Exception(partitioned_ending, ending)

    return ' '.join(partitioned_ending)


class TemplateException(Exception): pass
'''
Creates clojure to return one parsed form
from inflexion table
'''
def template_form_generator(filename, parameter, ending):
    def impl():
        try:
            partitioned_ending = partition_template_ending(ending)
            return (parameter, partitioned_ending)
        except Exception as e:
            print(lineno(), e, filename, parameter, ending)
            raise TemplateException(e)

    return impl

partition_table_templates = {}
'''
Loads and parses all partition table templates 
to partition_table_templates dictionary
'''
def load_partition_table_templates(tables_dir='tables'):
    for filename in os.listdir(tables_dir):
        if filename[-6:] != '.table':
            continue

        f = open(os.path.join(tables_dir, filename), 'r')
        lines = ''.join(f.readlines()).replace(EMP.stress, '')
        f.close()

        templates = {}
        for match in re.finditer('(\{\{\{[^ ]+\}\}\})([а-яё]*)', lines):
            if match.group(0) in templates:
                continue

            clojure = template_form_generator(filename, match.group(1), match.group(2))
            templates[match.group(0)] = clojure

        partition_table_templates[filename[:-6].replace('%', '/')] = templates


# ---------- Извлечение ------------------

'''
Calculates part order and simplified name
'''
def calc_part_order_and_name(part):
    if part[:len('префд')] == 'префд':
        return int(part[len('префд'):]), 'префд'
    elif re.match('прист?[1-3]$', part):
        return 10 + int(part[-1:]), 'прист'
    elif part == 'прист':
        return 10, 'прист'
    elif re.match('корень?1?$', part):
        return 20, 'корень'
    elif re.match('суфф-[1-4]$', part):
        return 30 + int(part[5]), 'суфф'
    elif part == 'оконч-1':
        return 40, 'оконч'
    elif re.match('соед1?$', part):
        return 50, 'соед'
    elif re.match('прист2[1-2]$', part):
        return 60 + int(part[6]), 'прист'
    elif part == 'корень2':
        return 70, 'корень'
    elif re.match('суфф-2[1-4]$', part):
        return 80 + int(part[6]), 'суфф'
    elif part == 'соед2':
        return 90, 'соед'
    elif re.match('прист3[1-2]$', part):
        return 100 + int(part[6]), 'прист'
    elif part == 'корень3':
        return 110, 'корень'
    elif part == 'интер':
        return 120, 'интер'
    elif part == 'суффд1':
        return 130, 'суффд'
    elif re.match('суфф?[1-5]$', part):
        return 140 + int(part[-1:]), 'суфф'
    elif part == 'суфф':
        return 140, 'суфф'
    elif part[:len('оконч')] == 'оконч':
        return 150, 'оконч'
    elif part == 'частица'[:len(part)] or part == 'постфикс':
        return 160, 'частица'
    else:
        raise Exception(part)

'''
Parts, known to be wrong, but present in dumps.
Apr. 19 2014
'''
error_parts = set(['ибелен', 'распре', 'ёхонек', 'ителен', 'надцат', 'привет', 'исмент', 'абелен', 'глобус', 'ирован'])
'''
Order of unnamed parameters in {{{морфо}}} template
'''
parts_order = ['прист1', 'корень1', 'суфф1', 'оконч', 'частица']
'''
Extracts partition of base word form from {{{мофро}}} template
'''
def extract_base_form_partition(morfo):
    partitiond = morfo[2:-2].split('|')[1:]

    normalized = []
    i = 0
    for part in partitiond:
        if part == '':
            i += 1
            continue

        split_index = part.find('=')
        if split_index == len(part) - 1:
            continue

        part_order = None
        part_name = None
        if split_index > -1:
            part_name_match = re.match('[^=]+', part)
            part_name = part_name_match.group(0)
            if part_name == 'источник':
                continue
            if part_name == 'постфикс':
                part_name = 'частица'
            part_order, part_name = calc_part_order_and_name(part_name)
            part = part[split_index + 1:].replace('ь', '').replace('ъ', '')
        elif i < len(parts_order):
            part_order, part_name = calc_part_order_and_name(parts_order[i])
            part = part.replace('ь', '').replace('ъ', '')
            i += 1
        else:
            raise Exception(i, part, morfo)

        if part_name != 'корень' and (len(part) > 6 or part in error_parts):
            raise Exception(i, part_name, part)

        normalized.append((part_order, part_name, part))

    return list(map(lambda t: t[1:], sorted(normalized, key=operator.itemgetter(0))))

def check_for_root_presence(partition):
    return any(map(lambda s: s[0] == 'корень', partition))

'''
For list of qualified stems, e.g.:
    основа1=дом
splits every stem in tuple
    ('основа1', 'дом')
If replace == True, removes 'ь' and 'ъ' from stem.
'''
def split_stems(stems, replace=False):
    for i, stem in enumerate(stems):
        if '=' in stem:
            name, stem = stem.split('=')
            if replace: stem = stem.replace('ь', '').replace('ъ', '')
            stems[i] = (name, stem)
        elif replace:
            stems[i] = stem.replace('ь', '').replace('ъ', '')

    return stems

'''
Partitions stem for inflexion table using partition of base form
'''
def partition_additional_stem(stem, base_form_partition):
    partition = []
    for part_type, part in base_form_partition:
        assert type(part_type) == str
        assert type(stem) == str

        if stem == '' and part_type == 'оконч':
            break

        if stem[:len(part)] == part:
            partition.append((part_type, part))
            stem = stem[len(part):]
        elif part_type == 'суфф':
            if len(part) > 0 and len(stem) > 0 and abs(len(part) - len(stem)) >= 3:
                raise Exception(part, stem, partition, base_form_partition)
            partition.append((part_type, stem))
            stem = ''
            break
        elif part_type == 'корень' and part[:len(stem)] == stem:
            partition.append((part_type, stem))
            stem = ''
            break
        else:
#            print(lineno(), base_form_partition, part, stem)
            return

    if stem != '':
#        print(lineno(), base_form_partition, stems)
        return

    return partition

'''
Partitions stems for inflexion table using partition of base form
'''
def partition_additional_stems(base_form_partition, stems):
    base_form = ''.join(map(operator.itemgetter(1), base_form_partition))
    base_stem_found = False

    stems = split_stems(stems, True)
    new_stems = []
    for i, stem in enumerate(stems):
        name = None
        if type(stem) == tuple:
            name, stem = stem

        if base_form[:len(stem)] == stem:
            base_stem_found = True 
        
        partition = partition_additional_stem(stem, base_form_partition)
        if partition is None:
#            print(lineno(), stems, stem)
            return

        stem = ' '.join(map(lambda p: p[0] + '_' + p[1], partition))
        if name is None:
            new_stems.append(stem)
        else:
            new_stems.append('{}={}'.format(name, stem))

    if not base_stem_found:
        print(lineno(), template_name, base_form_partition, stems)
        return

    return new_stems

''' 
Converts qualified stems list like
    основа=мушк;основа1=мушек 
to dictionary name -> stem, with name like it 
is used in templates.
'''
def fill_stems_dict(stems):
    result = {}
    i = 1
    for stem in split_stems(stems):
        value = stem
        if type(stem) == tuple:
            name, value = stem
            result['{{{' + name + '}}}'] = value
        result['{{{' + str(i) + '}}}'] = value
        i += 1

    if '{{{основа1}}}' in result and not '{{{основа}}}' in result:
        result['{{{основа}}}'] = result['{{{основа1}}}']
    if '{{{основа}}}' in result and not '{{{основа1}}}' in result:
        result['{{{основа1}}}'] = result['{{{основа}}}']

    return result

'''
Check and return template if it has already been parsed, 
and run parsing if not.
'''
def instantiate_template(template_name):

    template = partition_table_templates[template_name]
    if type(template) == set:
        return template

    instantiated_template = set()
    for clojure in template.values():
        instantiated_template.add(clojure())

    partition_table_templates[template_name] = instantiated_template

    return instantiated_template

'''
Render inflexion template
'''
def render_template(template_name, parameters):
    if template_name not in partition_table_templates:
#        print(lineno(), template_name)
        return

    template = instantiate_template(template_name)

    result = []
    for parameter, inflexion in template:
        value = None
        split_index = parameter.find('|')
        if split_index > -1:
            if parameter[:split_index] + '}}}' in parameters:
                value = parameters[parameter[:split_index] + '}}}']
            else:
                value = parameters[parameter[split_index + 1 : parameter.index('}', split_index) + 3]]
        else:
            value = parameters[parameter]

        result.append(value + ' ' + inflexion)

    return result

'''
Checks if partition looks like it should.
'''
def check_partition(partition):
    match = re.match('\w+_[\w-]+( \w+_[\w-]*)* *', partition)
    if not match or match.end(0) != len(partition): raise ValueError("'" + partition + "'")

'''
Extracts partitions with parts annotations from wikionary dump
output_file - file object
'''
def extract_annotated_partitions(output_file, filename='ruwiktionary.xml'):
    meta_partitions = EMT.extract_meta_partitions(filename)
    for morfo, template_name, stems in meta_partitions:
        
        try:
            base_form_partition = extract_base_form_partition(morfo)
            if not check_for_root_presence(base_form_partition):
                continue
            partitiond_stems = partition_additional_stems(base_form_partition, stems)
            if partitiond_stems is None:
#            print(l.strip())
#            input()
                continue
            stems_dict = fill_stems_dict(partitiond_stems)
        except Exception as e:
            print(lineno(), l.strip(), '\n', type(e), e)
#        if input() == 'r': raise e
            continue

        try:
            partitions = render_template(template_name, stems_dict)
        except (KeyError, TemplateException) as e:
            print(lineno(), l.strip(), '\n', type(e), e)
#        if type(e) == TemplateException and input() == 'r': raise e
            continue
        if partitions is not None:
            for partition in partitions:
                check_partition(partition)
                print(partition, file=output_file)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extracts word form partitions from ruwiktionary dump')
    parser.add_argument('-f', '--filename', default='ruwiktionary.xml', help='wiktionary dump file')
    parser.add_argument('-t', '--tables-dir', default='tables', help='directory with rendered template tables')
    parser.add_argument('-d', '--data-dir', default='../data/morfology', help='directory with known word parts')
    parser.add_argument('-O', dest='output_file', default='annotated-partitions.txt', help='file to write partitions to (if - is given, writes to standart output)')
    args = parser.parse_args()

    load_sets(args.data_dir)

    if not os.exists(args.table_dir):
        import extract_tables
        extract_tables.extract_and_render(filename=args.filename, dest_dir=args.tables_dir)
    load_partition_table_templates(args.tables_dir)

    of = sys.stdout
    if args.output_file != '-':
        of = open(args.output_file, 'w')

    extract_annotated_partitions(of, filename=args.filename)

    if args.output_file != '-':
        of.close()
