#!/usr/bin/env python

parts = {}
partition_types = {}
max_len = 4

import sys
filename = 'partitions'
if len(sys.argv) > 1:
    filename = sys.argv[1]

α = 1.0

partitions_count = α

f = open(filename)
for l in f:
    partition_parts = l.strip().split()
    for i, part in enumerate(partition_parts):
        if '_' not in part:
            print(l, part)
            exit(1)
        type, value = part.split('_')
        value = value.replace('ь', '').replace('ъ', '')
        if value == '': continue
        part_types = parts.setdefault(value, set()).add(type)
        if type != 'корень': 
            max_len = max(len(value), max_len)
        else:
            partition_parts[i] = type + '_'

    partition_parts = tuple(partition_parts)
    partition_types[partition_parts] = partition_types.get(partition_parts, 0.0) + 1.0
    partitions_count += 1
f.close()

partitions_count += (len(partition_types) + 1)*α
for partition, count in partition_types.items():
    partition_types[partition] = (count + α) / partitions_count
partition_types['__unknown__'] = α / partitions_count


import pickle
f = open('morfology.pick', 'wb')
pickle.dump((parts, partition_types, max_len), f)
f.close()

if '' in parts:
    print('aaaaaaaaaaaaa')
    exit(100500)
