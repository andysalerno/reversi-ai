K = 0
V = 1


class CacheDict:

    def __init__(self):
        self.c_list = []
        self.flip = True

    def update(self, k, v):
        if len(self.c_list) < 2:
            self.c_list.append((k, v))
        else:
            if self.flip:
                self.c_list[0] = (k, v)
            else:
                self.c_list[1] = (k, v)
            self.flip = not self.flip

    def get(self, k):
        size = len(self.c_list)
        if size >= 1 and self.c_list[0][K] == k:
            return self.c_list[0][V]
        elif size >= 2 and self.c_list[1][K] == k:
            return self.c_list[1][V]
        else:
            return None
