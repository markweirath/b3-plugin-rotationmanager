###################################################################################
#
# Plugin for B3 (www.bigbrotherbot.net)
# (c) 2006 www.xlr8or.com (mailto:xlr8or@xlr8or.com)
#
# This program is free software and licensed under the terms of
# the GNU General Public License (GPL), version 2.
#
# http://www.gnu.org/copyleft/gpl.html
###################################################################################

RotationManager (v1.3.8) for B3
###################################################################################

This plugin adjusts your maprotation based on the current playercount.
The configuration holds 2 switchpoints and 3 rotations. It keeps track of your
playercount and sets a small, medium or large maprotation. The plugin will
automatically create a proper random maprotation to work with.


Requirements:
###################################################################################

- Call of Duty server
- B3 version 1.1.0 or higher


Installation:
###################################################################################

1. Unzip the contents of this package into your B3 folder. It will
place the .py file in b3/extplugins and the config file .xml in
your b3/extplugins/conf folder.

2. Open the .xml file with your favorit editor and modify the
levels if you want them different. Do not edit the settingnames
for they will not function under a different name.

3. Open your B3.xml file (in b3/conf) and add the next line in the
<plugins> section of the file:

<plugin name="rotationmanager" priority="12" config="@b3/extplugins/conf/rotationmanager.xml"/>

The numer 12 in this just an example. Make sure it fits your
plugin list.


Changelog
###################################################################################
v1.3.9         : Added DLC2 maps, 'easy' map names support. Implemented map, maps and
                 nextmap commands for cod7 ranked server - 82ndab-Bravo17
v1.3.8         : Reworked adjustrotation, fixed bugs that were causing unnecessary
                 setrotation() calls - Just a baka
V1.3.7         : Implemented proper cod6 support, optimized first saveroundstartrotation - Just a baka
v1.3.6         : Added cod7 support, beautified code. - Just a baka
v1.3.5         : Added gametypehistory, changed maphistory: both are now configurable for each
                 rotation size individually - Just a baka
v1.3.4         : bugfix in maphistory
v1.3.3         : ...
v1.3.2         : only add maps that have not been added in the last 4 passes, no more double maps
v1.3.1         : fixed a bug where on slower boxes the rotation wasn't stored on time
v1.3.0         : Added support for CoD4
v1.2.2 - v1.2.3: Introduced version 11 for UO; generate rotations with all gametypes
v1.2.1 - v1.2.2: Added another safety .strip() when storing _roundstart_mapRotationCurrent
v1.2.0 - v1.2.1: Bugfixversion
v1.1.6 - v1.2.0: Added hysteresis (switchpoint threshold) and internal restore 
                 rotation functionality 
v1.1.4 - v1.1.5: Bugfix in fast-restart section
v1.1.3 - v1.1.4: Fixed a bug where B3 was unresponsive while in restart-countdown
                 Added CoD1/CoD2 restartcompatibility
v1.1.2 - v1.1.3: Intro copy.deepcopy() to fix empty rotation dict.
v1.1.1 - v1.1.2: Added more debugging info
v1.1.0 - v1.1.1: Added Fallbackrotation and some errorchecking
v1.0.0 - v1.1.0: Added MapDelay and smart/random creation of rotations
v1.2.3 - v1.2.4: Added check for limitation of the maximum stringlength (capped at 980)
v1.0.0         : Initial release


###################################################################################
xlr8or - 28 nov 2007 - www.bigbrotherbot.net // www.xlr8or.com
