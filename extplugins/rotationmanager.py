#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 www.xlr8or.com
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Changelog:
# 1.0.0 - 1.1.0: Added MapDelay and smart/random creation of rotations
# 1.0.0 - 1.1.1: Added fallbackrotation and some errorchecking
# 1.1.1 - 1.1.2: Added some more debugging.
# 1.1.2 - 1.1.3: Introduced copy.deepcopy()
# 1.1.3 - 1.1.4: Added CoD1/CoD2 restartcompatibility
#                Fixed a bug where B3 was unresponsive while in restart-countdown
# 1.1.4 - 1.1.5: Few Bugfixes.
# 1.1.5 - 1.1.6: Stripped space at end of rotation.
# 1.1.6 - 1.2.0: Added hysteresis, added some comments, added caching of roundstartrotation
# 1.2.0 - 1.2.1: Fixed a bug where the cached rotation would remain 'None'
# 1.2.1 - 1.2.2: Added another safety .strip() when storing _roundstart_mapRotationCurrent
# 1.2.2 - 1.2.3: Introduced version 11 for UO; generate rotations with all gametypes
# 1.2.3 - 1.2.4: Added check for limitation of the maximum stringlength (capped at 980)
# 1.3.0        : Added support for CoD4
# 1.3.1        : fixed a bug where on slower boxes the rotation wasn't stored on time
# 1.3.2        : only add maps that have not been added in the last 4 passes, no more double maps
# 1.3.3        : ...
# 1.3.4        : bugfix in maphistory
# 1.3.5        : Added gametypehistory, changed maphistory: both are now configurable for each
#                rotation size individually - Just a baka
# 1.3.6        : Added cod7 support, beautified code - Just a baka
# 1.3.7        : Reworked adjustrotation, fixed bugs that were causing unnecessary
#                setrotation() calls - Just a baka
# 1.3.8        : Implemented proper cod6 support, optimized first saveroundstartrotation - Just a baka
# 1.3.9        : Added map, maps and nextmap commands for ranked cod7 - 82ndab-Bravo17
# 1.3.9a       : Added Names translation for COD7 maps - 82ndab-Bravo17
# 1.3.9b       : Added DLC2 Maps

__version__ = '1.3.9'
__author__  = 'xlr8or, Just a baka, 82ndab-Bravo17'

import copy
import threading
import time
import random
import b3
import b3.events
import string

#--------------------------------------------------------------------------------------------------
class RotationmanagerPlugin(b3.plugin.Plugin):
    _rotation_small = {}
    _rotation_medium = {}
    _rotation_large = {}
    _currentrotation = 0
    _immediate = 0
    _switchcount1 = 0
    _switchcount2 = 0
    _hysteresis = 0
    _playercount = -1
    _oldplayercount = None
    _mapDelay = 0
    _version = 0
    _restartCmd = ''
    _countDown = 0
    _donotadjustnow = False
    _randomizerotation = 0
    _roundstart_mapRotation = None
    _roundstart_mapRotationCurrent = ''
    _roundstart_currentrotation = 0
    _fallbackrotation = ''
    _needfallbackrotation = False
    _initialrecount = False
    _rotation_size = 1                    # 1 - small, 2 - medium, 3 - large
    _recentmaps = []                      # The Maphistory
    _recentgts = []                       # The Gametype history
    _hmm = [0,0,0]                        # HowManyMaps to keep as a maphistory
    _hmgt = [0,0,0]                       # HowManyGameTypes to keep as a gametype history
    _cod7MapRotation = []
    _cod7MapRotationFixed = []
    _nextmap7 = []
    _outofrotation = False

    _cod7Maps = ['mp_array','mp_cairo','mp_cosmodrome','mp_cracked','mp_crisis','mp_duga','mp_firingrange','mp_hanoi',
                 'mp_havoc','mp_nuked','mp_mountain','mp_radiation','mp_russianbase','mp_villa','mp_berlinwall2',
                 'mp_kowloon','mp_stadium','mp_discovery','mp_gridlock','mp_hotel','mp_outskirts','mp_zoo']
    _cod7Mapeasynames = ['Array','Havanna','Launch','Cracked','Crisis','Grid','Firing Range','Hanoi',
                         'Jungle','Nuketown','Summit','Radiation','WMD','Villa','Berlin Wall',
                         'Kowloon','Stadium','Discovery','Gridlock','Hotel','Outskirts','Zoo']
    _cod7Mapeasynameslower = ['array','havanna','launch','cracked','crisis','grid','firing range','hanoi',
                              'jungle','nuketown','summit','radiation','wmd','villa','berlin wall',
                              'kowloon','stadium','discovery','gridlock','hotel','outskirts','zoo']
    _cod7Playlists = {18: {
                            0: {'tdm':1, 'dm':2, 'ctf':3, 'sd':4, 'koth':5, 'dom':6, 'sab':7, 'dem':8},         # softcore
                            1: {'tdm':9, 'dm':10, 'ctf':11, 'sd':12, 'koth':13, 'dom':14, 'sab':15, 'dem':16},  # hardcore
                            2: {'tdm':17, 'dm':18, 'ctf':19, 'sd':20, 'koth':21, 'dom':22, 'sab':23, 'dem':24}, # barebones
                          },
                      12: {
                            0: {'tdm':32, 'dm':33, 'ctf':34, 'sd':35, 'koth':36, 'dom':37, 'sab':38, 'dem':39}, # softcore
                            1: {'tdm':41, 'dm':42, 'ctf':43, 'sd':44, 'koth':45, 'dom':46, 'sab':47, 'dem':48}, # hardcore
                            2: {'tdm':50, 'dm':51, 'ctf':52, 'sd':53, 'koth':54, 'dom':55, 'sab':56},           # barebones (yes, no dem)
                          }
                     }
    _slot_num = 18
    _game_mode = 0
    _cod7Gametypes = ['tdm', 'dm', 'ctf', 'sd', 'hq', 'koth', 'dom', 'sab', 'dem']


    def onStartup(self):
        """\
        Initialize plugin settings
        """
        

        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False

        # register our commands
        if 'commands' in self.config.sections() and self._version == 7:
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp

                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)
        # Register our events
        self.verbose('Registering events')
        self.registerEvent(b3.events.EVT_CLIENT_CONNECT)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_GAME_EXIT)

        # don't adjust the rotation just yet
        self._donotadjustnow = True
        
        if self._version != 7:
            self._needfallbackrotation = True
            self._initialrecount = True
            # we'll store the initial rotation
            self.retrievefallback()

        # wait half a minute after pluginstart to do an initial playercount
        t1 = threading.Timer(30, self.recountplayers)
        t1.start()

        self.debug('Started')


    def onLoadConfig(self):
        # load our settings
        self.verbose('Loading config')
        self._switchcount1 = self.config.getint('settings', 'switchcount1')
        self._switchcount2 = self.config.getint('settings', 'switchcount2')
        self._hysteresis = self.config.getint('settings', 'hysteresis')
        self._immediate = self.config.getboolean('settings', 'immediate')
        self._mapDelay = self.config.getint('settings', 'mapdelay')
        self._version = self.config.getint('settings', 'version')
        self._randomizerotation = self.config.getboolean('settings', 'randomizerotation')

        self._hmm[0] = abs(self.config.getint('histories', 'maphistory_small'))
        self._hmm[1] = abs(self.config.getint('histories', 'maphistory_medium'))
        self._hmm[2] = abs(self.config.getint('histories', 'maphistory_large'))
        self.debug('MapHistory is set to: %s' % self._hmm)

        self._hmgt[0] = abs(self.config.getint('histories', 'gthistory_small'))
        self._hmgt[1] = abs(self.config.getint('histories', 'gthistory_medium'))
        self._hmgt[2] = abs(self.config.getint('histories', 'gthistory_large'))
        self.debug('GTHistory is set to: %s' % self._hmgt)

        if self._version == 7:
            self._slot_num = self.config.getint('cod7', 'slot_num')
            if self._slot_num not in (12, 18):
                self.error ('Incorrect number of slots (%d), assuming you meant 18.' % self._slot_num)
                self._slot_num = 18

            self._game_mode = self.config.getint('cod7', 'game_mode')
            if self._game_mode not in (0, 1, 2):
                self.error ('Incorrect game mode (%d), assuming you meant softcore.' % self._game_mode)
                self._game_mode = 0
        
        for gametype in self.config.options('rotation_small'):
            maps = self.config.get('rotation_small', gametype)
            maps = maps.split(' ')
            self._rotation_small[gametype] = maps
            self.debug('Small %s: %s' %(gametype, maps))

        for gametype in self.config.options('rotation_medium'):
            maps = self.config.get('rotation_medium', gametype)
            maps = maps.split(' ')
            self._rotation_medium[gametype] = maps
            self.debug('Medium %s: %s' % (gametype, maps))

        for gametype in self.config.options('rotation_large'):
            maps = self.config.get('rotation_large', gametype)
            maps = maps.split(' ')
            self._rotation_large[gametype] = maps
            self.debug('Large %s: %s' % (gametype, maps))

        if self._version in (1, 11):            # 1: CoD1 or 11: CoD UO
            self._restartCmd = 'map_restart'
        elif self._version in (2, 4, 5, 6):     # CoD2, CoD4, CoD5 or CoD6
            self._restartCmd = 'fast_restart'
        else:
            self._mapDelay = 0

    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
    
        return None

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == b3.events.EVT_CLIENT_CONNECT:
            self._playercount += 1
            self.debug('PlayerCount: %s' % self._playercount)
            # we're going up, pass a positive 1 to the adjustmentfunction
            self.adjustrotation(+1)
        elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
            self._playercount -= 1
            self.debug('PlayerCount: %s' % self._playercount)        
            # we're going down, pass a negative 1 to the adjustmentfunction
            self.adjustrotation(-1)
        elif event.type == b3.events.EVT_GAME_EXIT:
            self._donotadjustnow = True
            # wait 2 mins and cache the current rotation cvars
            if self._version != 7:
                t3 = threading.Timer(120, self.saveroundstartrotation)
                t3.start()
            # wait 3 mins and do a recount
            t4 = threading.Timer(180, self.recountplayers)
            t4.start()
            # should we fast_restart?
            if self._mapDelay != 0 and self._version != 7:
                t5 = threading.Thread(target=self.fastrestart)
                t5.start()
            # cod7 map change support
            if self._version == 7:
                # wait 2 minutes and set the next map
                self.debug ('Map change detected, Will push the new map to the server after 2 minutes.')
                self.cod7getnextmap()
                t6 = threading.Timer(120, self.cod7maprotate)
                t6.start()


    def adjustrotation(self, delta):
        if self._donotadjustnow:
            return None

        new_rotation = 0 # size: from 1 (small) to 3 (large)

        if delta == +1:
            if self._playercount > (self._switchcount2 + self._hysteresis):
                new_rotation = 3
            elif self._playercount > (self._switchcount1 + self._hysteresis):
                new_rotation = 2
            else:
                new_rotation = 1

        elif delta == -1:
            if self._playercount < (self._switchcount1 - self._hysteresis):
                new_rotation = 1
            elif self._playercount < (self._switchcount2 - self._hysteresis):
                new_rotation = 2
            else:
                new_rotation = 3

        elif delta == 0:
            if self._playercount < self._switchcount1:
                new_rotation = 1
            elif self._playercount < self._switchcount2:
                new_rotation = 2
            else:
                new_rotation = 3

        if new_rotation != 0 and (new_rotation != self._rotation_size or\
                                 (self._version == 7 and len(self._cod7MapRotation) == 0) or\
                                  self._initialrecount):
            self.setrotation (new_rotation)
        elif new_rotation == 0:
            self.debug ('Invalid delta has been passed to adjustrotation, aborting.')
        else:
            self.debug ('Rotation size has not changed, will not update rotation.')

        return None


    def setrotation(self, newrotation):
        if newrotation == self._currentrotation and self._version != 7:
            return None

        # restore the rotation if the new one is the same as the one at round/map start
        if newrotation == self._roundstart_currentrotation and self._roundstart_mapRotation is not None and self._version != 7:
            self.debug('Restoring Cached Roundstart Rotations')
            if self._version != 6:
                if self._roundstart_mapRotation != '':
                    self.console.setCvar('sv_mapRotation', self._roundstart_mapRotation)
                if self._roundstart_mapRotationCurrent != '':
                    self.console.setCvar('sv_mapRotationCurrent', self._roundstart_mapRotationCurrent)
            else:
                if self._roundstart_mapRotation != '':
                    self.console.write('sv_mapRotation %s' % self._roundstart_mapRotation)
                if self._roundstart_mapRotationCurrent != '':
                    self.console.write('sv_mapRotationCurrent %s' % self._roundstart_mapRotationCurrent)

            self._currentrotation = newrotation
            return None

        if newrotation == 1:
            rotname = "small"
            rotation = self._rotation_small
        elif newrotation == 2:
            rotname = "medium"
            rotation = self._rotation_medium
        elif newrotation == 3:
            rotname = "large"
            rotation = self._rotation_large
        else:
            self.error('Error: Invalid newrotation passed to setrotation.')
            return None

        self._rotation_size = newrotation

        self.debug('Adjusting to %s mapRotation' % rotname)
        self._rotation = self.generaterotation(rotation)

        if self._version != 7:
            if self._version != 6:
                self.console.setCvar('sv_mapRotation', self._rotation)
            else:
                self.console.write('sv_mapRotation %s' % self._rotation)

            if self._immediate and self._version != 6:
                self.console.setCvar('sv_mapRotationCurrent', '')
            elif self._immediate:
                self.console.write('reset sv_mapRotationCurrent')
            self._currentrotation = newrotation

            if self._initialrecount:
                self.saveroundstartrotation(self._rotation)
        else:
            self.cod7getnextmap()
            self.cod7maprotate()


    def generaterotation(self, rotation):
        #self.debug('Generate from: %s @ size: %s' % (rotation, self._rotation_size))
        rotation_size = self._rotation_size - 1  # We'll be using it as an index for _hmgt
        r = ''
        self._cod7MapRotation = []

        if self._randomizerotation:
            self.debug('Creating randomized rotation...')
            rot = copy.deepcopy(rotation)
            count = 0
            lastgametype = ''
            for gametype,maplist in rot.items():
                count += len(maplist)
            self.debug('MapCount: %s' % count)
            while count > 0:
                c = random.randint(1,count)
                #self.debug('Random: %s' % c)
                for gametype,maplist in rot.items():
                    if c > len(maplist):
                        #self.debug('Length this maplist: %s' % (len(maplist)))
                        c -= len(maplist)
                    else:
                        # Check if this mode was recently added
                        if gametype in self._recentgts:
                            self.debug('Gametype %s skipped, already added in the last %s items' % (gametype, self._hmgt[rotation_size]) )
                            continue    # skip to the next map in queue
                        # Check if this map was recently added
                        elif maplist[c-1] in self._recentmaps:
                            self.debug('Map %s skipped, already added in the last %s items' % (maplist[c-1], self._hmm[rotation_size]) )
                            continue    # skip to the next map in queue
                        # cod7 - check if this gametype exists for the chosen game mode and a number of slots
                        elif self._version == 7 and gametype not in self._cod7Playlists[self._slot_num][self._game_mode]:
                            self.warning('Gametype %s cannot be played in current playlist (game_mode=%d, slot_num=%d)' % (gametype, self._slot_num, self._game_mode))
                            continue    # skip to the next map in queue

                        if self._version != 7:
                            addition = ''

                        if gametype != lastgametype or self._version in (4, 6, 11): #UO, CoD4 and CoD6 need every gametype pre map
                            addition = 'gametype ' + gametype + ' '

                        addingmap = maplist.pop(c-1)
                        
                        if self._version != 7:
                            addition = addition + 'map ' + addingmap + ' '

                        if self._version != 7 and (len(r) + len(addition)) > 960:
                            self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
                            count = 0 # Make sure we break out of the while loop
                            break     # Break out of the for loop

                        if self._version != 7:
                            r += addition
                        else:
                            self._cod7MapRotation.append ([gametype,addingmap])

                        #self.debug('Building: %s' % r)
                        rot[gametype] = maplist
                        lastgametype = gametype

                        if self._hmm[rotation_size] != 0:
                            self._recentmaps.append(addingmap)
                            self._recentmaps = self._recentmaps[-self._hmm[rotation_size]:] # Slice the last _hmm nr. of maps
                        if self._hmgt[rotation_size] != 0:
                            self._recentgts.append(gametype)
                            self._recentgts = self._recentgts[-self._hmgt[rotation_size]:] # Slice the last _hmgt nr. of gametypes
                        break
                count -= 1

        else:
            self.debug('Creating non-randomized rotation...')
            stringmax = 0
            # UO, CoD6 and CoD4 needs every gametype pre map
            if self._version in (4, 6, 11):
                for gametype,maplist in rotation.items():
                    for map in maplist:
                        addition = 'gametype ' + gametype + ' ' + 'map ' + map + ' '
                        if (len(r) + len(addition)) > 980:
                            self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
                            stringmax = 1 # Make sure we break out of the first for loop
                            break         # Break out of the nested for loop
                        r += addition
                    if stringmax == 1:
                        break # Break out of the first for loop

            elif self._version == 7:
                addition = []
                for gametype,maplist in rotation.items():
                    for map in maplist:
                        addition = [gametype, map]
                        self._cod7MapRotation.append (addition)
                self._cod7MapRotationFixed = self._cod7MapRotation

            else:
                for gametype,maplist in rotation.items():
                    r2 = r # Backup r
                    r = r + 'gametype ' + gametype + ' '
                    for map in maplist:
                        r = r + 'map ' + map + ' '
                        if len(r) > 980 and self._version != 7:
                            self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
                            r = r2 # Restore r and break out
                            stringmax = 1
                            break
                        r2 = r # Backup r
                    if stringmax == 1:
                        break # Break out completely

        if self._version != 7:
            self.debug('NewRotation: %s' % r)
        else:
            self.debug('NewBlackOpsRotation: %s' % self._cod7MapRotation)
        if self._version != 7 and r.strip() == '':
            r = self._fallbackrotation
            self.error('Error: Generation failed! Reverting to original rotation!')
        # Strip excessive spaces from the new rotation
        r = r.strip()
        return r


    def recountplayers(self):
        if self._version != 7:
            # do we still need the original rotation
            if self._needfallbackrotation:
                self.retrievefallback()
            # if we still didnt get it we'll wait for the next round/map
            if self._needfallbackrotation:
                self.error('Error: Still not able to retrieve initial rotation!')
                return None

        # reset, recount and set a rotation
        self._oldplayercount = self._playercount
        self._playercount = 0
        self._donotadjustnow = False

        self._playercount = len (self.console.clients.getList())

        self.debug('PlayerCount: %s' % self._playercount)

        if self._oldplayercount == -1:
            self.adjustrotation(0)
        elif self._playercount > self._oldplayercount:
            self.adjustrotation(+1)
        elif self._playercount < self._oldplayercount:
            self.adjustrotation(-1)
        else:
            pass


    def retrievefallback(self):
        self._fallbackrotation = self.console.getCvar('sv_mapRotation').getString()
        time.sleep(0.5) # Give us plenty time to store the rotation
        if self._fallbackrotation is not None:
            self.debug('Fallbackrotation: %s' % self._fallbackrotation)
            # this is the only place where _needfallbackrotation is set to False!
            self._needfallbackrotation = False
        else:
            self.error('Could not save original rotation... Waiting for next pass')


    def saveroundstartrotation(self, rotation=''):
        if self._initialrecount and self._version != 7:
            self.debug('Saving the first generated rotation as the cached roundstart rotation')
            self._roundstart_mapRotation = rotation
            self._roundstart_mapRotationCurrent = ''
            self._initialrecount = False

        elif self._version != 7:
            self.debug('Getting current Rotation')
            self._roundstart_mapRotation = self.console.getCvar('sv_mapRotation')
            if self._roundstart_mapRotation is not None and self._roundstart_mapRotation != '':
                self._roundstart_mapRotation = self._roundstart_mapRotation.getString()
                self.debug('Cached Rotation: %s' % self._roundstart_mapRotation)
            else:
                self._roundstart_mapRotation = None

            self._roundstart_mapRotationCurrent = self.console.getCvar('sv_mapRotationCurrent')
            if self._roundstart_mapRotationCurrent is not None and self._roundstart_mapRotationCurrent != '':
                self._roundstart_mapRotationCurrent = self._roundstart_mapRotationCurrent.getString()
                # Removing extra spaces just in case...
                self._roundstart_mapRotationCurrent = self._roundstart_mapRotationCurrent.strip()
                self.debug('Cached RotationCurrent: %s' % self._roundstart_mapRotationCurrent)
            else:
                self._roundstart_mapRotationCurrent = ''

            self._roundstart_currentrotation = self._currentrotation
        else:
            pass

    def cod7getnextmap(self):
        if len(self._cod7MapRotation) == 0:
            self._donotadjustnow = False
            self.debug ('Nothing to rotate, re-adjusting rotation...')
            self.adjustrotation(0)

        # Get the next [gametype,map] and remove it from _cod7MapRotation
        if not self._outofrotation:
            self._nextrotationmap = self._cod7MapRotation.pop(0)
        self._nextmap7 = self._nextrotationmap
        self._outofrotation = False

    def cod7maprotate(self):
        self.debug('COD7MAPROTATE: next map will be %s at %s' % (self._nextmap7[0], self._nextmap7[1]))

        # Set the playlist thus changing the gametype
        self.console.write('setadmindvar playlist %s' % self._cod7Playlists[self._slot_num][self._game_mode][self._nextmap7[0]])

        # Build a map exclusion rule then apply it. Will exclude every map except the next one.
        exclusion = copy.copy (self._cod7Maps)
        exclusion.remove (self._nextmap7[1])
        self.console.write ('setadmindvar playlist_excludeMap "%s"' % ' '.join(exclusion))

        # Keep playlist_excludeGametypeMap empty, I'm in charge here!
        # If next map is in this dvar, server will keep not changing maps until it recieves something that's not restricted
        self.console.write ('setadmindvar playlist_excludeGametypeMap ""')


    def fastrestart(self):
        self._countDown = int(self._mapDelay)/10
        while self._countDown > 0:
            self.console.say('^1*** MATCH STARTING IN ^7%s^1 SECONDS ***' % (self._countDown*10) )
            self._countDown -= 1
            time.sleep(10)

        self.console.say('^7*** ^1MATCH ^7*** ^1STARTING ^7***')
        time.sleep(3)
        self.console.write(self._restartCmd)

    def cmd_maps(self, data, client=None, cmd=None):
        """\
        - list the server's map rotation for cod7, optionally limit the number in the list
        """

        if not self._adminPlugin.aquireCmdLock(cmd, client, 60, True):
            client.message('^7Do not spam commands')
            return

        m = self._adminPlugin.parseUserCmd(data)
        if m:
            try:
                limitno = int(m[0])
            except:
                limitno = 1000
            
        else:
            limitno = 1000

        if self._randomizerotation:
            rotation = self._cod7MapRotation[0:limitno]
        else:
            if limitno == 1000:
                rotation = self._cod7MapRotationFixed
            else:
                rotation = self._cod7MapRotation[0:limitno]

        maplist = ''
        
        for maps in rotation:
            mapeasyname = self.getcod7mapeasyname(maps[1])
            maplist = maplist + mapeasyname + '^7-^3' + maps[0] + '  ^2'
            
        if len(maplist) > 0:
            cmd.sayLoudOrPM(client, '^7Map Rotation: ^2%s' % maplist)
        else:
            client.message('^7Error: could not get map list')
    
    def cmd_nextmap(self, data, client=None, cmd=None):
        """\
        - list the next map in rotation for cod7
        """
        if not self._adminPlugin.aquireCmdLock(cmd, client, 60, True):
            client.message('^7Do not spam commands')
            return

        map = self._nextmap7

        if map:
            mapeasyname =  self.getcod7mapeasyname(map[1])
            if map[0] == 'koth':
                gt = 'hq'
            else:
                gt = map[0]
                
            cmd.sayLoudOrPM(client, '^7Next Map: ^2%s with ^3%s^2 gametype' % (mapeasyname, gt))
        else:
            client.message('^7Error: could not get map name')
            
    def cmd_map(self, data, client=None, cmd=None):
        """\
        - switch what the next map and gametype is for cod7
        """
        #m = self._adminPlugin.parseUserCmd(data)
        m = data.split(' ')
        self.debug(m)
        gt = m[-1]
        map = string.join(m[0:-1])
        
        self.debug('Result is map %s gametype %s' % (map, gt))
        map = map.lower()
        if (map not in self._cod7Maps) and (map not in self._cod7Mapeasynameslower):
            client.message('^7You must supply a map and valid gametype to change to.')
            return
        
        if map in self._cod7Mapeasynameslower:
            maphardname = self.getcod7maphardname(map)
         
        if not gt or gt not in self._cod7Gametypes or gt not in self._cod7Playlists[self._slot_num][self._game_mode]:
            client.message('^7You must supply a valid gametype to change to.')
            return
        # Set the playlist thus changing the gametype
        if gt == 'hq':
            gt = 'koth'
            

        self._outofrotation = True
        self._nextmap7 = [gt, maphardname]
        if gt == 'koth':
            gt = 'hq'
        client.message('^7Next map changed to ^2%s with ^3%s^2 gametype' % (map, gt))
        self.cod7maprotate()


    def aquireCmdLock(self, cmd, client, delay, all=True):
        if client.maxLevel >= 20:
            return True
        elif cmd.time + delay <= self.console.time():
            return True
        else:
            return False    
    
    def getcod7mapeasyname(self, map):
        if map in self._cod7Maps:
            ix = self._cod7Maps.index(map)
            self.debug(map)
            return self._cod7Mapeasynames[ix]
        else:
            return 'Error'
            
    def getcod7maphardname(self, map):
        map = map.lower()
        if map in self._cod7Mapeasynameslower:
            ix = self._cod7Mapeasynameslower.index(map)
            return self._cod7Maps[ix]
        else:
            return 'Error'
            

if __name__ == '__main__':
    print ('\nThis is version '+__version__+' by '+__author__+' for BigBrotherBot.\n')
