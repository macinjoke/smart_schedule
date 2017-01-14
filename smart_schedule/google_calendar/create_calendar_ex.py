# Refer to the Python quickstart on how to setup the environment:
# https://developers.google.com/google-apps/calendar/quickstart/python
# Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
# stored credentials.

from apiclient import discovery
from smart_schedule.google_calendar import api_manager
import httplib2

credentials = api_manager.get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)


event = {
  'summary': 'APIから予定をつくったぞ',
  'location': '東京電機大学',
  'description': '試しに予定を作った',
  'start': {
    'dateTime': '2017-01-15T09:00:00+09:00',
    'timeZone': 'Asia/Tokyo',
  },
  'end': {
    'dateTime': '2017-01-15T17:00:00+09:00',
    'timeZone': 'Asia/Tokyo',
  },
  'recurrence': [
    'RRULE:FREQ=DAILY;COUNT=2'
  ],
  'attendees': [
    {'email': 'lpage@example.com'},
    {'email': 'sbrin@example.com'},
  ],
  'reminders': {
    'useDefault': False,
    'overrides': [
      {'method': 'email', 'minutes': 24 * 60},
      {'method': 'popup', 'minutes': 10},
    ],
  },
}

event = service.events().insert(calendarId='primary', body=event).execute()
print('Event created: %s' % (event.get('htmlLink')))
