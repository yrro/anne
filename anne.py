#! /usr/bin/env python
#
# Bot to anounce Debian Security Advisories to a channel.
# Written by Sam Morris <sam@robots.org.uk>

"""Bot to announce Debian Security Advisories to a channel."""

# Functions to print out headlines
def getHeadlines_summary (feed, data):
	return sets.Set (map (lambda e: '%s: %s <%s>' % (e['title'], e['summary'], e['link']), data['entries']))
def getHeadlines (feed, data):
	return sets.Set (map (lambda e: '%s: <%s>' % (e['title'], e['link']), data['entries']))

# Feed config
feeds = [{'name': 'debian-security-announce', 'url': 'http://www.debian.org/security/dsa', 'filter': getHeadlines_summary},
         {'name': 'debian-news', 'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.news', 'filter': getHeadlines},
         {'name': 'debian-devel-announce', 'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.devel.announce', 'filter': getHeadlines},
         {'name': 'debian-announce', 'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.announce', 'filter': getHeadlines},
         {'name': 'debian-administration', 'url': 'http://www.debian-administration.org/headlines.rdf', 'filter': getHeadlines},
		 {'name': 'debianhelp', 'url': 'http://www.debianhelp.org/rss.xml', 'filter': getHeadlines},
		 {'name': 'lwn', 'url': 'http://lwn.net/headlines/rss', 'filter': getHeadlines}]
refresh = 60 * 60 # seconds
#feeds = [{'name': 'yahoo', 'url': 'http://rss.news.yahoo.com/rss/topstories', 'filter': getHeadlines},
#          {'name': 'google', 'url': 'http://news.google.com/?output=rss', 'filter': getHeadlines}]

# IRC config
server = 'irc.uk.quakenet.org'
port = 6667
nick = 'anne'
channel = 'debian'

# Here be dragons
from twisted.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.internet import task

import sys

import sets
import feedparser

def refreshFeeds (factory):
	for feed in feeds:
		# this holds the headlines for each feed
		# initialize it to be the empty set
		if not feed.has_key ('headlines'):
			feed['headlines'] = sets.Set ()
			
		headlines_prev = feed['headlines']

		# if there is an error, feedparser will return an empty collection
		# if this happens, just use the previous set of headlines
		headlines_tmp = feed['filter'] (feed, feedparser.parse (feed['url']))
		if len (headlines_tmp) > 0:
			feed['headlines'] = headlines_tmp
		del headlines_tmp

		headlines_new = feed['headlines'].difference (headlines_prev)
		print '%s: %d new headlines' % (feed['name'], len (headlines_new))

		if len (headlines_prev) > 0:
			if len (headlines_new) == len (headlines_prev):
				print '%s: might have lost some headlines' % (feed['name'])
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
		self.bot.lineRate = 2
		return self.bot

	def announce (self, announcement):
		if self.bot == None:
			print 'not connected; skipping "%s"' % (announcement)
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
	print 'anne -- a bot to announce RSS feed entries to an IRC channel'

	factory = AnnounceBotFactory (channel)
	reactor.connectTCP (server, port, factory)

	l = task.LoopingCall (refreshFeeds, (factory))
	l.start (refresh)

	reactor.run ()
