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

import getpass
import Github
import GithubException

def request_oauth_token():
  """ Prompts user for credentials and returns Oauth token from GitHub """

  print "Requesting an oauth token from GitHub."
  print "Your username and password will not be stored."

  username = raw_input("GitHub Username: ")
  password = getpass.getpass("GitHub Password: ")

  try:
    g = Github.Github(username, password)
    user = g.get_user()
    auth = user.create_authorization(scopes=["public_repo"],note="quickopen")
    return auth.token
  except GithubException.GithubException as e:
    print "Error: " + str(e)
    return None
