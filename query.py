from urllib.request import urlopen as urlopen
from pprint import pprint, pformat
from time import sleep
from datetime import datetime
import re
import os
import json

SONG_LIST_START = 'var songlist = ['
PATH = os.getcwd()

def getTimeNow():
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M')

class AZLyricsCrowler:
    URL = "http://www.azlyrics.com/"

    def __init__(self):
        self.singers = {}
        self.songs = {}
        self.lyrics = {}
        self.singers_change = False
        self.songs_change = False
        self.lyrics_change = False

    def getAllSinger(self):
        for w in "abcdefghijklmnopqrstuvwxyz":
            self.getSingerByWord(w)
            print(".", end="")
            sleep(5)

        self.getSingerByWord("19")

    def getAllSingerGentle(self):
        for w in "abcdefghijklmnopqrstuvwxyz":
            self.getSingerByWord(w)

        self.getSingerByWord("19")

    def getLimitedSingersSongGentle(self, limit=50):
        count = 0
        fail_count = 0
        searched_list = []
        for singer in self.singers:
            if singer in self.songs:
                continue
            if count >= limit:
                break
            try:
                self.getAllSongBySinger(self.singers[singer])
                searched_list.append(singer)
                sleep(1)
            except:
                fail_count += 1
            count += 1
        print("Total: %i Failed %i" % (count, fail_count))
        for search in searched_list:
            print(search)

    def getSingerByWord(self, word):
        r = urlopen(AZLyricsCrowler.URL + word + ".html")

        if r.code >= 400:
            raise Exception("Signer who name is start with %s not Exists" % word)

        html = str(r.read())
        r.close()

        singers_html = html[html.find("<!-- main -->"):]
        singers_html = singers_html[singers_html.find("<a"):]
        singers_html = singers_html[:singers_html.find("<!-- container main-page -->")]

        find = singers_html.find("href=")
        while find != -1:
            url = AZLyricsCrowler.URL + singers_html[find + 6:singers_html.find('">', find)]
            singer = singers_html[singers_html.find('">', find) + 2:singers_html.find("<", find)]
            self.singers[singer] = url
            self.singers_change = True

            find = singers_html.find("href=", find + 1)
            sleep(5)

    def getAllSongBySinger(self, url):
        r = urlopen(url)

        if r.code >= 400:
            raise Exception("Song url not Exists")

        html = str(r.read())
        r.close()

        title = html[html.find("<title>") + 7:html.find("</title>")]
        singer = title.replace(" lyrics", "")

        song_list = html[html.find(SONG_LIST_START) + len(SONG_LIST_START) - 1:]
        song_list = song_list[:song_list.find("];") + 1]

        # remove useless character
        song_list = song_list.replace("'", '"')
        song_list = song_list.replace("\\n", "")
        song_list = song_list.replace("\\r", "")
        song_list = song_list.replace("\\t", "")
        song_list = song_list.replace("s:", "\"s\":")
        song_list = song_list.replace("a:", "\"a\":")
        song_list = song_list.replace("c:", "\"c\":")
        song_list = song_list.replace("h:", "\"h\":")

        song_list = json.loads(song_list)
        singer_dict = []
        for song in song_list:
            singer_dict.append({
                "url": song["h"].replace("../", AZLyricsCrowler.URL),
                "name": song["s"]
                })
        self.songs[singer] = singer_dict
        self.songs_change = True

    def getSongByUrl(self, url):
        r = urlopen(url)

        if r.code >= 400:
            raise Exception("Song url not Exists")

        html = str(r.read())
        r.close()

        title = html[html.find("<title>") + 7:html.find("</title>")]
        singer, name = title.split(" - ")
        singer = singer.replace(" LYRICS", "")

        # remove useless character
        lyric = html[html.find("<div>") + 5:]
        lyric = lyric[:lyric.find("</div>")]
        lyric = lyric.replace("<br>", "")
        lyric = lyric.replace("\\n", "\n")
        lyric = lyric.replace("\\r", "")
        lyric = lyric.replace("\\t", "")
        lyric = lyric.replace("\\'", "'")
        lyric = lyric.replace(",", "")
        lyric = lyric.replace("?", "")

        lyric = re.sub("<!--.+-->",
            "",
            lyric)

        songinfo = {
            "url": url,
            "singer": singer,
            "name": name,
            "lyric": lyric
        }

        # build song's index
        lyric = lyric.replace("\n", " ")
        lyric = lyric.lower()
        lyric = lyric.split()

        word_index = {} 
        for word in lyric:
            if word not in word_index:
                word_index[word] = 0
            word_index[word] += 1
        songinfo["index"] = word_index
        
        if singer not in self.lyrics:
            self.lyrics[singer] = {}
        self.lyrics[singer][url] = songinfo
        self.lyrics_change = True

    def readSigners(self):
        try:
            with open("singers.txt") as file:
                read = file.read()
                file.close()

                singer_list = read.split("\n")
                for singer in singer_list:
                    if singer == "":
                        continue
                    singer_, url = singer.split("|||||")

                    self.singers[singer_] = url
        except:
            raise Exception("Signer Read Error")

    def saveSigners(self):
        try:
            if self.singers_change:
                # make copy of last version
                time = getTimeNow()
                os.rename(PATH + "/singers.txt", PATH + "/history/singers %s.txt" % time)

                txt = ""
                for singer in self.singers:
                    txt += "%s|||||%s\n" % (singer, self.singers[singer])
                with open("singers.txt", "w") as file:
                    file.write(txt)
                print("Signers Saved Success")
            else:
                # do nothing if songs didn't change
                print("Singers Haven Change")
        except:
            print("Singer Save Error")

    def readSongs(self):
        try:
            with open("songs.txt") as file:
                read = file.read()
                file.close()

                song_list = read.split("\n")
                for song in song_list:
                    if song == "":
                        continue
                    singer, url, name = song.split("|||||")

                    if singer not in self.songs:
                        self.songs[singer] = []

                    self.songs[singer].append({
                        "url": url,
                        "name": name
                        })
        except:
            raise Exception("Songs Read Error")

    def saveSongs(self):
        try:
            if self.songs_change:
                # make copy of last version
                time = getTimeNow()
                os.rename(PATH + "/songs.txt", PATH + "/history/songs %s.txt" % time)

                txt = ""
                for singer in self.songs:
                    for song in self.songs[singer]:
                        txt += "%s|||||%s|||||%s\n" % (singer, song["url"], song["name"])
                with open("songs.txt", "w") as file:
                    file.write(txt)
                print("Songs Saved Success")
            else:
                # do nothing if songs didn't change
                print("Songs Haven Change")
        except:
            print("Error")  

    # def saveLyrics(self):
    #     if self.lyrics_change:
    #         try:
    #             for singer in self.lyrics:
    #                 if not os.path.isdir("lyrics/" + singer):
    #                     os.mkdir("lyrics/" + singer)
    #                 for song in self.lyrics[singer].values():

    def readLyrics(self):
        paths = []
        for i, j, k in os.walk("lyrics"):
            for e in k:
                if e.endswith("txt"):
                    file = open("%s/%s" % (i, e))
                    read = file.read()
                    file.close()
                    l = read.split("\n")

                    url = l[0]
                    name = l[1]
                    singer = l[2]
                    lyric = l[3]
                    index_list = l[4:]
                    index = {}
                    for word in index_list:
                        w, count = word.split()
                        index[w] = count

                    songinfo = {
                        "url": url,
                        "singer": singer,
                        "name": name,
                        "lyric": lyric,
                        "index": index,
                    }

                    if singer not in self.lyrics:
                        self.lyrics[singer] = {}
                    self.lyrics[singer][url] = songinfo


class MusixMatchScrowler:
    URL = "https://www.musixmatch.com"
    LYRIC_START = '<p class="mxm-lyrics__content" data-reactid="141">'
    TITLE_START = '<title data-react-helmet="true">'

    def __init__(self):
        self.singers = set()

    def getSongByUrl(self, url):
        r = urlopen(url)

        if r.code >= 400:
            raise Exception("Song url not Exists")

        html = str(r.read())
        r.close()

        lyric_start = html.find(LYRIC_START)
        title = html[TITLE_START + len(TITLE_START):html.find("</title>")]

        singer, name = title.split(" - ")
        singer = singer.upper()

        name = name[:name.find(" Lyrics")]

        lyric = html[lyric_start + len(LYRIC_START):]
        lyric = lyric[:lyric.find("</p>")]
        lyric = lyric.replace("<br>", "")
        lyric = lyric.replace("\\n", "\n")
        lyric = lyric.replace("\\r", "")
        lyric = lyric.replace("\\t", "")
        lyric = lyric.replace("\\'", "'")
        lyric = lyric.replace(",", "")

        songinfo = {
            "singer": singer,
            "name": name,
            "lyric": lyric
        }

        lyric = lyric.replace("\n", " ")
        lyric = lyric.lower()
        lyric = lyric.split()

        word_index = {} 
        for word in lyric:
            if word not in word_index:
                word_index[word] = 0
            word_index[word] += 1
        songinfo["index"] = word_index
        print(songinfo)

if __name__ == "__main__":
    crowler = AZLyricsCrowler()
    crowler.readSongs()

    crowler.readLyrics()
    # crowler.getSongByUrl("http://www.azlyrics.com/lyrics/coldplay/vivalavida.html")
    pprint(crowler.lyrics["COLDPLAY"]["http://www.azlyrics.com/lyrics/coldplay/vivalavida.html"])

# if __name__ == "__main__":
#     crowler = AZLyricsCrowler()
#     crowler.readSigners()
#     crowler.readSongs()

#     try:
#         crowler.getLimitedSingersSongGentle(limit=5)
#     except:
#         pass
#     count = 0
#     for i in crowler.songs:
#         count += len(crowler.songs[i])
#     print("%i Singers Get" % len(crowler.songs))
#     print("%i Songs" % count)
#     print("%i Singers Left" % (len(crowler.singers) - len(crowler.songs)))
#     crowler.saveSigners()
#     crowler.saveSongs()
