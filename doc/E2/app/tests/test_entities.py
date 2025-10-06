import unittest
from core.entities import Entity, FMTransmitter, Aircraft

class TestEntities(unittest.TestCase):

    def test_entity_creation(self):
        e = Entity(id="E1", nombre="Entidad", x_km=10.0, y_km=20.0, h_km=1.0)
        self.assertEqual(e.id, "E1")
        self.assertEqual(e.nombre, "Entidad")
        self.assertEqual(e.x_km, 10.0)
        self.assertEqual(e.y_km, 20.0)
        self.assertEqual(e.h_km, 1.0)

    def test_entity_move(self):
        e = Entity(id="E2", nombre="Mover", x_km=5.0, y_km=5.0, h_km=0.5)
        e.move_to(15.0, 25.0)
        self.assertEqual(e.x_km, 15.0)
        self.assertEqual(e.y_km, 25.0)

    def test_fm_transmitter_creation(self):
        fm = FMTransmitter(id="FM1", nombre="FM Uno", x_km=30.0, y_km=15.0, h_km=0.1, potencia_W=10000.0, f_Hz=100e6)
        self.assertEqual(fm.potencia_W, 10000.0)
        self.assertEqual(fm.f_Hz, 100e6)

    def test_aircraft_creation(self):
        ac = Aircraft(id="AV1", nombre="Avión", x_km=70.0, y_km=30.0, h_km=2.0)
        self.assertEqual(ac.nombre, "Avión")
        self.assertEqual(ac.h_km, 2.0)

if __name__ == "__main__":
    unittest.main()