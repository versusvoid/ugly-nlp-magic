#!/usr/bin/env python

from partition import partition, select_the_one_partition

while True:
    w = input("Cлово:")
    w = w.strip().replace('ь', '').replace('ъ', '')
    partitions = partition(w)
    the_partition = select_the_one_partition(partitions)
    print('and the one is:', the_partition)
