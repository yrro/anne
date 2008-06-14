# A sequence of dicts that describe feeds. The following keys should be present in each dict:
#   name: an identifier for the feed, displayed when the bot speaks an entry
#   url: rss/atom feed URL
#   headline (optional): a function that transforms a feed entry into text that the bot will speak.
#                        can be 'headline_default', 'headline_summary' or 'headline_title'.
feeds = [{'name': 'debian-security-announce',   'url': 'http://www.debian.org/security/dsa', 'headline': 'headline_summary'},
         {'name': 'debian-infrastructure-announce', 'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.infrastructure.announce'},
         {'name': 'debian-news',                'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.news'},
         {'name': 'debian-devel-announce',      'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.devel.announce'},
         {'name': 'debian-announce',            'url': 'http://rss.gmane.org/messages/excerpts/gmane.linux.debian.user.announce'},
         {'name': 'debian-administration.org',  'url': 'http://www.debian-administration.org/atom.xml'},
         {'name': 'debianhelp.org',             'url': 'http://www.debianhelp.org/rss.xml'},
         {'name': 'LWN',                        'url': 'http://lwn.net/headlines/rss'},
         {'name': 'lugradio',                   'url': 'http://lugradio.org/episodes.ogg.rss'},
         #{'name': 'Planet Debian',              'url': 'http://planet.debian.org/rss20.xml'},
         {'name': 'Debian Times',               'url': 'http://times.debian.net/?format=rss20.xml'},
         {'name': 'Debian Package of the Day',  'url': 'http://debaday.debian.net/feed/'},
         #{'name': 'Slashdot',                   'url': 'http://rss.slashdot.org/Slashdot/slashdot'},
         {'name': 'KernelTrap',                 'url': 'http://kerneltrap.org/node/feed'},
         {'name': 'UK Terror Status',           'url': 'http://www.terror-alert.co.uk/feed/'},
         {'name': 'Open Rights Group',          'url': 'http://www.openrightsgroup.org/feed/'},
         {'name': 'Free Software Foundation',   'url': 'http://www.fsf.org/news/RSS'},
         {'name': 'Spyblog',                    'url': 'http://p10.hostingprod.com/@spyblog.org.uk/blog/atom.xml'},
         {'name': 'Ars Technica',               'url': 'http://feeds.arstechnica.com/arstechnica/BAaf'},
         {'name': 'Groklaw News Picks',         'url': 'http://www.groklaw.net/backend/GLNewsPicks.rdf'},
         {'name': 'Groklaw',                    'url': 'http://www.groklaw.net/backend/GrokLaw.rdf'},
         {'name': 'xkcd',                       'url': 'http://xkcd.com/atom.xml'}]


# Often-updated feeds, useful for testing:
#feeds = [{'name': 'yahoo',  'url': 'http://rss.news.yahoo.com/rss/topstories', 'headline': 'headline_title'},
#         {'name': 'google', 'url': 'http://news.google.com/?output=atom', 'headline': 'headline_title'},
#         {'name': 'bbc',  'url': 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml', 'headlines': 'headline_title'}]

# IRC server information.
host = 'irc.example'
port = 6667
nick = 'anne'
channel = 'somechannel' # without initial hash

# The bot will refresh feeds and speak at this interval:
refresh_time = 60 * 60 # seconds
