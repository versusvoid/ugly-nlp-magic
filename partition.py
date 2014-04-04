#!/usr/bin/env python

import operator
from pattern_position import *

def log(args):
    if type(args) == list:
        print()
        print(*args, sep='\n')
        print()
    else:
        print(args)

debug_enabled = False
def debug(args):
    if debug_enabled: log(args)

info_enabled = False
def info(args):
    if info_enabled: log(args)
        

class Part(object):

    def __init__(self, part, part_type, offset):
        self.type = part_type
        self.part = part
        self.offset = offset
        self.len = len(part)

    def to_tuple(self):
        return (self.type, self.part)

    def __str__(self):
        return "({}, {}, {})".format(self.type, self.part, self.offset)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.len

def find_next_possible_position(parts, offset):
    for i, p in enumerate(parts):
        if p.offset >= offset:
            return i

class PartialPartition(object):

    def __init__(self, partition=[], offset=0, parts_list_position=0, pattern_position=PatternPosition()):
        self.partition = partition
        self.offset = offset
        self.parts_list_position = parts_list_position
        self.pattern_position = pattern_position

    def is_suitable(self, part):
        if (part.offset == self.offset and part.type in self.pattern_position.possible_next()):
            return True

        if (part.offset > self.offset and 
            self.pattern_position.is_root_possible() and 
            part.type in self.pattern_position.possible_after_neares_root()):
            return True

        return False

    def moved(self, part, parts, word):
        new_pattern_position = self.pattern_position
        new_partition = self.partition
        if part.offset != self.offset:
            root_part = Part(word[self.offset:part.offset], 'корень', self.offset)
            new_partition = new_partition + [root_part]
            new_pattern_position = new_pattern_position.moved(root_part)

        new_offset = part.offset + part.len
        new_parts_list_position = find_next_possible_position(parts, new_offset)

        new_partition = new_partition + [part]
        new_pattern_position = new_pattern_position.moved(part)

        return PartialPartition(new_partition, new_offset, new_parts_list_position, new_pattern_position)

    def __str__(self):
        return "({}, {}, {}, {})".format(self.partition, self.offset, self.parts_list_position, self.pattern_position)

    def __repr__(self):
        return self.__str__()

parts = None
partition_types = None
max_part_len = None

def load_model():
    global parts, partition_types, max_part_len
    import pickle
    f = open('morfology.pick', 'rb')
    parts, partition_types, max_part_len = pickle.load(f)
    f.close()
load_model()


def extract_parts(s):
    result = []
    for i in range(0, len(s) + 1):
        for j in range(max(0, i - max_part_len), i):
            part_types = parts.get(s[j:i])
            if part_types != None:
                non_roots = filter(lambda part_type: part_type != 'корень', part_types)
                result.extend(map(lambda part_type: Part(s[j:i], part_type, j), non_roots))

    import operator
    return sorted(result, key=lambda p: p.offset)

def add_flexion(partition):
    if all(map(lambda p: p.type != 'оконч', partition)):
        partition.append(Part('', 'оконч', None))

    return partition

def partition(word):
    parts = extract_parts(word)
    partial_partitions = [PartialPartition()]
    partitions = [[Part(word, 'корень', 0)]]
    while len(partial_partitions) > 0:
        partial_partition = partial_partitions.pop()
        debug(partial_partition)
        if partial_partition.offset == len(word):
            partitions.append(add_flexion(partial_partition.partition))
            continue
        if not partial_partition.pattern_position.valid():
            continue

        for part in parts[partial_partition.parts_list_position:]:
            if partial_partition.is_suitable(part):
                partial_partitions.append(partial_partition.moved(part, parts, word))

    return partitions

empty_part_types_set = set()

def max_len(partition):
    return max(map(len, partition))

def min_len(partition):
    return min(map(len, partition))

base = 3
def select_the_one_partition(partitions):
    for i, partition in enumerate(partitions):
        score = 0.0
        parts_list = []
        for part in partition:
            if part.type == 'корень':
                types_porbs = parts.get(part.part)
                if types_porbs is not None and 'корень' in types_porbs:
                    score += base ** len(part.part)

                parts_list.append('корень_')
            else:
                score += base ** len(part.part)
                parts_list.append('{}_{}'.format(part.type, part.part))

        ''' мб *= ? '''
        score += partition_types.get(tuple(parts_list), partition_types['__unknown__'])
        score += sum(map(lambda p: 1 if p.type == 'оконч' and len(p.part) > 0 else 0, partition))

        partitions[i] = (score, partition)

    partitions = sorted(partitions, key=operator.itemgetter(0), reverse=True)
    debug(partitions)
    info(partitions[:10])
    selected_score, selected_partition = partitions[0]
    max_selected_len = max_len(selected_partition)
    min_selected_len = min_len(selected_partition)

    for score, partition in partitions[1:]:
        if score < selected_score:
            break

        partition_max_len = max_len(partition)
        partition_min_len = min_len(partition)
        if partition_max_len > max_selected_len or partition_min_len > min_selected_len:
            selected_partition = partition
            max_selected_len = partition_max_len
            min_selected_len = partition_min_len 

    return list(map(lambda p: p.to_tuple(), selected_partition))

def deterministic_partition(word): return select_the_one_partition(partition(word))
