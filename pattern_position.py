#!/usr/bin/env python

# префд{0,5} прист{0,3} корень суфф{0,5} (соед прис{0,3} корень суфф{0,3}){0,2} оконч? частица?

class PatternPosition(object):
    PREFD = 1
    PREF = 2
    ROOT = 3
    SUFF = 4
    GROUP_START = 5
    GROUP_PREF = 6
    GROUP_ROOT = 7
    GROUP_SUFF = 8
    INFLECTION = 9
    PARTICLE = 10

    expected_parts = {
        PREFD : "префд",
        PREF : "прист",
        ROOT : "корень",
        SUFF : "суфф",
        GROUP_START : "соед",
        GROUP_PREF : "прист",
        GROUP_ROOT : "корень",
        GROUP_SUFF : "суфф",
        INFLECTION : "оконч",
        PARTICLE : "частица"
    }

    group_positions = set([GROUP_START, GROUP_PREF, GROUP_ROOT, GROUP_SUFF])


    max_counts = {
        PREFD : 5,
        PREF  : 3,
        ROOT  : None,
        SUFF  : 5,

        GROUP_START : None,
        GROUP_PREF  : 3,
        GROUP_ROOT  : None,
        GROUP_SUFF  : 4,

        INFLECTION  : 1,
        PARTICLE    : 1
    }


    _possible_next = {}

    _possible_next[PREFD] = ['префд', "прист"]
    _possible_next[PREF] = ['прист']
    _possible_next[ROOT] = []
    _possible_next[SUFF] = ["суфф", "оконч", "соед"]

    _possible_next[GROUP_START] = ["соед", "оконч"]
    _possible_next[GROUP_PREF] = ['прист']
    _possible_next[GROUP_ROOT] = []
    _possible_next[GROUP_SUFF] = ['суфф', 'оконч', 'соед']

    _possible_next[INFLECTION] = ['оконч']
    _possible_next[PARTICLE] = ['частица']


    root_possible = [PREFD, PREF, ROOT, GROUP_PREF, GROUP_ROOT]


    def __init__(self, position=PREFD, count=0, groups_count=0):
        self.position = position
        self.count = count
        self.groups_count = groups_count

    def possible_next(self):
        possible = PatternPosition._possible_next[self.position]
        if self.groups_count == 2:
            return list(filter(lambda p: p != "соед", possible))
        else:
            return possible

    def is_root_possible(self):
        return self.position in PatternPosition.root_possible

    def possible_after_neares_root(self):
        assert self.is_root_possible()
        """ Они совпадают, поэтому можно упростить
        if self.position in PatternPosition.group_positions:
        else:
        """
        return list(filter(lambda p: self.groups_count < 2 or p != "соед", PatternPosition._possible_next[PatternPosition.SUFF]))

    def valid(self):
        return self.position >= PatternPosition.PREFD and self.position <= PatternPosition.PARTICLE

    def moved(self, part):
        if (part.type not in self.possible_next()) and (part.type != "корень" or not self.is_root_possible()):
            raise ValueError(part.type, self.position)
        assert (part.type != PatternPosition.expected_parts[self.position]
             or PatternPosition.max_counts[self.position] is None 
             or self.count < PatternPosition.max_counts[self.position])

        if part.type == "корень":
            new_position = None
            if self.position in PatternPosition.group_positions:
                new_position = PatternPosition.GROUP_SUFF
            else:
                new_position = PatternPosition.SUFF
            return PatternPosition(new_position, 0, self.groups_count)

        if part.type == "соед":
            assert self.groups_count < 2
            return PatternPosition(PatternPosition.GROUP_PREF, 0, self.groups_count + 1)

        if part.type == PatternPosition.expected_parts[self.position] and self.count + 1 < PatternPosition.max_counts[self.position]:
            return PatternPosition(self.position, self.count + 1, self.groups_count)
        
        if part.type == PatternPosition.expected_parts[self.position]:
            if self.position == PatternPosition.GROUP_SUFF and self.groups_count < 2:
                return PatternPosition(PatternPosition.GROUP_START, 0, self.groups_count)
            else:
                return PatternPosition(self.position + 1, 0, self.groups_count)

        if part.type == "прист":
            return PatternPosition(PatternPosition.PREF, 1, self.groups_count)

        if part.type == "оконч":
            return PatternPosition(PatternPosition.PARTICLE, 0, self.groups_count)

        if part.type == "частица":
            return PatternPosition(None, 0, self.groups_count)

        raise ValueError("Bad state", self, part)


    def __str__(self):
        return "({}, {}, {})".format(self.position, self.count, self.groups_count)

    def __repr__(self):
        return self.__str__()
