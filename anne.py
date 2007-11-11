#!/usr/bin/python

# IRC bot that announces entries from RSS feeds to a channel.
# Written by Sam Morris <sam@robots.org.uk>

refresh_time = 60 * 60 # seconds

def headlines_summary (feed, data):
    '''debian-security-announce describes the vulnerability in the summary
    of its entries.'''
    return set (['%s (%s): %s <%s>' % (e.title, feed['name'], e.summary, e.link) for e in data.entries])

def headlines_title (feed, data):
    '''useful for testing'''
    return  set (['%s: %s' % (feed['name'], e.title) for e in data.entries])

feeds = [{'name': 'debian-security-announce',   'url': 'http://www.debian.org/security/dsa', 'headline': headlines_summary},
         {'name': 'debian-news',                'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.news'},
         {'name': 'debian-devel-announce',      'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.devel.announce'},
         {'name': 'debian-announce',            'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.announce'},
         {'name': 'debian-administration.org',  'url': 'http://www.debian-administration.org/headlines.rdf'},
         {'name': 'debianhelp.org',             'url': 'http://www.debianhelp.org/rss.xml'},
         {'name': 'LWN',                        'url': 'http://lwn.net/headlines/rss'},
         {'name': 'lugradio',                   'url': 'http://lugradio.org/episodes.ogg.rss'},
         {'name': 'Planet Debian',              'url': 'http://planet.debian.org/rss20.xml'},
         {'name': 'Debian Times',               'url': 'http://times.debian.net/?format=rss20.xml'},
         {'name': 'Debian Package of the Day',  'url': 'http://debaday.debian.net/feed/'},
         {'name': 'Slashdot',                   'url': 'http://rss.slashdot.org/Slashdot/slashdot'},
         {'name': 'KernelTrap',                 'url': 'http://kerneltrap.org/node/feed'},
         {'name': 'UK Terror Status',           'url': 'http://www.terror-alert.co.uk/feed/'},
         {'name': 'Open Rights Group',          'url': 'http://www.openrightsgroup.org/feed/'},
         {'name': 'Free Software Foundation',   'url': 'http://www.fsf.org/news/RSS'},
         {'name': 'Spyblog',                    'url': 'http://p10.hostingprod.com/@spyblog.org.uk/blog/atom.xml'},
         {'name': 'Ars Technica',               'url': 'http://feeds.arstechnica.com/arstechnica/BAaf'},
         {'name': 'Groklaw News Picks',         'url': 'http://www.groklaw.net/backend/GLNewsPicks.rdf'},
         {'name': 'Groklaw',                    'url': 'http://www.groklaw.net/backend/GrokLaw.rdf'}]

#feeds = [{'name': 'yahoo',  'url': 'http://rss.news.yahoo.com/rss/topstories', 'headline': headlines_title},
#         {'name': 'google', 'url': 'http://news.google.com/?output=rss', 'headline': headlines_title},
#         {'name': 'bbc',  'url': 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml', 'headlines': headlines_title}]

# IRC server
server = 'irc.uk.quakenet.org'
port = 6667
nick = 'anne'
channel = 'debian'

# end of configuration

def got_data (data, feed, announce):
    import feedparser
    data = feedparser.parse (data)

    if data.bozo == '1':
        log.msg ('%s: %s' % (feed['name'], data.bozo_exception))

    if len (data.entries) == 0:
        log.msg ('%s: 0 entries; ignoring' % (feed['name']))

    old_entries = feed.get ('entries', None)
    if feed.has_key ('headline'):
        new_entries = feed['headline'] (feed, data)
    else:
        new_entries = set (['%s (%s): <%s>' % (e.title, feed['name'], e.link) for e in data.entries])

    if old_entries != None:
        for e in new_entries.difference (old_entries):
            announce (e)
    feed['entries'] = new_entries

def got_error (failure, feed):
    #log.err ('%s: %s' % (url, failure.getErrorMessage ()))
    log.err ()
    return failure

def refresh_feeds (announce):
    from twisted.web.client import getPage

    for feed in feeds:
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
        self.bot.nickname = nick
        self.bot.realname = 'Announce Bot'
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

    factory = AnnounceBotFactory (channel)

    from twisted.internet import task
    l = task.LoopingCall (refresh_feeds, factory.announce)
    l.start (refresh_time)

    from twisted.internet import reactor
    reactor.connectTCP (server, port, factory)
    reactor.run ()

# vim: softtabstop=4 expandtab
