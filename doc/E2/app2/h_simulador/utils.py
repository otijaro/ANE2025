from __future__ import annotations

def frange(start: float, stop: float, step: float):
    v = start
    if step == 0:
        return
    if step > 0:
        while v <= stop + 1e-9:
            yield round(v, 6)
            v += step
    else:
        while v >= stop - 1e-9:
            yield round(v, 6)
            v += step

class UnitsConverter:
    def __init__(self, km_to_px: float = 10.0):
        self.km_to_px = km_to_px
