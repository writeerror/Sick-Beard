# Author: Robert Massa <robertmassa@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is based upon tvtorrents.py.
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import sickbeard
import generic

from sickbeard import helpers, exceptions, tvcache
import StringIO, zlib, gzip

import urllib, urllib2
import socket

import traceback

from httplib import BadStatusLine

from sickbeard import logger, classes
from sickbeard.common import USER_AGENT




urllib._urlopener = classes.SickBeardURLopener()

class TorrentBytesProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "TorrentBytes")

        self.supportsBacklog = False
        self.cache = TorrentBytesCache(self)
        self.url = 'http://www.TorrentBytes.net/'

    def isEnabled(self):
        return sickbeard.TORRENTBYTES

    def imageName(self):
        return 'torrentbytes.png' 
    
    def getURL (self, url, headers=[]):
        """
        Returns a byte-string retrieved from the url provider.
        """
    
    
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', USER_AGENT),
                             ('Accept-Encoding', 'gzip,deflate'),
                             ('Cookie', 'uid='+sickbeard.TORRENTBYTES_UID +"; pass="+sickbeard.TORRENTBYTES_PASS)]
    
        
        for cur_header in headers:
            opener.addheaders.append(cur_header)
    
        try:
            usock = opener.open(url)
            url = usock.geturl()
            encoding = usock.info().get("Content-Encoding")
    
            if encoding in ('gzip', 'x-gzip', 'deflate'):
                content = usock.read()
                if encoding == 'deflate':
                    data = StringIO.StringIO(zlib.decompress(content))
                else:
                    data = gzip.GzipFile('', 'rb', 9, StringIO.StringIO(content))
                result = data.read()
    
            else:
                result = usock.read()
    
            usock.close()
    
        except urllib2.HTTPError, e:
            logger.log(u"HTTP error " + str(e.code) + " while loading URL " + url, logger.WARNING)
            return None
        except urllib2.URLError, e:
            logger.log(u"URL error " + str(e.reason) + " while loading URL " + url, logger.WARNING)
            return None
        except BadStatusLine:
            logger.log(u"BadStatusLine error while loading URL " + url, logger.WARNING)
            return None
        except socket.timeout:
            logger.log(u"Timed out while loading URL " + url, logger.WARNING)
            return None
        except ValueError:
            logger.log(u"Unknown error while loading URL " + url, logger.WARNING)
            return None
        except Exception:
            logger.log(u"Unknown exception while loading URL " + url + ": " + traceback.format_exc(), logger.WARNING)
            return None
    
        return result


class TorrentBytesCache(tvcache.TVCache):

    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll every 15 minutes
        self.minTime = 15

    def _getRSSData(self):

        if not sickbeard.TORRENTBYTES_URL:
            raise exceptions.AuthException("TorrentBytes requires an RSS URL to work correctly")

        url = sickbeard.TORRENTBYTES_URL
        logger.log(u"TorrentBytes cache update URL: " + url, logger.DEBUG)

        data = self.provider.getURL(url)

        return data

    def _parseItem(self, item):
        description = helpers.get_xml_text(item.getElementsByTagName('description')[0])

        if "wrong passkey or username" in description:
            raise exceptions.AuthException("TorrentBytes URL invalid")

        (title, url) = self.provider._get_title_and_url(item)


        if not title or not url:
            logger.log(u"The XML returned from the Torrentbytes RSS feed is incomplete, this result is unusable", logger.ERROR)
            return

        logger.log(u"Adding item from RSS to cache: " + title, logger.DEBUG)

        self._addCacheEntry(title, url)

provider = TorrentBytesProvider()
