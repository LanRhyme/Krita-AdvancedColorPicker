from krita import *
from .vhsv_docker import VhsvDocker

try:
    dock_position = DockWidgetFactoryBase.DockPosition.DockRight
except AttributeError:
    dock_position = DockWidgetFactoryBase.DockRight

Krita.instance().addDockWidgetFactory(DockWidgetFactory("sai_vhsv_picker", dock_position, VhsvDocker))
