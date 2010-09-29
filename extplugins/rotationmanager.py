#
# Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2005 www.xlr8or.com
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

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
# 1.3.5        : Added support for gametypehistory, changed maphistory - justabaka
#

__version__ = '1.3.5'
__author__  = 'xlr8or'

import b3, re, threading, time, random, copy
import b3.events

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
  _recentmaps = []                      # The Maphistory
  _recentgts = []                       # The Gametype history
  _hmm = 4                              # HowManyMaps to keep as a maphistory
  _hmgt = [0,0,0]                       # HowManyGameTypes to keep as a gametype history

  def onStartup(self):
    """\
    Initialize plugin settings
    """
    # Register our events
    self.verbose('Registering events')
    self.registerEvent(b3.events.EVT_CLIENT_CONNECT)
    self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
    self.registerEvent(b3.events.EVT_GAME_EXIT)

    # don't adjust the rotation just yet
    self._donotadjustnow = True
    self._needfallbackrotation = True

    # we'll store the initial rotation
    self.retrievefallback()
      
    # wait half a minute after pluginstart to do an initial playercount
    t1 = threading.Timer(30, self.recountplayers)
    t1.start()

    # Save the first generated rotation as the cached rountstart rotation
    t2 = threading.Timer(40, self.saveroundstartrotation)
    t2.start()


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
    self._hmm = abs(self.config.getint('settings', 'maphistory'))
	
    for rotation_size in self.config.options('gametypehistory'):
      self._hmgt[0] = abs(self.config.getint('gametypehistory', 'gthistory_small'))
      self._hmgt[1] = abs(self.config.getint('gametypehistory', 'gthistory_medium'))
      self._hmgt[2] = abs(self.config.getint('gametypehistory', 'gthistory_large'))
      self.debug('GTHistory is set to: %s' %(self._hmgt))

    for gametype in self.config.options('rotation_small'):
      maps = self.config.get('rotation_small', gametype)
      maps = maps.split(' ')
      self._rotation_small[gametype] = maps
      self.debug('Small %s: %s' %(gametype, maps))
    
    for gametype in self.config.options('rotation_medium'):
      maps = self.config.get('rotation_medium', gametype)
      maps = maps.split(' ')
      self._rotation_medium[gametype] = maps
      self.debug('Medium %s: %s' %(gametype, maps))
    
    for gametype in self.config.options('rotation_large'):
      maps = self.config.get('rotation_large', gametype)
      maps = maps.split(' ')
      self._rotation_large[gametype] = maps
      self.debug('Large %s: %s' %(gametype, maps))
    
    if self._version in (1, 11):    # 1: CoD1 or 11: CoD UO
      self._restartCmd = 'map_restart'
    elif self._version in (2, 4, 5):   # CoD2, CoD4 or CoD5
      self._restartCmd = 'fast_restart'
    else:
      self._mapDelay = 0


  def onEvent(self, event):
    """\
    Handle intercepted events
    """
    if event.type == b3.events.EVT_CLIENT_CONNECT:
      self._playercount += 1
      self.debug('PlayerCount: %s' % (self._playercount))    
      # we're going up, pass a positive 1 to the adjustmentfunction
      self.adjustrotation(+1)
    elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
      self._playercount -= 1
      self.debug('PlayerCount: %s' % (self._playercount))    
      # we're going down, pass a negative 1 to the adjustmentfunction
      self.adjustrotation(-1)
    elif event.type == b3.events.EVT_GAME_EXIT:
      self._donotadjustnow = True
      # wait 2 mins and cache the current rotation cvars
      t3 = threading.Timer(120, self.saveroundstartrotation)
      t3.start()
      # wait 3 mins and do a recount
      t4 = threading.Timer(180, self.recountplayers)
      t4.start()
      # should we restart the map/round?
      if self._mapDelay != 0:
        t5 = threading.Thread(target=self.fastrestart)
        t5.start()


  def adjustrotation(self, delta):
    if self._donotadjustnow == True:
      return None
      
    if delta == +1:
      if self._playercount > (self._switchcount2 + self._hysteresis):
        self.setrotation(3)
      elif self._playercount > (self._switchcount1 + self._hysteresis):
        self.setrotation(2)
      else:
        self.setrotation(1)
    
    elif delta == -1 or delta == 0:
      if self._playercount < (self._switchcount1 + (delta * self._hysteresis)):
        self.setrotation(1)
      elif self._playercount < (self._switchcount2 + (delta * self._hysteresis)):
        self.setrotation(2)
      else:
        self.setrotation(3)
    
    else:
      self.error('Error: Invalid delta passed to adjustrotation')
    
    return None


  def setrotation(self, newrotation):
    if newrotation == self._currentrotation:
      return None

    # restore the rotation if the new one is the same as the one at round/map start
    if newrotation == self._roundstart_currentrotation and self._roundstart_mapRotation != None:
      self.debug('Restoring Cached Roundstart Rotations')
      if self._roundstart_mapRotation != '':
        self.console.setCvar('sv_mapRotation', self._roundstart_mapRotation)
      if self._roundstart_mapRotationCurrent != '':
        self.console.setCvar('sv_mapRotationCurrent', self._roundstart_mapRotationCurrent)
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

    self.debug('Adjusting to %s mapRotation' % rotname)
    self.console.setCvar('sv_mapRotation', self.generaterotation(rotation, newrotation))
    if self._immediate:
      self.console.setCvar('sv_mapRotationCurrent', '')
    self._currentrotation = newrotation


  def generaterotation(self, rotation, rotation_size):
    #self.debug('Generate from: %s @ size: %s' % (rotation, rotation_size))
    rotation_size -=1 # We'll be using it as an index for _hmgt 
    r = ''

    if self._randomizerotation:
      self.debug('Creating randomized rotation...')
      rot = copy.deepcopy(rotation)
      count = 0
      lastgametype = ''
      for gametype,maplist in rot.items():
        count = count + len(maplist)
      self.debug('MapCount: %s' % count)
      while count > 0:
        c = random.randint(1,count)
        #self.debug('Random: %s' % c)
        for gametype,maplist in rot.items():
          _skipMap = False
          if c > len(maplist):
            #self.debug('Length this maplist: %s' % (len(maplist)))
            c -= len(maplist)
          else:
            # Check if this mode was recently added
            if gametype in self._recentgts:
              _skipMap = True
              self.debug('Gametype %s skipped, already added in the last %s items' % (gametype, self._hmgt[rotation_size]) )
              continue # skip to the next map in queue
            # Check if this map was recently added
            elif maplist[c-1] in self._recentmaps:
              _skipMap = True
              self.debug('Map %s skipped, already added in the last %s items' % (maplist[c-1], self._hmm) )
              continue # skip to the next map in queue
            addition = ''
            if gametype != lastgametype or self._version == 11 or self._version == 4: #UO and CoD4 need every gametype pre map
              addition = 'gametype ' + gametype + ' '
            addingmap = maplist.pop(c-1)
            addition = addition + 'map ' + addingmap + ' '
            if (len(r) + len(addition)) > 980:
              self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
              count = 0 # Make sure we break out of the while loop
              break     # Break out of the for loop
            r = r + addition
            #self.debug('Building: %s' % r)
            rot[gametype] = maplist
            lastgametype = gametype
            if self._hmm != 0:
              self._recentmaps.append(addingmap)
              self._recentmaps = self._recentmaps[-self._hmm:] # Slice the last _hmm nr. of maps
            if self._hmgt[rotation_size] != 0:
              self._recentgts.append(gametype)
              self._recentgts = self._recentgts[-self._hmgt[rotation_size]:] # Slice the last _hmgt nr. of gametypes
            break
        count -= 1
    else:
      self.debug('Creating non-randomized rotation...')
      stringmax = 0
      # UO, CoD4 needs every gametype pre map
      if self._version == 11 or self._version == 4:
        for gametype,maplist in rotation.items():
          for map in maplist:
            addition = 'gametype ' + gametype + ' ' + 'map ' + map + ' '
            if (len(r) + len(addition)) > 980:
              self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
              stringmax = 1 # Make sure we break out of the first for loop
              break     # Break out of the nested for loop
            r = r + addition
          if stringmax == 1:
            break # Break out of the first for loop
      else:
        for gametype,maplist in rotation.items():
          r2 = r # Backup r
          r = r + 'gametype ' + gametype + ' '
          for map in maplist:
            r = r + 'map ' + map + ' '
            if len(r) > 980:
              self.debug('Maximum sv_rotation stringlength reached... Aborting adding maps to rotation!')
              r = r2 # Restore r and break out
              stringmax = 1
              break
            r2 = r # Backup r
          if stringmax == 1:
            break # Break out completely 


    self.debug('NewRotation: %s' % (r))
    if r.strip() == '':
      r = self._fallbackrotation
      self.error('Error: Generation failed! Reverting to original rotation!')
    # Strip excessive spaces from the new rotation
    r = r.strip()
    return r


  def recountplayers(self):
    # do we still need the original rotation
    if self._needfallbackrotation == True:
      self.retrievefallback()
    # if we still didnt get it we'll wait for the next round/map
    if self._needfallbackrotation == True:
      self.error('Error: Still not able to retrieve initial rotation!')
      return None
    
    # reset, recount and set a rotation
    self._oldplayercount = self._playercount
    self._playercount = 0
    self._donotadjustnow = False
    
    for p in self.console.clients.getList():
      self._playercount += 1

    self.debug('PlayerCount: %s' % (self._playercount))    
    
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
    if self._fallbackrotation != None:
      self.debug('Fallbackrotation: %s' %(self._fallbackrotation))
      # this is the only place where _needfallbackrotation is set to False!
      self._needfallbackrotation = False
    else:
      self.error('Could not save original rotation... Waiting for next pass')


  def saveroundstartrotation(self):
    self.debug('Getting current Rotation')
    self._roundstart_mapRotation = self.console.getCvar('sv_mapRotation')
    if self._roundstart_mapRotation != None and self._roundstart_mapRotation != '':
      self._roundstart_mapRotation = self._roundstart_mapRotation.getString()
      self.debug('Cached Rotation: %s' %(self._roundstart_mapRotation))
    else:
      self._roundstart_mapRotation = None

    self._roundstart_mapRotationCurrent = self.console.getCvar('sv_mapRotationCurrent')
    if self._roundstart_mapRotationCurrent != None and self._roundstart_mapRotationCurrent != '':
      self._roundstart_mapRotationCurrent = self._roundstart_mapRotationCurrent.getString()
      # Removing extra spaces just in case...
      self._roundstart_mapRotationCurrent = self._roundstart_mapRotationCurrent.strip()
      self.debug('Cached RotationCurrent: %s' %(self._roundstart_mapRotationCurrent))
    else:
      self._roundstart_mapRotationCurrent = ''

    self._roundstart_currentrotation = self._currentrotation


  def fastrestart(self):
    self._countDown = int(self._mapDelay)/10
    while self._countDown > 0:
      self.console.say('^1*** MATCH STARTING IN ^7%s^1 SECONDS ***' % (self._countDown*10) )
      self._countDown -= 1
      time.sleep(10)
    
    self.console.say('^7*** ^1MATCH ^7*** ^1STARTING ^7***')
    time.sleep(3)
    self.console.write(self._restartCmd)

if __name__ == '__main__':
  print ('\nThis is version '+__version__+' by '+__author__+' for BigBrotherBot.\n')
