import sys
sys.path.append('/usr/local/lib/python3.7/site-packages')

import requests

dummyData = '{"Question":"layoutItems_2_value", "Answer" : "layoutItems_3_value"}'

#print(type(dummyData))

#attributes = requests.post("http://127.0.0.1:5000/")

attributes1 = requests.post("http://127.0.0.1:5000/postmap", data = dummyData)

print(attributes1.text)