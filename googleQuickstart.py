from __future__ import print_function
import secrets
import datetime
from dateutil import parser
from collections import OrderedDict
import os.path
import sqlite3 

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    commitHours(creds)
    addEvent(creds, 2, "Testing what I know!")

def printDailyEvents(all_events_ordered):
    for time, events  in all_events_ordered.items():  
        for event in events:
            summary = event["summary"]
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_start = parser.isoparse(start)
            formatted_end = parser.isoparse(end)
            
            duration = formatted_end-formatted_start     
            hour = int(time[:time.find(':')])
            if hour > 12:
                hour = hour - 12
                time = str(hour) + time[2:-3] + " PM"
            else:
                time = time[:-3] + " AM"

            print(f"{summary} :: Duration: {duration} hours at {time} CST")

def commitHours(creds):
    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        today = datetime.date.today()
        timeStart = str(today) + "T10:00:00Z" # 'Z' indicates UTC time
        timeEnd = str(today) + "T23:59:59Z"
        print('Getting today\'s working hours')
    
        calendarIds = [secrets.CALENDAR1, secrets.CALENDAR2, secrets.CALENDAR3 ,secrets.CALENDAR4 , secrets.CALENDAR5]

        total_duration = datetime.timedelta(seconds=0,minutes=0,hours=0)
        print("Today's Event Hours")
        all_events = dict()
        for calendarId in calendarIds:
            events_result = service.events().list(calendarId=calendarId, timeMin=timeStart, timeMax=timeEnd,
                                                singleEvents=True,
                                                orderBy='startTime', timeZone="America/Chicago").execute()
            events = events_result.get('items', [])

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_start = parser.isoparse(start)
                formatted_end = parser.isoparse(end)
                
                duration = formatted_end-formatted_start
                total_duration += duration
                    

                t_index = start.find('T')
                dash_index = start.rfind("-")
                time = start[t_index+1:dash_index]    
                
                if all_events.get(time):
                    all_events[time].append(event)
                else:
                    all_events[time] = [event]

            all_events_ordered = OrderedDict(sorted(all_events.items()))

        printDailyEvents(all_events_ordered)
        print(f"Total busy time today: {total_duration}")    
        connection = sqlite3.connect(f'time.db')
        cursor = connection.cursor()    
        print("Opened database successfully")
        date = datetime.date.today()
        
        formatted_total_duration = total_duration.seconds/60/60
        busy_hours = (date, 'WORKING', formatted_total_duration)
        cursor.execute("INSERT INTO time VALUES(?, ?, ?);", busy_hours)
        connection.commit()

    except HttpError as error:
        print('An error occurred: %s' % error)


def addEvent(creds, duration, description):
    start = datetime.datetime.utcnow()
    end = datetime.datetime.utcnow() + datetime.timedelta(hours=duration)
    f_start = start.isoformat() + "Z"
    f_end = end.isoformat() + "Z"

    event = {
        'sumamry': description,
        'start': {
            'dateTime': f_start,
            'timeZone': 'America/Chicago',
        },
        'end': {
            'dateTime': f_end,
            'timeZone': 'America/Chicago',
        }
    }

    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId=secrets.CALENDAR1, body=event).execute()
    print("Event created: %s" % (event.get('htmlLink')))

if __name__ == '__main__':
    main()