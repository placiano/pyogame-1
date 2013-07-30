#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import logging
from selenium import selenium

logger = logging.getLogger(__name__)
from pyogame import planets, ships

DEFAULT_WAIT_TIME = 40000

class Ogame(selenium):

    def __init__(self, mother=None, planets=[]):
        selenium.__init__(self,
                "localhost", 4444, "*chrome", "http://ogame.fr/")
        self.current_position = None
        self.current_page = None
        self.mother, self.planets = mother, planets
        self.start()

    def __del__(self):
        self.stop()

    def login(self, login, passwd):
        logger.info('Logging in with identity %r' % login)
        self.open("http://ogame.fr/")
        self.click("id=loginBtn")
        self.select("id=serverLogin", "label=Pegasus")
        self.type("id=usernameLogin", login)
        self.type("id=passwordLogin", passwd)
        self.click("id=loginSubmit")
        self.wait_for_page_to_load(DEFAULT_WAIT_TIME)
        if not self.planets:
            self.get_planets()

    def __split_text(self, xpath, split_on='\n'):
        return self.get_text(xpath).split(split_on)

    def update_planet_resources(self, planet):
        logger.info('updating ressources on planet %r' % planet)
        planet.resources = {}
        try:
            for res_type in ['metal_box', 'crystal_box',
                    'deuterium_box', 'energy_box']:
                res = self.__split_text("//li[@id='%s']" % res_type, '.')
                planet.resources[res_type[:-4]] = int(''.join(res))
        except Exception, error:
            logger.error("ERROR: Couldn't update ressources")
            logger.error(error)

    def update_planet_buildings(self, planet):
        logger.info('updating buildings states for %r' % planet)
        planet.constructions = constructions = {}
        try:
            for ctype in ('building', 'storage'):
                for const in self.__split_text("//ul[@id='%s']" % ctype):
                    if not const.strip():
                        continue
                    constructions[ctype] = {}
                    name, level = const.strip().rsplit(' ', 1)
                    constructions[ctype][name] = int(''.join(level.split('.')))
        except Exception, error:
            logger.error("ERROR: Couldn't update building states")
            logger.error(error)

    def update_planet_fleet(self, planet):
        logger.info('updating fleet states on %r' % planet)
        planet.fleet = ships.Fleet()
        try:
            for fleet_type in ('military', 'civil'):
                for fleet in self.__split_text("//ul[@id='%s']" % fleet_type):
                    planet.fleet.add(*fleet.strip().rsplit(' ', 1))
        except Exception, error:
            logger.error("ERROR: Couldn't update fleet states")
            logger.error(error)

    def get_planets(self, full=False):
        logger.info('Getting list of colonized planets')
        self.planets, xpath = {}, "//div[@id='planetList']"
        for position, planet in enumerate(self.__split_text(xpath)):
            name, coords = re.split('\[?\]?', planet.split('\n')[0])[:2]
            planet = planets.Planet(name.strip(), coords, position + 1)
            self.planets[planet.position] = planet
            logger.debug('Got planet %r' % planet)

            if not full:
                continue
            self.go_to(planet, 'Ressources')
            self.go_to(planet, 'Flotte')

    def go_to(self, planet, page):
        logger.info('Going to page %r on %r' % (page, planet))
        if self.current_position != planet.position:
            self.click("//div[@id='planetList']/div[%d]/a" % (planet.position))
            self.current_position = planet.position
            self.wait_for_page_to_load(DEFAULT_WAIT_TIME)

        if self.current_page != page:
            self.click("link=%s" % page)
            self.current_page = page
            self.wait_for_page_to_load(DEFAULT_WAIT_TIME)

        self.update_planet_resources(planet)
        if page == 'Ressources':
            self.update_planet_resources(planet)
        elif page == 'Flotte':
            self.update_planet_fleet(planet)

    def send_ressources(self, src, dst, content={}):
        #metal = content.get('metal', 'all')
        #cristal = content.get('cristal', 'all')
        #deut = content.get('deut', 'all')
        logger.info('sending all possible ressources from %r to %r'
                % (src, dst))

        self.go_to(src, 'Flotte')
        self.click("//ul[@id='civil']/li[2]/div/a")
        self.click("css=#continue > span")
        self.wait_for_page_to_load(DEFAULT_WAIT_TIME)

        self.type("id=galaxy", dst[0])
        self.type("id=system", dst[1])
        self.type("id=position", dst[2])
        self.click("id=pbutton")
        self.click("css=#continue > span")
        self.wait_for_page_to_load(DEFAULT_WAIT_TIME)

        self.click("css=#missionButton3")
        #if metal == 'all' and cristal == 'all' and deut == 'all':
        self.click("css=#allresources > img")
        self.click("css=#start > span")
        self.wait_for_page_to_load(DEFAULT_WAIT_TIME)
        self.update_planet_fleet(src)

    def rapatriate(self, dst=None):
        if not self.planets:
            self.get_planets()
        dst = dst if dst is not None else self.mother
        logger.info('launching rapatriation to %r' % dst)
        for src in self.planets.values():
            if dst != src.coords:
                try:
                    self.send_ressources(src, dst)
                except Exception:
                    pass

# vim: set et sts=4 sw=4 tw=120: