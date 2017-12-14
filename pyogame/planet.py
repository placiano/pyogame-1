import logging
from pyogame.tools import Resources
from pyogame.fleet import Fleet
from pyogame.constructions import Constructions
from pyogame.tools.common import coords_to_key
from pyogame.abstract.planner import PlannerMixin

logger = logging.getLogger(__name__)


class Planet(PlannerMixin):

    def __init__(self, name, coords, position, **kwargs):
        self.name = name
        self.coords = coords
        self.position = position
        self.idle = kwargs.get('idle', False)
        self.capital = kwargs.get('capital', False)
        self.waiting_for = kwargs.get('waiting_for', {})

        self.fleet = kwargs.get('fleet', Fleet())
        self.resources = kwargs.get('resources', Resources())
        self.constructs = kwargs.get('constructs', Constructions())
        self.plans = kwargs.get('plans', Constructions())
        PlannerMixin.__init__(self, 'constructs', 'plans')

    def get_curr(self, obj, bump_level=False):
        curr = self.constructs.cond(
                name=obj if isinstance(obj, str) else obj.name).first
        return curr.copy(curr.level) if bump_level else curr

    @property
    def key(self):
        return coords_to_key(self.coords)

    @property
    def is_fleet_empty(self):
        return not bool(self.fleet)

    @property
    def is_idle(self):
        return self.idle and not self.waiting_for

    @property
    def is_waiting(self):
        return bool(self.waiting_for)

    @property
    def is_metal_tank_full(self):
        return self.resources.metal >= self.get_curr('metal_tank').capacity

    @property
    def is_crystal_tank_full(self):
        return self.resources.crystal >= self.get_curr('crystal_tank').capacity

    @property
    def is_deuterium_tank_full(self):
        current_deut_cap = self.get_curr('deuterium_tank').capacity
        return self.resources.deuterium >= current_deut_cap

    def time_to_construct(self, cost):
        return ((float(cost.metal) + cost.crystal)
                / (2500. * (float(self.get_curr('robot_factory').level) + 1.)
                * pow(2., float(self.get_curr('nanite_factory').level))))

    def requirements_for(self, building):
        building_types = tuple(self.constructs.registry.values())
        unmatched_req = False
        for req in building.requirements or []:
            if (isinstance(req, building_types)
                    and req.level > self.get_curr(req).level):
                unmatched_req = True
                yield from self.requirements_for(req)
        if unmatched_req:
            return
        if building.level > self.get_curr(building).level + 1:
            yield from self.requirements_for(
                    building.__class__(building.level - 1))
            return
        yield building

    @property
    def to_construct(self, filter_meth=None):
        # Handling construction list
        metal_mine = self.get_curr('metal_mine')
        metal_tank = self.get_curr('metal_tank')
        crystal_tank = self.get_curr('crystal_tank')
        deut_tank = self.get_curr('deuterium_tank')

        to_construct = metal_mine
        if self.get_curr('deuterium_synthetizer').level < metal_mine.level - 7:
            to_construct = self.get_curr('deuterium_synthetizer')
        if self.get_curr('crystal_mine').level < metal_mine.level - 3:
            to_construct = self.get_curr('crystal_mine')
        # more or less 5%
        if to_construct.cost.energy * .95 > self.resources.energy:
            to_construct = self.get_curr('solar_plant')
        if self.capital:
            if metal_tank.capacity < to_construct.cost.metal \
                    or self.is_metal_tank_full:
                to_construct = metal_tank
            elif crystal_tank.capacity < to_construct.cost.crystal \
                    or self.is_crystal_tank_full:
                to_construct = crystal_tank
            elif deut_tank.capacity < to_construct.cost.deuterium \
                    or self.is_deuterium_tank_full:
                to_construct = deut_tank
        else:
            def should_build_tank(res_type, ratio):
                mine = self.get_curr('%s_mine' % res_type)
                tank = self.get_curr('%s_tank' % res_type)
                return float(mine.level) / (1 + tank.level) > ratio
            if should_build_tank('metal', 7):
                to_construct = self.get_curr('metal_tank')
            elif should_build_tank('crystal', 9):
                to_construct = self.get_curr('crystal_tank')
        yield from self.requirements_for(
                to_construct.copy(level=to_construct.level + 1))

    @classmethod
    def load(cls, **kwargs):
        for key, attr_cls in (('fleet', Fleet),
                              ('resources', Resources),
                              ('constructs', Constructions),
                              ('plans', Constructions)):
            kwargs[key] = attr_cls.load(**kwargs.get(key, {'data': {}}))
        return cls(**kwargs)

    def dump(self):
        return {'name': self.name,
                'coords': self.coords,
                'idle': self.idle,
                'position': self.position,
                'waiting_for': self.waiting_for,
                'capital': self.capital,
                'resources': self.resources.dump(),
                'fleet': {'data': self.fleet.dump()},
                'constructs': {'data': self.constructs.dump()},
                'plans': {'data': self.plans.dump()}}

    def __repr__(self):
        return r"<Planet(%r, %r, %r)>" % (
                self.name, self.coords, self.position)

    def __str__(self):
        return '%s %r' % (self.name, self.coords)

    def __eq__(self, other):
        if isinstance(other, Planet) and other.coords == self.coords:
            return True
        return False
