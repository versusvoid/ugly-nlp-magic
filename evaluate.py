#!/usr/bin/env python

import partition as P
import sys
import operator
class pos(object):
    def __init__(self):
        self.offset = 0
        self.index = 0

    def __repr__(self):
        return "({}, {})".format(self.offset, self.index)

def record(gold, partition, counts):
    gold_pos = pos()
    partition_pos = pos()
    def gold_move():
        gold_pos.offset += len(gold[gold_pos.index][1])
        gold_pos.index += 1
    def partition_move():
        partition_pos.offset += len(partition[partition_pos.index][1])
        partition_pos.index += 1

    wasWrong = [False]
    def wrong_type():
        counts['wrongType'] += 1
        wasWrong[0] = True
    def wrong_part():
        counts['wrongPart'] += 1
        wasWrong[0] = True
    def not_found():
        counts['notFound'] += 1
        wasWrong[0] = True

    while gold_pos.index < len(gold) or partition_pos.index < len(partition):
        if gold_pos.offset == partition_pos.offset:
            if gold_pos.index == len(gold):
#                print('lol1')
                if partition_pos.index != len(partition) - 1: raise Exception(gold_pos, partition_pos, gold, partition)
                wrong_part()
                partition_move()
            elif partition_pos.index == len(partition):
#                print('lol2')
                if gold_pos.index != len(gold) - 1: raise Exception(gold_pos, partition_pos, gold, partition)
                not_found()
                gold_move()
            elif gold[gold_pos.index] == partition[partition_pos.index]:
                counts['right'] += 1
                gold_move()
                partition_move()
            elif gold[gold_pos.index][1] == partition[partition_pos.index][1]:
#                print(gold_pos, partition_pos, 'wrong type')
                gold_move()
                partition_move()
                wrong_type()
            elif len(gold[gold_pos.index][1]) < len(partition[partition_pos.index][1]):
#                print(gold_pos, partition_pos, 'not found')
                gold_move()
                not_found()
            else:
#                print(gold_pos, partition_pos, 'wrong part')
                partition_move()
                wrong_part()

        elif gold_pos.offset < partition_pos.offset:
#            print(gold_pos, partition_pos, 'not found 2')
            gold_move()
            not_found()
        else:
#            print(gold_pos, partition_pos, 'wrong part 2')
            partition_move()
            wrong_part()
            
    if wasWrong[0]: counts['perWordWrong'] += 1
    else: counts['perWordRight'] += 1

counts = {
    'perWordRight': 0,
    'perWordWrong': 0,

    'right': 0,
    'wrongType': 0,
    'wrongPart': 0,
    'notFound': 0,
}
f = open(sys.argv[1], 'r')
count = 0
for l in f:
    if count % 10 == 0:
        print(count)
    l = l.strip()
    if l == '': continue
    parts = l.split()
    for i in range(len(parts)):
        parts[i] = tuple(parts[i].split('_'))
    parts = list(filter(lambda p: p[0] == 'оконч' or p[1] != '', parts))

    word = ''.join(map(operator.itemgetter(1), parts))
    partition = P.deterministic_partition(word)
    test_word = ''.join(map(operator.itemgetter(1), partition))
    if word != test_word:
        print('Partitioning of word', word, 'resulted in', test_word)
        exit()
#    print('Gold:', parts, '\nGenerated:', partition)
    record(parts, partition, counts)
    count += 1
f.close()

totalWords = counts['perWordWrong'] + counts['perWordRight']
print('Right per word:', counts['perWordRight'] / totalWords)

totalParts = counts['right'] + counts['wrongType'] + counts['notFound'] + counts['wrongPart']
print('Right:', counts['right'] / totalParts)
print('Wrong type:', counts['wrongType'] / totalParts)
print('Not found:', counts['notFound'] / totalParts)
print('Wrong part:', counts['wrongPart'] / totalParts)
