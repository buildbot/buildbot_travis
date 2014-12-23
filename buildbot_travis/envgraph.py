from collections import defaultdict


class EnvTree(defaultdict):

    def __init__(self):
        super(EnvTree, self).__init__(EnvTree)


class EnvMap:

    def __init__(self, labels):
        self.data = EnvTree()
        self.labels = labels

    def add(self, data):
        if not self.labels:
            return
        for l in self.labels:
            if l not in data:
                return
        d = self.data
        for l in self.labels[:-1]:
            d = d[data[l]]
        d[data[self.labels[-1]]] = data

    def iterall(self, data=None):
        if not data:
            data = self.data
        for k in sorted(data.keys()):
            v = data[k]
            if not isinstance(v, EnvTree):
                yield (k, )
            else:
                for c in self.iterall(v):
                    yield (k, ) + c

    def iter_keys(self):
        for data in self.iterall():
            env = dict(zip(self.labels, data))
            yield tuple((k, env[k]) for k in sorted(env.keys()))

    def iter_at_depth(self, depth):
        map = {}
        ordered = []
        total = 0
        for c in self.iterall():
            k = c[:depth]
            v = c[depth:]

            if k not in map:
                i = map[k] = dict(label=k[-1], children=[])
                ordered.append(i)

            if len(v) >= 1:
                map[k]['children'].append(v[0])

            total += 1

        for c in ordered:
            c['span'] = len(c['children']) or 1

        return ordered

    def iter_all_depths(self):
        for i, label in enumerate(self.labels, start=1):
            yield dict(label=label, children=self.iter_at_depth(i))
