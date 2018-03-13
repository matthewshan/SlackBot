from slackclient import SlackClient
from time import sleep
from pprint import pprint
import traceback
from sys import exit
from os import environ
import json
import requests
import praw
import random

class Bot(object):
    prefix = '!'
    #contructor, called when an instance is created
    def __init__(self):
        self.username = None
        self.userid = None
        self.teamid = None
        self.token = None
        self.slackclient = None

    def echo(self, text, channel):
            self.slackclient.api_call(
            'chat.postMessage',
            channel=channel,
            text=text
            )

    def getToken(self, filename):
        try:
            tokenFile = open('tokens/' + filename, 'r')
            token = tokenFile.read().rstrip()
            tokenFile.close()
        except IOError:
            print('Failed to retrieve token from ' + filename)
            exit(1)
        return token

    def connect(self):
        self.token = self.getToken('token.txt')
        self.slackclient = SlackClient(self.token)
        print('Attempting to connect...')
        if(self.slackclient.rtm_connect()):
            print('Connection successful!')
            return True
        else:
            print('Failed to connect')
            return False

    def setUserID(self):
        print('Retrieving self ID...')
        data = self.slackclient.api_call('auth.test')
        self.userid = data['user_id']

    def getWeather(self,zip):
        print('Accessing OpenWeatherMapAPI with token')
        weatherToken = self.getToken('weather.txt')
        weatherAddress = 'http://api.openweathermap.org/data/2.5/forecast?zip=' + str(zip) + ',us&APPID=' + weatherToken

        print('Retrieving JSON Data ')
        weatherJSON = requests.get(weatherAddress).json()
        if weatherJSON['cod'] != '200':
            print(weatherJSON)
            return ("Uh oh... There seems to be a problem retrieving weather info for the entered ZIP Code")

        weatherTemp = str(round((weatherJSON['list'][0]['main']['temp']) * (9/5) - 459.67))
        weatherStatus = weatherJSON['list'][0]['weather'][0]['main']
        location = weatherJSON['city']['name'] + ', ' + weatherJSON['city']['country']
        return ('Here is the current weather in ' + location + ', ' + str(zip) + ':\n>>>The temperature is `' + weatherTemp + ' degrees fahrenheit`\nCurrently the weather status is `' + weatherStatus + '`')

    def reddit(self):
        reddit = praw.Reddit(client_id='Lz8v84RHrHl_Jw',
                             client_secret=self.getToken("reddit.txt"),
                             user_agent='Slack Bot')
        submission = random.choice(list(reddit.subreddit('ProgrammerHumor').hot(limit=10)))
        if(not submission.over_18):
            return ('From reddit.com/r/ProgrammerHumor:\n>>>' + submission.title + ':\n' + submission.url + '\n')
        else:
            return ('Uh oh... It looks like the randomly selected post was Not Safe For Work. It will not be posted on this chat')

    def processMSG(self,args,channel):
        if(args.startswith(self.prefix)):
            noarg = False
            command = args.split(' ')[0][1:]
            if(' ' in args):
                args = args.split(' ', 1)[1]
            else:
                noarg = True
            #Commands Below
            if(command == 'ohce'):
                if(noarg):
                    self.echo(">>>Command usage _incorrect_.\nExample: `!ohce [msg]`",channel)
                else:
                    self.echo(args[::-1],channel)
            if command == 'weather':
                if(noarg):
                    self.echo(self.getWeather(49401), channel)
                else:
                    print(args)
                    self.echo(self.getWeather(args), channel)
            if command == 'reddit':
                self.echo(self.reddit(),channel)


    def processEvent(self,event):
        if(event[0]['type'] == 'message'):
            text = event[0]['text']
            channel = event[0]['channel']
            self.processMSG(text,channel)

    def run(self):
        print("Preparing to connect....")
        if(self.connect()):
            self.setUserID()
            print('Bot running...')
            while True:
                event = self.slackclient.rtm_read()
                if(len(event) != 0):
                    pprint(event)
                    if(len(event) != 0):
                        try:
                            self.processEvent(event)
                        except Exception:
                            print(traceback.format_exc())
                sleep(1)
