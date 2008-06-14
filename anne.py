#!/usr/bin/python

# IRC bot that announces entries from RSS feeds to a channel.
# Written by Sam Morris <sam@robots.org.uk>

import config

def sws (s):
    '''Squeeze whitespace characters together. Whitespace characters
    are taken from <http://www.w3.org/TR/2006/REC-xml11-20060816/#NT-S>.
    Python's string/uniode split method appears to handle them all.'''
    return ' '.join (s.split ())

def headline_default (feed, data, entry):
    '''Default feed entry format.'''
    return '%s (%s): <%s>' % (sws (entry.title), feed['name'], sws (entry.link))

def headline_summary (feed, data, entry):
    '''debian-security-announce describes the vulnerability in the summary
    of its entries.'''
    return '%s (%s): %s <%s>' % (sws (entry.title), feed['name'], sws (entry.summary), sws (entry.link))

def headline_title (feed, data, entry):
    '''useful for testing'''
    return  '%s: %s' % (feed['name'], sws (entry.title))

# end of configuration

def got_data (data, feed, announce):
    import feedparser
    data = feedparser.parse (data)

    if data.bozo == 1:
        log.msg ('%s: %s' % (feed['name'], data.bozo_exception))

    if len (data.entries) == 0:
        log.msg ('%s: 0 entries; ignoring' % (feed['name']))
        return

    # feed entires are stored in a dict that maps the entry's GUID to its
    # announcement string
    hf = globals ()[feed.get ('headline', 'headline_default')]
    current_entries = {}
    ignored_entries = 0
    for e in data.entries:
        if not hasattr (e, 'id'):
            ignored_entries += 1
            continue
        current_entries[e.id] = hf (feed, data, e)
    if ignored_entries > 0:
        log.msg ('%s: ignored %i entries without ids' % (feed['name'], ignored_entries))

    old_entries = feed.get ('entries', None)
    if old_entries == None:
        log.msg ('%s: %i entries' % (feed['name'], len (current_entries)))
    else:
        new_entries = []
        for id, entry in current_entries.iteritems ():
            if id not in old_entries:
                new_entries.append (entry)
        log.msg ('%s: %i new entries' % (feed['name'], len (new_entries)))
        for e in new_entries:
            announce (e)

    feed['entries'] = current_entries

def got_error (failure, feed):
    #log.err ('%s: %s' % (url, failure.getErrorMessage ()))
    log.err ()
    return failure

def refresh_feeds (announce):
    from twisted.web.client import getPage

    for feed in config.feeds:
        d = getPage (feed['url'], timeout = 60, agent = 'anne/0.2')
        d.addCallback (got_data, feed, announce)
        d.addErrback (got_error, feed)

from twisted.words.protocols import irc
class AnnounceBot (irc.IRCClient):
    '''An IRC but to announce things to a channel.'''

    def connectionMade (self):
        irc.IRCClient.connectionMade (self)
        log.msg ('connection made')

    def signedOn (self):
        self.join (self.factory.channel)
        log.msg ('signed on')

    def joined (self, channel):
        log.msg ('joined ', channel)

    def kickedFrom (self, channel, kicker, message):
        log.msg ('kicked by %s (%s)' % (kicker, message))
        self.join (self.factory.channel)

from twisted.internet import protocol
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

        self.bot.nickname = config.nick
        self.bot.realname = 'Announce Bot'
        self.bot.versionName = 'anne'
        self.bot.versionNum = '0'
        self.bot.versionEnv = sws (sys.version)
        self.bot.sourceURL = 'http://robots.org.uk/src/anne/'

        self.bot.lineRate = 3
        return self.bot

    def announce (self, announcement):
        if self.bot == None:
            log.msg ('not connected; skipping "%s"' % (announcement))
        else:
            self.bot.msg ('#%s' % (self.channel), announcement.encode ('utf-8'))

    def clientConnectionLost (self, connector, reason):
        log.msg ('connection lost: ', reason)
        self.bot = None
        protocol.ReconnectingClientFactory.clientConnectionLost (self, connector, reason)

    def clientConnectionFailed (self, connector, reason):
        log.msg ('connection failed: ', reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed (self, connector, reason)

from twisted.python import log

if __name__ == '__main__':
    import sys
    log.startLogging (sys.stdout, setStdout=False)

    factory = AnnounceBotFactory (config.channel)

    from twisted.internet import task
    l = task.LoopingCall (refresh_feeds, factory.announce)
    l.start (config.refresh_time)

    from twisted.internet import reactor
    reactor.connectTCP (config.host, config.port, factory)
    reactor.run ()

# vim: softtabstop=4 expandtab
