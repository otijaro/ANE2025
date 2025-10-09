# h_simulador/__init__.py
from .models import Entity, FMTransmitter, Aircraft, ControlTower, Scene
from .utils import UnitsConverter, frange

# Importar controladores explícitamente donde se necesiten:
# - Web API: from h_simulador.controller_core import SceneController
# - Desktop: from h_simulador.controller_qt import SceneController
