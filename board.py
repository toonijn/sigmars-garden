cardinals = ["FI", "WA", "AI", "EA"]
metals = ["M0", "M1", "M2", "M3", "M4", "M5"]

elements = cardinals + metals + ["CH", "HG", "LI", "DE", "QU"]

possible_pairings = set(map(tuple, map(sorted, [
    (a, a) for a in cardinals
] + [
    (a, "CH") for a in cardinals
] + [
    (c, "HG") for c in metals[:-1]
] + [
    ("LI", "DE"), ("CH", "CH")
])))

n = [(-1, 0), (0, 1), (1, 1), (1, 0), (0, -1), (-1, -1)]

full_sigmars_garden = {
    "FI": 8,
    "WA": 8,
    "EA": 8,
    "AI": 8,
    "CH": 4,
    "LI": 4,
    "DE": 4,
    "HG": 5,
    "M0": 1,
    "M1": 1,
    "M2": 1,
    "M3": 1,
    "M4": 1,
    "M5": 1,
    'QU': 0,
}

full_sigmars_garden2 = dict(full_sigmars_garden)
full_sigmars_garden2.update({
    'QU': 2,
    'LI': 3,
    'DE': 3
})


def neighbors(i, j):
    for di, dj in n:
        yield i + di, j + dj


class Board:
    def __init__(self):
        self.tiles = {}
        self.inverse_tiles = {e: set() for e in elements}
        self.free = {}
        self.inverse_free = {e: set() for e in elements}

    def __str__(self):
        return f"""Board({self.tiles},{self.inverse_tiles},{self.free},{self.inverse_free})"""

    def counts(self):
        return {
            e: len(s) for e, s in self.inverse_tiles.items()
        }

    def is_full(self, sigmars_garden2=False):
        sg = full_sigmars_garden2 if sigmars_garden2 else full_sigmars_garden
        return all(sg[e] == len(p) for e, p in self.inverse_tiles.items())

    def is_free(self, position):
        e = self.tiles[position]
        if e[0] == 'M':
            for i in range(int(e[1])):
                if len(self.inverse_tiles['M'+str(i)]) > 0:
                    return False

        i, j = position
        for k in range(6):
            if all((i + n[k-l][0], j + n[k-l][1]) not in self.tiles for l in range(3)):
                return True
        return False

    def pairings(self):
        l = []
        for (pa, a) in self.free.items():
            for (pb, b) in self.free.items():
                if pb == pa:
                    break
                if (a, b) in possible_pairings or (b, a) in possible_pairings:
                    l.append((pa, pb))

        for f5 in self.inverse_free["M5"]:
            l.append((f5,))

        if self.inverse_free["QU"] and all(map(self.inverse_free.get, cardinals)):
            for qu in self.inverse_free["QU"]:
                for fi in self.inverse_free["FI"]:
                    for wa in self.inverse_free["WA"]:
                        for ai in self.inverse_free["AI"]:
                            for ea in self.inverse_free["EA"]:
                                l.append((qu, fi, wa, ai, ea))
        return l

    def has_hope(self):
        counts = self.counts()
        qu = len(self.inverse_tiles['QU'])

        odds = 0
        for e in cardinals:
            c = counts[e]
            if c < qu:
                return False
            if (c - qu) % 2 == 1:
                odds += 1
        if odds > counts["CH"]:
            return False

        return True

    def _add_free(self, p, e):
        if p not in self.free:
            self.free[p] = e
            self.inverse_free[e].add(p)

    def _remove_free(self, p, e):
        if p in self.free:
            del self.free[p]
            self.inverse_free[e].remove(p)

    def update_free_around(self, ij):
        for p in neighbors(*ij):
            if p in self.tiles:
                if self.is_free(p):
                    self._add_free(p, self.tiles[p])
                else:
                    self._remove_free(p, self.tiles[p])

    def _update_free_metal(self):
        first = True
        for m in metals:
            if self.inverse_tiles[m]:
                p = next(iter(self.inverse_tiles[m]))
                if first:
                    if self.is_free(p):
                        self._add_free(p, m)
                    else:
                        self._remove_free(p, m)
                    first = False
                else:
                    self._remove_free(p, m)

    def remove_tile(self, p):
        e = self.tiles[p]
        del self.tiles[p]
        self.inverse_tiles[e].remove(p)
        self._remove_free(p, e)
        self.update_free_around(p)
        if e[0] == 'M':
            self._update_free_metal()

    def _unsafe_add_tile(self, p, e):
        self.tiles[p] = e
        self.inverse_tiles[e].add(p)
        if self.is_free(p):
            self._add_free(p, e)
        self.update_free_around(p)
        if e[0] == 'M':
            self._update_free_metal()

    def add_tile(self, p, e):
        assert e in elements, f"'{e}' is not an element"
        assert p not in self.tiles, f"'{p}' is not free"
        self._unsafe_add_tile(p, e)

    def solve(self, steps=None):
        # self.check_validity()
        if not self.has_hope():
            return
        if steps is None:
            steps = []
        if len(self.tiles) == 0:
            yield list(steps)
        else:
            for p in self.pairings():
                v = tuple(map(self.tiles.get, p))
                for i in p:
                    self.remove_tile(i)

                steps.append(p)
                yield from self.solve(steps)
                steps.pop()

                for i, u in zip(p, v):
                    self._unsafe_add_tile(i, u)

    def check_validity(self, simple=False):
        print("check  validity")
        for p in self.free:
            assert p in self.tiles, f"{p} is free, but it is not in tiles"
            assert self.is_free(p), f"{p} should be free in {self}"
        for p in self.tiles:
            if p not in self.free:
                assert not self.is_free(p), f"{p} is free, but not in free"

        if simple:
            return
        b = Board()
        for p, e in self.tiles.items():
            b.add_tile(p, e)
        b.check_validity(True)
        valid = (
            b.tiles == self.tiles
            and b.inverse_tiles == self.inverse_tiles
            and b.free == self.free
            and b.inverse_free == self.inverse_free
        )
        if not valid:
            print(self.free)
            print(b.free)
        assert valid, "Invalid board"
