#!/usr/bin/python3

import configparser
import feedparser
from os.path import isfile, isdir, dirname, join
import datetime
import requests
import urllib.parse

def logger(logthis):
    #print(str(logthis))
    with open(join(dirname(__file__), 'log.txt'), 'a') as logfile:
        logfile.write(str(logthis) + '\n')
    return

def errorExit():
    #input('\nPress the Enter key to exit')
    print('Failed.')
    exit(1)

class RSS_downloader:
    def __init__(self):
        logger(' -- ' + datetime.datetime.now().isoformat(' ') + ' -- ')
        self.readConfig()

    def findConfig(self):
        configFile = 'config.ini'

        if isfile(configFile):
            return configFile

        if isfile(join(dirname(__file__), configFile)):
            return join(dirname(__file__), configFile)

        logger('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')
        print('Failed to read configuration file. Are you sure there is a file called "config.ini"?\n')
        errorExit()
        return

    def readConfig(self):
        logger("Reading config.")
        configFile = self.findConfig()
        config = configparser.ConfigParser()
        config.read(configFile)
        myconfig = config['RSS-downloader']
        logger(myconfig)

        try:
            self.URL1 = myconfig['URL1']
            self.OUTPUT_DIR = myconfig['OUTPUT_DIR']
            self.RSS_DOWNLOADS_FILE = myconfig['RSS_DOWNLOADS_FILE']
            self.WANTED_SHOWS_FILE = myconfig['WANTED_SHOWS_FILE']
        except Exception:
            print('Failed to parse configuration file. Is it broken?\n')
            errorExit()

        if not isfile(self.RSS_DOWNLOADS_FILE):
            if not isfile(join(dirname(__file__), self.RSS_DOWNLOADS_FILE)):
                print('Failed to read list of downloaded files.\n')
                self.RSS_DOWNLOADS_FILE = join(dirname(__file__), self.RSS_DOWNLOADS_FILE)
                logger('Creating new downloads list: ' + self.RSS_DOWNLOADS_FILE + '\n')
                print('Creating new downloads list: ' + self.RSS_DOWNLOADS_FILE + '\n')
            else:
                self.RSS_DOWNLOADS_FILE = join(dirname(__file__), self.RSS_DOWNLOADS_FILE)


        if not isfile(self.WANTED_SHOWS_FILE):
            if not isfile(join(dirname(__file__), self.WANTED_SHOWS_FILE)):
                print('Failed to read list of files to download.\n')
                errorExit()
            else:
                self.WANTED_SHOWS_FILE = join(dirname(__file__), self.WANTED_SHOWS_FILE)

        self.OUTPUT_DIR = dirname(self.OUTPUT_DIR)

        if not isdir(self.OUTPUT_DIR):
            print("Output dir doesn't exist: " + self.OUTPUT_DIR)
            errorExit()

        self.WANTED_SHOWS = []

        with open(self.WANTED_SHOWS_FILE, 'r') as tempfile:
            for show in tempfile.read().splitlines():
                show = show.strip()
                if len(show) < 3 or show.startswith == "#":
                    continue
                self.WANTED_SHOWS.append(show)

        logger('URL1: ' + self.URL1)
        logger('OUTPUT_DIR: ' + self.OUTPUT_DIR)
        logger('RSS_DOWNLOADS_FILE: ' + self.RSS_DOWNLOADS_FILE)
        logger('WANTED_SHOWS_FILE: ' + self.WANTED_SHOWS_FILE)
        logger(self.WANTED_SHOWS)
        return

    def hasFileBeenDownloaded(self, filename, url):
        if url.startswith('https://') and url.endswith('.torrent'):
            filename = urllib.parse.unquote(url).split('/')[-1]
            if filename.endswith('.torrent'):
                filename = filename[0:len(filename) - 8]
        with open(self.RSS_DOWNLOADS_FILE, 'r') as fin:
            for line in fin:
                line = line.strip()
                if line == filename:
                    return True
        return False

    def isShowWanted(self, showName):
        for wantedShow in self.WANTED_SHOWS:
            if showName.find(wantedShow) >= 0:
                return True
        return False

    def downloadMirrorLink(self, filename, mirrorLink):
        logger("To download: " + filename + '\n\n' + mirrorLink + '\n')
        torrentContent = 'd10:magnet-uri' + str(len(mirrorLink)) + ':' + mirrorLink + 'e'
        #logger("torrentContent: " + torrentContent + '\n')
        torrentFile = join(self.OUTPUT_DIR, filename + '.torrent')
        logger("Writing to: " + torrentFile)
        if not isfile(torrentFile):
            with open(torrentFile, 'x') as newTorrentFile:
                newTorrentFile.write(torrentContent)
                print("Saved: " + torrentFile)
        else:
            print('File exists: ' + torrentFile)
        with open(self.RSS_DOWNLOADS_FILE, 'a') as downloaded:
            downloaded.write(filename + '\n')
        return

    def downloadTorrentLink(self, filename, torrentLink):
        filename = urllib.parse.unquote(torrentLink).split('/')[-1]
        logger("To download: " + filename + '\n\n' + torrentLink + '\n')
        r = requests.get(torrentLink)
        r.raise_for_status()
        torrentContent = r.content
        #logger("torrentContent: " + torrentContent + '\n')
        torrentFile = join(self.OUTPUT_DIR, filename)
        logger("Writing to: " + torrentFile)
        if not isfile(torrentFile):
            with open(torrentFile, 'xb') as newTorrentFile:
                newTorrentFile.write(torrentContent)
                print("Saved: " + torrentFile)
        else:
            print('File exists: ' + torrentFile)
        with open(self.RSS_DOWNLOADS_FILE, 'a') as downloaded:
            if filename.endswith('.torrent'):
                filename = filename[0:len(filename) - 8]
            downloaded.write(filename + '\n')
        return

    def downloadLink(self, filename, link):
        if link.startswith('magnet:?xt=urn:btih:'):
            self.downloadMirrorLink(filename, link)
        elif link.startswith('https://') and link.endswith('.torrent'):
            self.downloadTorrentLink(filename, link)
        else:
            logger("Don't know what to do with download link: " + link)
        return

    def processFeed(self, url):
        d = feedparser.parse(url)
        if d.bozo > 0:
            logger('Failed to parse feed: ' + url)
            logger(d.bozo_exception)
            print('Failed to parse feed: ' + url)
            print(d.bozo_exception)
            errorExit()
        for ep in d.entries:
            if self.isShowWanted(ep.title):
                logger("Matched: " + ep.title)
                if not self.hasFileBeenDownloaded(ep.title, ep.link):
                    logger("Downloading: " + ep.title + " at " + ep.link)
                    self.downloadLink(ep.title, ep.link)
        return

    def run(self):
        logger('Running first RSS.')
        self.processFeed(self.URL1)
        return

def main():
    downloader = RSS_downloader()
    downloader.run()
    return

if __name__ == "__main__":
    # execute only if run as a script
    main()
