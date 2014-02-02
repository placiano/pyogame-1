import logging

from pyogame.const import Resources
from pyogame.fleet import Fleet
from pyogame.constructions import MetalMine, CrystalMine, \
        DeuteriumSynthetizer, SolarPlant

logger = logging.getLogger(__name__)


class Planet(object):

    def __init__(self, name, coords, position):
        self.name = name
        self.coords = coords
        self.position = position
        self.flags = []

        self.fleet = Fleet()
        self.resources = Resources()

        self.metal_mine = MetalMine()
        self.crystal_mine = CrystalMine()
        self.deuterium_synthetize = DeuteriumSynthetizer()
        self.solar_plant = SolarPlant()

    def __repr__(self):
        return r"<%s %s>" % (self.name, self.coords)

    def __eq__(self, other):
        if isinstance(other, Planet) and other.coords == self.coords:
            return True
        return False

    def add_flag(self, flag):
        if not self.has_flag(flag):
            self.flags.append(flag)

    def del_flag(self, flag):
        if self.has_flag(flag):
            self.flags.remove(flag)

    def has_flag(self, flag):
        return flag in self.flags

    @property
    def is_idle(self):
        return 'idle' in self.flags

    @property
    def is_capital(self):
        return 'capital' in self.flags

    @property
    def to_construct(self):
        if self.deuterium_synthetize.level < self.metal_mine.level - 4:
            if self.deuterium_synthetize.cost.energy > self.resources.energy:
                return self.solar_plant
            return self.deuterium_synthetize
        if self.crystal_mine.level <= self.metal_mine.level - 2:
            if self.crystal_mine.cost.energy > self.resources.energy:
                return self.solar_plant
            return self.crystal_mine
        if self.metal_mine.cost.energy > self.resources.energy:
            return self.solar_plant
        return self.metal_mine
