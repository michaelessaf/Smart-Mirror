# smartmirror.py
# requirements
# requests, feedparser, traceback, Pillow

from Tkinter import *
import locale
import threading
import time
import requests
import json
import traceback
import feedparser
import urllib
import os
from AnimatedGif import AnimatedGif
from PIL import Image, ImageTk
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
news_country_code = 'us'
weather_api_token = 'f790c1bd866b024679e147b43c2fb8b2' # create account at https://darksky.net/dev/
weather_lang = 'en' # see https://darksky.net/dev/docs/forecast for full list of language parameters values
weather_unit = 'us' # see https://darksky.net/dev/docs/forecast for full list of unit parameters values
latitude = None # Set this if IP location lookup does not work for you (must be a string)
longitude = None # Set this if IP location lookup does not work for you (must be a string)
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18
frames = []
weatherInd = 0

@contextmanager
def setlocale(name): #thread proof function to work with locale
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

# maps open weather icons to
# icon reading is not impacted by the 'lang' parameter
icon_lookup = {
    'clear-day': "assets/Sun.png",  # clear sky day
    'wind': "assets/Wind.png",   #wind
    'cloudy': "assets/Cloud.png",  # cloudy day
    'partly-cloudy-day': "assets/PartlySunny.png",  # partly cloudy day
    'rain': "assets/Rain.gif",  # rain day
    'snow': "assets/Snow.png",  # snow day
    'snow-thin': "assets/Snow.png",  # sleet day
    'fog': "assets/Haze.png",  # fog day
    'clear-night': "assets/Moon.png",  # clear sky night
    'partly-cloudy-night': "assets/PartlyMoon.png",  # scattered clouds night
    'thunderstorm': "assets/Storm.png",  # thunderstorm
    'tornado': "assests/Tornado.png",    # tornado
    'hail': "assests/Hail.png"  # hail
}


class oneBus(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.config(bg='black')
        self.transitContainer = Frame(self, bg="black")
        self.transitContainer.pack(side=TOP)
        for x in range (0, 3): #(len(transitText))):
            entry = TransitData(self.transitContainer, "Initializing...")
            entry.pack(side=TOP, anchor=W)
        self.get_oneBusData()


    def get_oneBusData(self):
        oneBusURL = "http://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/1_16480.json?&minutesAfter=60&key=5f44b6f4-fb7e-4c64-bd0f-2250b3cb4867"
        response = urllib.urlopen(oneBusURL)
        parsedOneBus= json.loads(response.read())
        #availRange = len(parsedOneBus['data']['entry']['arrivalsAndDepartures'])
        #availRange = min(availRange, 2)
        transitText = []

        #Puts string data into list
        for x in range (0, 3):#(availRange)):
            try:
                if (parsedOneBus['data']['entry']['arrivalsAndDepartures'] and parsedOneBus['data']['entry']['arrivalsAndDepartures'][x]['predictedArrivalTime'] != 0):
                    busTimeNearest = parsedOneBus['data']['entry']['arrivalsAndDepartures'][x]['predictedArrivalTime']
                    timeAway = int((float(busTimeNearest/1000) - time.time())/(60))
                    if (timeAway == 0):
                        transitText.append(" " + "NOW")

                    else:
                        transitText.append(" " + str(timeAway) + "m away")

                elif(parsedOneBus['data']['entry']['arrivalsAndDepartures']):
                    busTimeNearest = parsedOneBus['data']['entry']['arrivalsAndDepartures'][x]['scheduledArrivalTime']
                    timeAway = int((float(busTimeNearest/1000) - time.time())/(60))
                    if (timeAway == 0):
                        transitText.append(" " + "NOW *Scheduled")

                    else:
                        transitText.append(" " + str(timeAway) + "m away *Scheduled")

                else:
                    transitText.append(" ---")

            except:
                transitText.append(" ---")

        #updates widget with new list
        #print(str(transitText) + " =list")
        childrenW = self.transitContainer.winfo_children()
        for x in range (0, 3): #(len(transitText))):
            childrenW[x].eventNameLbl.config(text = (" " + transitText[x]))
            #print "test " + str(x)
        self.after(6000, self.get_oneBusData)


class TransitData(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/bus.png")
        image = image.resize((25, 25)) #, Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        # initialize time label
        self.time1 = ''
        self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        self.timeLbl.pack(side=TOP, anchor=E)
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dayOWLbl.pack(side=TOP, anchor=E)
        # initialize date label
        self.date1 = ''
        self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.dateLbl.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.config(text=date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timeLbl.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degreeFrm = Frame(self, bg="black")
        self.degreeFrm.pack(side=TOP, anchor=W)
        self.temperatureLbl = Label(self.degreeFrm, font=('Helvetica', xlarge_text_size), fg="white", bg="black")
        self.temperatureLbl.pack(side=LEFT, anchor=N)
        self.iconLbl = Label(self.degreeFrm, bg="black", image = '')
        self.iconLbl.pack(side=LEFT, anchor=S, padx=10)
        #self.currentlyLbl = Label(self, font=('Helvetica', medium_text_size), fg="white", bg="black")
        #self.currentlyLbl.pack(side=TOP, anchor=W)
        self.forecastLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.forecastLbl.pack(side=TOP, anchor=W)
        #self.locationLbl = Label(self, font=('Helvetica', small_text_size), fg="white", bg="black")
        #self.locationLbl.pack(side=TOP, anchor=W)
        self.get_weather()

    def get_ip(self):
        try:
            ip_url = "http://jsonip.com/"
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return "Error: %s. Cannot get ip." % e

    def get_weather(self):
        try:

            if latitude is None and longitude is None:
                # get location
                location_req_url = "http://freegeoip.net/json/%s" % self.get_ip()
                r = requests.get(location_req_url)
                location_obj = json.loads(r.text)

                lat = location_obj['latitude']
                lon = location_obj['longitude']

                location2 = "%s, %s" % (location_obj['city'], location_obj['region_code'])

                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, lat,lon,weather_lang,weather_unit)
            else:
                location2 = ""
                # get weather
                weather_req_url = "https://api.darksky.net/forecast/%s/%s,%s?lang=%s&units=%s" % (weather_api_token, latitude, longitude, weather_lang, weather_unit)

            r = requests.get(weather_req_url)
            weather_obj = json.loads(r.text)

            degree_sign= u'\N{DEGREE SIGN}'
            temperature2 = "%s%s" % (str(int(weather_obj['currently']['temperature'])), degree_sign)
            currently2 = weather_obj['currently']['summary']
            forecast2 = weather_obj["hourly"]["summary"]

            icon_id = weather_obj['currently']['icon']
            iconImg = None

            #get weather icon
            if icon_id in icon_lookup:
                iconImg = icon_lookup[icon_id]

            if iconImg is not None:
                if (True): #self.icon != iconImg:
                    global frames
                    frames = []
                    self.processImage("assets/Rain.gif")
                    print("frames len = " + str(len(frames)))

                    Photo = frames[0]
                    #im = im.resize((150,150), Image.ANTIALIAS)
                    #Photo = ImageTk.PhotoImage(im)

                    self.iconLbl.config(image=Photo)
                    self.iconLbl.image = Photo
                    self.after(0, self.update)
            else:
                # remove image
                self.iconLbl.config(image='')
                print("HELPPP")


            #weather text
            if self.currently != currently2:
                self.currently = currently2
                #self.currentlyLbl.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecastLbl.config(text=forecast2)
            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperatureLbl.config(text=temperature2)
            # if self.location != location2:
            #     if location2 == ", ":
            #         self.location = "Cannot Pinpoint Location"
            #         self.locationLbl.config(text="Cannot Pinpoint Location")
            #     else:
            #         self.location = location2
            #         self.locationLbl.config(text=location2)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get weather." % e

        self.after(600000, self.get_weather)

    @staticmethod
    def convert_kelvin_to_fahrenheit(kelvin_temp):
        return 1.8 * (kelvin_temp - 273) + 32

    def update(self):
        global weatherInd
        global frames

        if weatherInd == (len(frames)):
            weatherInd = 0
        Photo = frames[weatherInd]

        self.iconLbl.config(image=Photo)
        self.iconLbl.image = Photo

        weatherInd+=1

        self.after(20, self.update)

    def processImage(self, path):
        '''
        Iterate the GIF, extracting each frame.
        '''
        global frames

        mode = 'global'

        im = Image.open(path)

        i = 0
        p = im.getpalette()
        last_frame = im.convert('RGBA')

        try:
            while True:
                print "saving %s (%s) frame %d, %s %s" % (path, mode, i, im.size, im.tile)

                '''
                If the GIF uses local colour tables, each frame will have its own palette.
                If not, we need to apply the global palette to the new frame.
                '''
                if not im.getpalette():
                    im.putpalette(p)

                new_frame = Image.new('RGBA', im.size)

                '''
                Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
                If so, we need to construct the new frame by pasting it on top of the preceding frames.
                '''
                if mode == 'partial':
                    new_frame.paste(last_frame)

                new_frame.paste(im, (0,0), im.convert('RGBA'))


                new_frame = new_frame.resize((100,100), Image.ANTIALIAS)
                Photo = ImageTk.PhotoImage(new_frame)
                frames.append(Photo)

                i += 1
                last_frame = new_frame
                im.seek(im.tell() + 1)
        except EOFError:
            pass

class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News' # 'News' is more internationally generic
        self.newsLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.newsLbl.pack(side=TOP, anchor=W)
        self.headlinesContainer = Frame(self, bg="black")
        self.headlinesContainer.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            # remove all children
            for widget in self.headlinesContainer.winfo_children():
                widget.destroy()
            if news_country_code != None:
                headlines_url = "http://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
            else:
                headlines_url = "https://news.google.com/news?ned=%s&output=rss" % news_country_code

            feed = feedparser.parse(headlines_url)

            for post in feed.entries[0:5]:
                headline = NewsHeadline(self.headlinesContainer, post.title)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s. Cannot get news." % e

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=""):
        Frame.__init__(self, parent, bg='black')

        image = Image.open("assets/Newspaper.png")
        image = image.resize((25, 25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.iconLbl = Label(self, bg='black', image=photo)
        self.iconLbl.image = photo
        self.iconLbl.pack(side=LEFT, anchor=N)

        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=LEFT, anchor=N)


class Calendar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.title = 'Calendar Events'
        self.calendarLbl = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg="white", bg="black")
        self.calendarLbl.pack(side=TOP, anchor=E)
        self.calendarEventContainer = Frame(self, bg='black')
        self.calendarEventContainer.pack(side=TOP, anchor=E)
        self.get_events()

    def get_events(self):
        #TODO: implement this method
        # reference https://developers.google.com/google-apps/calendar/quickstart/python

        # remove all children
        for widget in self.calendarEventContainer.winfo_children():
            widget.destroy()

        calendar_event = CalendarEvent(self.calendarEventContainer)
        calendar_event.pack(side=TOP, anchor=E)
        pass


class CalendarEvent(Frame):
    def __init__(self, parent, event_name="Event 1"):
        Frame.__init__(self, parent, bg='black')
        self.eventName = event_name
        self.eventNameLbl = Label(self, text=self.eventName, font=('Helvetica', small_text_size), fg="white", bg="black")
        self.eventNameLbl.pack(side=TOP, anchor=E)


class FullscreenWindow:

    def __init__(self):
        self.tk = Tk()
        self.tk.configure(background='black')
        self.topFrame = Frame(self.tk, background = 'black')
        self.bottomFrame = Frame(self.tk, background = 'black')
        self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
        self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
        self.state = False
        self.tk.bind("<Return>", self.toggle_fullscreen)
        self.tk.bind("<Escape>", self.end_fullscreen)
        # clock
        self.weather = Weather(self.topFrame)
        self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
        self.clock = Clock(self.topFrame)
        self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
        # weather

        # news
        #self.news = News(self.bottomFrame)
        #self.news.pack(side=LEFT, anchor=S, padx=100, pady=60)

        self.oneBus = oneBus(self.bottomFrame)
        self.oneBus.pack(side=LEFT, anchor=S, padx=100, pady=60)
        # calender - removing for now
        # self.calender = Calendar(self.bottomFrame)
        # self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.tk.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes("-fullscreen", False)
        return "break"

if __name__ == '__main__':
    w = FullscreenWindow()
    w.tk.mainloop()
