import vs


class Criteria(object):
    def __init__(self):
        self.__criteria = []

    def __get(self):
        return ''.join(self.__criteria)

    def has_record(self, record_name: str):
        self.__criteria.append('(R in [\'' + record_name + '\'])')
        return self

    def for_each(self, do: callable):
        vs.ForEachObject(do, self.__get())