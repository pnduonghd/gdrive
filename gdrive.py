import httplib2
import oauth2client
from googleapiclient.discovery import build
from oauth2client import file, client, tools
import requests
import os
import json
import time
from urllib import parse
from progress.bar import Bar


def generate_token():
    drive_scope = [
        'https://www.googleapis.com/auth/drive',
    ]
    flow = client.flow_from_clientsecrets(
        'gdrive.json',
        scope=drive_scope,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        prompt='consent'
    )

    authorization_url = flow.step1_get_authorize_url()
    print('Visit URL and Copy Code')
    print('\n')
    print(authorization_url)
    print('\n')
    code=input('Code: ')
    # print(code)

    credentials = flow.step2_exchange(code)
    token = credentials.access_token
    store = file.Storage('token.json')
    store.put(credentials)
    return token

def get_token():
    store = file.Storage('token.json')
    credentials = store.get()
    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
    token = credentials.access_token
    return token

if os.path.isfile('token.json'):
    token = get_token()
else:
    token = generate_token()

print('TOKEN', token)

with open('list.txt', 'r') as fp:
    lines = fp.readlines()

ids = []
for line in lines:
  if line.strip():
    prefix, drive_id = line.strip().rsplit('id=', 1)
    ids.append(drive_id)

# drive_id = ids[0]

endpoint = 'https://drive.google.com/e/get_video_info?docid={}&access_token={}'
api_endpoint = 'https://www.googleapis.com/drive/v3/files/{}?supportsAllDrives=true&supportsTeamDrives=true&fields=name&access_token={}'

for drive_id in ids:
    s = requests.Session()

    api_url = api_endpoint.format(drive_id, token)
    r = s.get(api_url)
    file_name = r.json()['name']

    print(file_name)

    info_url = endpoint.format(drive_id, token)
    page = s.get(info_url)
    info_raw = page.text
    stream_data = parse.parse_qs(info_raw)
    streams = {}
    fmt_stream_map = stream_data['fmt_stream_map'][0]

    for stream in fmt_stream_map.split(','):
        k, v = stream.split('|', 1)
        streams[k] = v

    dl_url = ''
    if '37' in streams:
        dl_url = streams['37']
    elif '22' in streams:
        dl_url = streams['22']
    else:
        dl_url = list(streams.values())[0]

    # print(dl_url)

    r = s.get(dl_url, stream=True)

    try:
        file_size = int(r.headers['Content-Length'])
    except:
        file_size = 1

    bar = Bar('Downloading {}'.format(file_name), max=file_size)
    with open(file_name, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                bar.next(8192)
                f.write(chunk)
    bar.finish()
