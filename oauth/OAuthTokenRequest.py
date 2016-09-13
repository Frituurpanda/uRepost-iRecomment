import requests
import requests.auth

client_auth = requests.auth.HTTPBasicAuth('VZiZ63DTFUxfUA', 'wCDnG-rZeBzsaK2zroublTHedsA')
post_data = {"grant_type": "password", "username": "Dejavupvote", "password": "hunter2"}
headers = {"User-Agent": "ChangeMeClient/0.1 by Dejavupvote"}
response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data,
                         headers=headers)
secondToken = "60ZQWbpRnh0bGGq2QVPRkK3V0Hw"

# Inject values into the oauthtoken.txt
text_file = open("oauth/oauthtoken.txt", "w")
text_file.write(response.json()['access_token'] + "\n")
text_file.write(secondToken)
text_file.close()
at = response.json()['access_token']

def printdebuglines():
    return "Injected the new token: " + at + " into oauthtoken.txt"
