# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import getpass
import httplib2
import json
import urllib

def request_oauth_token():
  """ Prompts user for credentials and returns Oauth token from GitHub """

  print "Requesting an oauth token from GitHub."
  print "Your username and password will not be stored."

  # Deliberately don't use httplib2.add_credentials, as httplib2 does a
  # request without them first and expects to get a 401 back.  github
  # instead throws a 404 if there's no user/pass attached to the request.
  # This confuses httplib2, which thinks there's an error, and aborts
  # after the first request without using the set credentials.
  username = raw_input("GitHub Username: ")
  password = getpass.getpass("GitHub Password: ")
  auth = base64.encodestring(username + ':' + password)

  http = httplib2.Http()
  headers = {'Content-type': 'application/x-www-form-urlencoded',
             'Accept': 'application/json',
             'Authorization': 'Basic ' + auth}
  params = {"scopes": ["public_repo"], "note_url": "quickopen"}
  # Don't urlencode the json delimiters.
  body = json.dumps(params, separators=(',',':'))
  response, content = http.request('https://api.github.com/authorizations',
                                   'POST',
                                   headers=headers,
                                   body=body)
  try:
    content = json.loads(content)
  except(ValueError):
    print "Error, unable to parse response. Dumping raw response"
    print response, content
    return None

  if response.status != 201:
    print content['message']
    return None

  token = content['token']
  return token
