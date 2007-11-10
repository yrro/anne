#! /usr/bin/env python
#
# Bot to anounce Debian Security Advisories to a channel.
# Written by Sam Morris <sam@robots.org.uk>

# TODO: use Twisted's Deferred callback thingies to refresh the feeds in the
# background

"""Bot that announces Debian-related news to an IRC channel."""

# Functions to print out headlines
#def getHeadlines_summary (feed):
#	return set (map (lambda e: '%s (%s): %s <%s>' % (e['title'], feed['name'], e['summary'], e['link']), feed['data']['entries']))
#def getHeadlines (feed):
#	return set (map (lambda e: '%s (%s): <%s>' % (e['title'], feed['name'], e['link']), feed['data']['entries']))

def getHeadlines_summary (feed):
	return ['%s (%s): %s <%s>' % (e['title'], feed.name, e['summary'], e['link']) for e in feed.data['entries']]

import feedparser
class Feed (object):
	def __init__ (self, name, url, headline_function = None):
		(self.__name, self.__url, self.__hf) = (name, url, headline_function)
		self.__headlines = []
	
	name = property (lambda self: self.__name)
	url = property (lambda self: self.__url)
	
	def refresh (self):
		print 'refreshing %s...' % (self.name)

		data = feedparser.parse (self.url)
		if data['bozo'] == 1:
			print '%s: %s' % (self.name, data['bozo_exception'])
		if len (data['entries']) == 0:
			print '%s: no entries; ignoring' % (self.name)
			return
		
		self.__data = data

		if self.__hf != None:
			self.__headlines = self.__hf (self)
		else:
			self.__headlines = ['%s (%s): <%s>' % (e['title'], self.name, e['link']) for e in self.data['entries']]

	data = property (lambda self: self.__data)
	headlines = property (lambda self: set (self.__headlines))

# Feed config
feeds = [Feed ('debian-security-announce', 'http://www.debian.org/security/dsa', getHeadlines_summary),
         Feed ('debian-news', 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.news'),
         Feed ('debian-devel-announce', 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.devel.announce'),
         Feed ('debian-announce', 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.announce'),
         Feed ('debian-administration.org', 'http://www.debian-administration.org/headlines.rdf'),
		 Feed ('debianhelp.org', 'http://www.debianhelp.org/rss.xml'),
		 Feed ('LWN', 'http://lwn.net/headlines/rss'),
		 Feed ('lugradio', 'http://lugradio.org/episodes.ogg.rss'),
		 #Feed ('Planet Debian', 'http://planet.debian.org/rss20.xml'),
		 Feed ('Debian Times', 'http://times.debian.net/?format=rss20.xml'),
		 Feed ('Debian Package of the Day', 'http://debaday.debian.net/feed/'),
		 Feed ('Slashdot', 'http://rss.slashdot.org/Slashdot/slashdot'),
		 Feed ('KernelTrap', 'http://kerneltrap.org/node/feed'),
		 Feed ('UK Terror Status', 'http://www.terror-alert.co.uk/feed/'),
		 Feed ('Open Rights Group', 'http://www.openrightsgroup.org/feed/'),
		 Feed ('Free Software Foundation', 'http://www.fsf.org/news/RSS'),
		 Feed ('Spyblog', 'http://p10.hostingprod.com/@spyblog.org.uk/blog/atom.xml'),
		 Feed ('Ars Technica', 'http://feeds.arstechnica.com/arstechnica/BAaf')]

refresh = 60 * 60 # seconds
#feeds = [Feed ('yahoo', 'http://rss.news.yahoo.com/rss/topstories'),
#         #Feed ('google', 'http://news.google.com/?output=rss'),
#		 Feed ('bbc', 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml')]

# IRC config
server = 'irc.uk.quakenet.org'
port = 6667
nick = 'anne'
channel = 'debian'

import sys
from twisted.internet import reactor, protocol, task
from twisted.python import log
from twisted.words.protocols import irc

def refreshFeeds (factory):
	for feed in feeds:
		headlines_prev = feed.headlines
		feed.refresh ()
		headlines_new = feed.headlines.difference (headlines_prev)
		print '%s: %d new headlines' % (feed.name, len (headlines_new))

		if len (headlines_prev) > 0:
			if len (headlines_new) == len (headlines_prev):
				print '%s: might have lost some headlines' % (feed.name)
			for h in headlines_new:
				factory.announce (h)

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
		print 'joined ', channel
	
	def kickedFrom (self, channel, kicker, message):
		print 'kicked by %s (%s)' % (kicker, message)
		self.join (self.factory.channel)

class AnnounceBotFactory (protocol.ReconnectingClientFactory):
	'''A factory for AnnounceBots.

	A new instance of the bot will be created each time we connect to the
	server.'''

	# Holds a reference to the AnnounceBot for the current connection
	bot = None

	def __init__ (self, channel):
		self.channel = channel

	def buildProtocol (self, addr):
		self.resetDelay ()

		self.bot = AnnounceBot ()
		self.bot.factory = self
		self.bot.nickname = nick
		self.bot.realname = 'Announce Bot'
		self.bot.lineRate = 3
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

	factory = AnnounceBotFactory (channel)
	reactor.connectTCP (server, port, factory)

	l = task.LoopingCall (refreshFeeds, (factory))
	l.start (refresh)

	reactor.run ()
