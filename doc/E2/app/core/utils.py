from typing import Tuple

class UnitsConverter:
    def __init__(self, km_to_px: float = 10.0):
        self.km_to_px = km_to_px

    def world_to_screen(self, x_km: float, y_km: float) -> Tuple[int, int]:
        sx = int(round(x_km * self.km_to_px))
        sy = int(round(-y_km * self.km_to_px))
        return sx, sy

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        x_km = sx / self.km_to_px
        y_km = -sy / self.km_to_px
        return x_km, y_km

def frange(start, stop, step):
    while start < stop:
        yield round(start, 6)
        start += step