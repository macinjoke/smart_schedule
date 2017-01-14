from __future__ import print_function
import os

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import httplib2

from apiclient import discovery

# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     flags = None

from smart_schedule import settings

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
# select readonly or not
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = '{}/local_setting/client_secret.json'.format(settings.APP_ROOT)
APPLICATION_NAME = 'Smart Schedule'


def get_credentials():
    # home_dir = os.path.expanduser('~')
    # credential_dir = os.path.join(home_dir, '.credentials')
    # if not os.path.exists(credential_dir):
    #     os.makedirs(credential_dir)
    # credential_path = os.path.join(credential_dir,
    #                                'calendar-smart-schedule.json')
    credential_path = os.path.join(settings.APP_ROOT, 'local_setting', 'calendar-smart-schedule.json')
    # if not os.path.exists(credential_dir):
    #     os.makedirs(credential_dir)
    # credential_path = os.path.join(credential_dir,
    #                                'calendar-smart-schedule.json')

    store = Storage(credential_path)
    credentials = store.get()
    # if not credentials or credentials.invalid:
    #     flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    #     flow.user_agent = APPLICATION_NAME
    #     if flags:
    #         credentials = tools.run_flow(flow, store, flags)
    #     else:  # Needed only for compatibility with Python 2.6
    #         credentials = tools.run(flow, store)
    #     print('Storing credentials to ' + credential_path)

    return credentials


def build_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service
