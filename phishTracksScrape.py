import os
from bs4 import BeautifulSoup
import glob
import unicodedata
import operator


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
    return str(time[0]) + ":" + str(time[1]).zfill(2)

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

#set these to True to download the html.  No need to download multiple times
downloadYears = False
downloadShows = False
populateSetlistDict = True


baseAddress = "www.phishtracks.com/shows/"

validYears = range(1988,2016)

#download html of a full year of setlists
if downloadYears:
    for year in validYears:
        #create url
        yearURL = baseAddress +str(year)

        #download url, and store in a file
        os.system("curl " + yearURL + " > " + str(year) + ".html")

    #83-87 is a special case
    yearURL = baseAddress + "83-87"
    os.system("curl " + yearURL + " > " + "1987.html")

validYears = range(1987, 2016)

if downloadShows:
    for year in validYears:

        #make directory if it doesn't exist yet
        if(str(year) not in os.listdir(".")):
            os.system("mkdir " + str(year))

        #parse the html
        soup = BeautifulSoup(open(str(year) + ".html"), "lxml")

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
                    os.system("curl " + setlistLink + " > ./" + str(year) + "/" + date + ".html")

showList = []

if populateSetlistDict:
    for year in validYears:
    #get list of files in each year folder
        folder = "./" + str(year) + "/*"
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
    out_file = open("showLength.txt", "w")

    #write output to file
    for s in sorted_lengths:
        out_file.write(s.date + ": " + seconds_to_time_string(s.get_total_length()) + "\n")

    #close file
    out_file.close()

    #create list to store average lengths
    averageLengthList = []

    #average song length
    for show in showList:
        for s in show.sets:

            #set this to "Set 1", "Set 2", "Set 3", "Set 4", or "Encore"
            if s.name == "Encore":
                #get average length of song in this set
                average = s.average_song_time()
                #create name for this set
                name = show.date + " " + s.name
                #add entry to the list
                averageLengthList.append((name, average, len(s.times)))

    #sort list of sets by average length of song
    sorted_average = sorted(averageLengthList, key=operator.itemgetter(1), reverse=True)

    index = 1

    #create another output file
    out_file = open("averageSongLength.txt", "w")

    #write the output
    for a in sorted_average:
        out_file.write(str(index) + ". " + a[0] + ": " + str(seconds_to_time_string(a[1])) + " - " + str(a[2]) + " songs" + "\n")
        index += 1

    #close the file
    out_file.close()





