cardinals = ["FI", "WA", "AI", "EA"]
metals = ["M0", "M1", "M2", "M3", "M4", "M5"]

elements = cardinals + metals + ["CH", "HG", "LI", "DE"]

possible_pairings = set(map(tuple, map(sorted, [
    (a, a) for a in cardinals
] + [
    (a, "CH") for a in cardinals
] + [
    (c, "HG") for c in metals[:-1]
] + [
    ("LI", "DE"), ("CH", "CH")
])))

n = [(-1,0),(0,1),(1,1),(1,0),(0,-1),(-1,-1)]

class Board:
    def __init__(self):
        self.tiles = {}

    def counts(self):
        counts = {i: 0 for i in elements}
        for v in self.tiles.values():
            counts[v] += 1
        return counts

    def is_full(self):
        return self.counts() == {
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
        }
    
    def is_free(self, position):
        e = self.tiles[position]
        if e in metals:
            if len(set(self.tiles.values()) & set(metals[:metals.index(e)])) > 0:
                return False
        
        i, j = position
        for k in range(6):
            if all((i + n[k-l][0], j + n[k-l][1]) not in self.tiles for l in range(3)):
                return True
        return False

    def pairings(self):
        l = []
        free = [(p,v) for p, v in self.tiles.items() if self.is_free(p)]
        for (pa, a) in free:
            for (pb, b) in free:
                if pb == pa:
                    break
                if (a, b) in possible_pairings or (b, a) in possible_pairings:
                    l.append((pa, pb))
        if (5,5) in self.tiles and self.is_free((5,5)):
            l.append(((5,5),))
        return l 
    

    def has_hope(self):
        counts = self.counts()
        odds = 0
        for c in cardinals:
            if counts[c] % 2 == 1:
                odds += 1
        if odds > counts["CH"]:
            return False
        
        return True


    def solve(self, steps=None):
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
                    del self.tiles[i]
                
                steps.append(p)
                yield from self.solve(steps)
                steps.pop()
                
                for i, u in zip(p, v):
                    self.tiles[i] = u