import datetime
import os.path
from sys import argv
import sqlite3
from dateutil import parser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


YOUR_CALENDAR_ID = ''
YOUR_TIMEZONE = ''


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
    
    # determine which function to run        
    if argv[1] == 'add':
        duration = argv[2]
        description = argv[3]
        addEvent(creds, duration, description)
    if argv[1] == 'commit':
        commitHours(creds)  
      
def commitHours(creds):
  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    today = datetime.date.today()
    timeStart = str(today) + "T05:00:00"
    timeEnd = str(today) + "T04:59:59"
    print("Getting the upcoming events")
    events_result = (
        service.events()
        .list(
            # Change the calendar ID for specific events
            calendarId="primary",
            timeMin = timeStart,
            maxResults = timeEnd,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    totalDuration = datetime.timedelta(
    seconds = 0,
    minutes = 0,
    hours = 0,
    )
    
    print("Your Hours for Today:")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        
        start_formatted = parser.isoparse(start)
        end_formatted = parser.isoparse(end)
        duration = end_formatted - start_formatted
        
        totalDuration += duration
        print(f"{event['summary']}, duration: {duration}")
    print(f"Total duration for events: {totalDuration}")

    conn = sqlite3.connect(f'hours.db')
    cur = conn.cursor()
    print("Opened database successfully")
    date = datetime.date.today()
    
    formatted_totalDuration = totalDuration.seconds/3600 #Getting Hours
    used_hours = (date, "USED", formatted_totalDuration)
    cur.execute("INSERT INTO hours VALUES(?, ?, ?);", used_hours)
    conn.commit()

  except HttpError as error:
    print(f"An error occurred: {error}")

def addEvent(creds, duration, description):
    start = datetime.datetime.utcnow()
    
    end = datetime.datetime.utcnow() + datetime.timedelta(hours=int(duration))
    start_formatted = start.isoformat() + 'Z'
    end_formatted = end.isoformat() + 'Z'

    event = {
    'summary': description,
    'start': {
        'dateTime': start_formatted,
        'timeZone': YOUR_TIMEZONE,
        },
    'end': {
        'dateTime': end_formatted,
        'timeZone': YOUR_TIMEZONE,
        },
    }

    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId=YOUR_CALENDAR_ID, body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

def getHours(number_of_days):

    # get today's date
    today = datetime.date.today()
    seven_days_ago = today + datetime.timedelta(days=-int(number_of_days))

    # get hours from database
    conn = sqlite3.connect('hours.db')
    cur = conn.cursor()

    cur.execute(f"SELECT DATE, HOURS FROM hours WHERE DATE between ? AND ?", (seven_days_ago, today))

    hours = cur.fetchall()

    total_hours = 0
    for element in hours:
        print(f"{element[0]}: {element[1]}")
        total_hours += element[1]
    print(f"Total hours: {total_hours}")
    print(f"Average hours: {total_hours/float(number_of_days)}")
    
     
if __name__ == "__main__":
  main()