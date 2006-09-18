#! /usr/bin/env python
#
# Bot to anounce Debian Security Advisories to a channel.
#
# Version 20060423
# Written by Sam Morris <sam@robots.org.uk>

"""Bot to announce Debian Security Advisories to a channel."""

# http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.news
# http://rss.gmane.org/messages/excerpts/gmane.linux.debian.devel.announce
# http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.announce

#feed = 'http://rss.slashdot.org/Slashdot/slashdot'
#feed = 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml'
feed = 'http://www.debian.org/security/dsa'
refresh = 60 * 60 # seconds
server = 'irc.uk.quakenet.org'
port = 6667
nick = 'anne'
channel = 'debian'

from twisted.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.internet import task

import sys

import sets
import feedparser

headlines = sets.Set ()

def getHeadlines (feed):
    """
    Returns a Set of strings that could be printed to a channel
    """
    return sets.Set (map (lambda e: '%s: %s <%s>' % (e['title'], e['summary'], e['link']), feed['entries']))

def refreshFeeds (factory):
	print 'updating...'
	global headlines
	headlines_prev = headlines

	# if there is an error, feedparser will return an empty collection
	# if this happens, just use the previous set of headlines
	headlines_tmp = getHeadlines (feedparser.parse (feed))
	if len (headlines_tmp) > 0:
		headlines = headlines_tmp
	del headlines_tmp

	headlines_new = headlines.difference (headlines_prev)
	print '%s new headlines' % (len (headlines_new))

	if len (headlines_prev) > 0 and len (headlines_new) == len (headlines_prev):
		print 'might have lost some headlines'
	map (factory.announce, headlines_new)

class AnnounceBot (irc.IRCClient):
	'''An IRC but to announce things to a channel.'''

	def connectionMade (self):
		irc.IRCClient.connectionMade (self)
		print 'connection made'
	
	def connectionLost (self, reason):
		irc.IRCClient.connectionLost (self)
	
	def signedOn (self):
		self.join (self.factory.channel)

	def joined (self, channel):
		print 'joined channel', channel
	
	def kickedFrom (self, channel, kicker, message):
		print 'kicked by %s (%s)' % (kicker, message)

class AnnounceBotFactory (protocol.ReconnectingClientFactory):
	'''A factory for AnnounceBots.

	A new instance of the bot will be created each time we connect to the
	server.'''

	# Holds a reference to the AnnounceBot for the current connection
	bot = None

	def __init__ (self, channel):
		self.channel = channel

	def startedConnection (self, connector):
		print 'connecting...'
	
	def buildProtocol (self, addr):
		print 'connected; resetting reconnection delay'
		self.resetDelay ()

		self.bot = AnnounceBot ()
		self.bot.factory = self
		self.bot.nickname = nick
		self.bot.realname = 'Announce Bot'
		return self.bot

	def announce (self, announcement):
		if self.bot == None:
			print 'not connected; skipping "%s..."' % (announcement[0:26])
		else:
			self.bot.msg ('#%s' % (self.channel), announcement.encode ('utf-8'))
	
	def clientConnectionLost (self, connector, reason):
		print 'connection lost: ', reason
		self.bot = None
		protocol.ReconnectingClientFactory.clientConnectionLost (self, connector, reason)
	
	def clientConnectionFailed (self, connector, reason):
		print 'connection failed: ', reason
		protocol.ReconnectingClientFactory.clientConnectionFailed (self, connector, reason)

if __name__ == '__main__':
	log.startLogging (sys.stdout)

	factory = AnnounceBotFactory (channel)
	reactor.connectTCP (server, port, factory)

	l = task.LoopingCall (refreshFeeds, (factory))
	l.start (refresh)

	reactor.run ()
