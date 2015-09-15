import os
from bs4 import BeautifulSoup
import glob
import unicodedata
import operator

#set these to True to download the html.  No need to download multiple times
downloadYears = False
downloadShows = False
populateSetlistDict = True

def remove_unicode(s):
    return unicodedata.normalize('NFKD', s).encode('ascii','ignore')

#convert a string from mm:ss to number of seconds
def get_seconds(t):
    #separate minutes and seconds
    timeArray = t.split(":")

    if len(timeArray) != 2:
        return 0

    minutes = int(timeArray[0])
    seconds = int(timeArray[1])

    #calculate seconds
    return minutes * 60 + seconds

#convert seconds to time string in form of mm:ss
def seconds_to_time_string(s):
    #this returns a tuple in the form of (minutes, seconds)
    time = divmod(s,60)
    #create string, add leading zero for seconds, if necessary
    return "{0}:{1}".format(str(time[0]), str(time[1]).zfill(2))

#class for a single set of songs
class SetEntry:

    def __init__(self):
        self.times = []
        self.name = ""

    def average_song_time(self):
        average = 0

        if len(self.times) > 0:
            average = int(round((self.set_length()/len(self.times))))
        return average

    def set_length(self):
        total = 0
        for t in self.times:
            total += get_seconds(t)
        return total


#class for a single show
class ShowEntry:

    def __init__(self, d):
        self.date = d
        self.sets = []

    def get_total_length(self):
        total_length = 0
        for s in self.sets:
            total_length += s.set_length()
        return total_length

baseAddress = "www.phishtracks.com/shows/"

validYears = range(1988,2016)

#download html of a full year of setlists
if downloadYears:
    for year in validYears:
        #create url
        yearURL = "{0}{1}".format(baseAddress, str(year))

        #download url, and store in a file
        os.system("curl {0} > {1}.html".format(yearURL, str(year)))

    #83-87 is a special case
    yearURL = "{0}83-87".format(baseAddress)
    os.system("curl {0} > 1987.html".format(yearURL))

validYears = range(1987, 2016)

if downloadShows:
    for year in validYears:

        #make directory if it doesn't exist yet
        if(str(year) not in os.listdir(".")):
            os.system("mkdir " + str(year))

        #parse the html
        soup = BeautifulSoup(open("{0}.html".format(str(year))), "lxml")

        #links to each show are in <li> tags
        dateLIs = soup.find_all('li')


        for item in dateLIs:
            link = item.a
            if link.has_attr('href'):
                #extract the date from the link
                date = str(link['href']).split("/")[2]

                #make the full url of the show
                setlistLink = baseAddress + date

                #each year page has links to all other years, filter these out
                if len(date) == 10:
                    #download the show, save it in a file
                    os.system("curl {0} > ./{1}/{2}.html".format(setlistLink, str(year), date))

showList = []

if populateSetlistDict:
    for year in validYears:
    #get list of files in each year folder
        folder = "./{0}/*".format(year)
        fileList = glob.glob(folder)

        for fileName in fileList:
            #parse html
            soup = BeautifulSoup(open(fileName), "lxml")

            #extract date from file name
            date = str(fileName[7:17])

            #create a new showentry object
            show = ShowEntry(date)

            #both set names and songs are in <li> tags
            items = soup.find_all('li')

            #declare variable, but dont put anything in it yet
            songs = None

            for item in items:
                #set names have a class attribute
                if item.has_attr("class"):
                    #make a new SetEntry
                    songs = SetEntry()
                    #get the name of the set
                    setTitle = remove_unicode(item.h2.contents[0])
                    #store the set in the show object
                    show.sets.append(songs)
                    #store the name of the set in the set object
                    songs.name = setTitle
                #songs have data-id attributes
                elif item.has_attr("data-id"):
                    #the duration is in a <span> tag with a class called duration
                    times = item.find_all('span', attrs={'class' : 'duration'})
                    for t in times:
                        #remove white space from time string
                        time = remove_unicode(t.contents[0]).strip(' \t\n\r')
                        #store the time in the set object
                        songs.times.append(str(time))
            #add the show to the show list
            showList.append(show)

    #sort by total length
    sorted_lengths = sorted(showList, key=lambda x: x.get_total_length(), reverse=True)

    #create output file
    with open("showLength.txt", "w") as out_file:
        for s in sorted_lengths:
            out_file.write(s.date + ": " + seconds_to_time_string(s.get_total_length()) + "\n")

    #create list to store average lengths
    averageLengthList = []

    #average song length
    for show in showList:
        for s in show.sets:
            #set this to "Set 1", "Set 2", "Set 3", "Set 4", or "Encore"
            if s.name == "Set 1":
                song_count = len(s.times)
                #dont include sets with only one song
                if song_count > 1:
                    #get average length of song in this set
                    average = s.average_song_time()
                    #create name for this set
                    name = "{0} {1}".format(show.date, s.name)
                    #add entry to the list
                    averageLengthList.append((name, average, song_count))

    #sort list of sets by average length of song
    sorted_average = sorted(averageLengthList, key=operator.itemgetter(1), reverse=True)

    #create another output file
    with open("averageSongLength.txt", "w") as out_file:
        for index, average_tuple in enumerate(sorted_average):
            song_count = average_tuple[2]
            date_and_set = average_tuple[0]
            average_song_length = str(seconds_to_time_string(average_tuple[1]))
            out_file.write("{0}. {1}: {2} - {3} songs\n".format(index, date_and_set, average_song_length, song_count))







