import sys
sys.path.append('/usr/local/lib/python3.7/site-packages')

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# dummyData = '{"Question":"layoutItems_2_value", "Answer" : "layoutItems_3_value"}'

data= []

def authenticate_url(url):
    params = {
    "grant_type": "password",
    "client_id": "3MVG9n_HvETGhr3BYBHKpD2a6jwnPLLU5LGOzt0gsIMJIm6r0.8aWhJp33TE8Q1zfMYk8YvxvS0ClrjWxRAkp", # Consumer Key
    "client_secret": "1606E962D50A2D698564E5B4DCECB1DB5EA9EBB1D0C383495E61D1A7E5AF6F99", # Consumer Secret
    "username": "zain@sydney.com", # The email you use to login
    "password": "ZMC1122zzcub2etuPXA8FtZc6dxoWFNaG" # Concat of password and security token
}
    r = requests.post(url, params=params)
    access_token = r.json().get("access_token")
    instance_url = r.json().get("instance_url")
    print("Access Token:", access_token)
    print("Instance URL", instance_url)

    return access_token, instance_url


def sf_api_call(action, access_token, instance_url):
    """
    Helper function to make calls to Salesforce REST API.
    Parameters: action (the URL), URL params, method (get, post or patch), data for POST/PATCH.
    """
    method = 'get'

    parameters = {}

    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        'Accept-Language': 'en-US',
        'Authorization': 'Bearer %s' % access_token
    }
    if method == 'get':
        r = requests.request(method, instance_url+action, headers=headers, params=parameters, timeout=30)
    elif method in ['post', 'patch']:
        r = requests.request(method, instance_url+action, headers=headers, json=data, params=parameters, timeout=10)
    else:
        # other methods not implemented in this example
        raise ValueError('Method should be get or post or patch.')
    print('Debug: API %s call: %s' % (method, r.url) )
    if r.status_code < 300:
        if method=='patch':
            return None
        else:
            return r.json()
    else:
        raise Exception('API error when calling %s : %s' % (r.url, r.content))

def extract_article(json):
    return json.get("articles")

def extract_information(json_file, attributes):
    ret_dict = {}
    #print(attributes)
    #print(type(attributes))
    y = '{"Question":"layoutItems_2_value", "Answer" : "layoutItems_3_value"}'
    x = json.loads(y)
    print(x)
    print(type(x))
    #print(x)
    #print(x)
    #print(type(x))
    for attribute in x:
        print(attribute)
        value = json_file.get(x[attribute])
        ret_dict[attribute] = value
    
    print(ret_dict)
    return ret_dict



# attributes = x

# articles_simplified.append(extract_information(article, attributes))

# Getting JSON data
@app.route('/', methods=['POST'])
def addOne():
    try:
        print("sdsd")
        access_token, instance_url = authenticate_url("https://login.salesforce.com/services/oauth2/token")
        print(access_token)
        print(instance_url)
        data = sf_api_call("/services/data/v38.0/support/knowledgeArticles", access_token, instance_url)
        article_data = extract_article(data)
        #print(article_data[0])
        return article_data[0]
    except:
        return 'error'

def flatten_json(json_data):
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(json_data)
    return out


def elastic_search(data):
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    import elasticsearch.exceptions

    # Check connection!
    import requests
    from requests.auth import HTTPBasicAuth

    dbUrl = "https://43e94a6daea349b88b7fe5df6a59e496.ap-southeast-2.aws.found.io:9243/"
    res = requests.get(dbUrl, auth=HTTPBasicAuth("elastic", "GL0nVKx2szcQtBKaJVDxAOmf"))

    print(res.status_code)
    print(res.ok)

    # Elastic search object
    es = Elasticsearch([dbUrl], 
                    http_auth=('elastic', 'GL0nVKx2szcQtBKaJVDxAOmf'))

    # Manual DB update
    def gendata(data):
        # refids = [1,2,3]
        # topics = ["a", "b", "c"]
        # searchString = ['foo', 'bar', 'baz']
        # answers = ['foo-found', 'bar-found', 'baz-found']

        i=0
        while i < len(data):
            
            yield {
                "_index": "salesforce_kb",
                "_type": "_doc",
                "refID": "",
                "topic": "",
                "searchString": data[i].get("Question"),
                "refurl": "",
                "lastModified": "",
                "answer": data[i].get("Answer")
            }
            i+=1

    # DB store/update
    def add_to_db(data):
        try:
            bulk(es, gendata(data), 
                #index='TestChatmate', 
                #doc_type='clue', 
                raise_on_error=True)
        except elasticsearch.exceptions.ConnectionError:
            # TODO: Handle the error appropriately for your situation
            print("Couldn't connect to DB")
        else:
            print("record added to DB!")

    #Adding articles json to elastic database 
    add_to_db(data)



#articles_list = data_json.get(“articles”)
# articles_json_list = []

# for article in articles_list:
#   url = article.get("url")
#   data = sf_api_call(url)
#   data = flatten_json(data)
#   print(json.dumps(data, indent=4))
#   articles_json_list.append(data)

@app.route('/postmap', methods=['POST'])
def addTwo():
        attributes = request.get_data()
        #print(attributes)

        access_token, instance_url = authenticate_url("https://login.salesforce.com/services/oauth2/token")

        #print(access_token)
        #print(instance_url)
        
        data = sf_api_call("/services/data/v38.0/support/knowledgeArticles", access_token, instance_url)
        #print(data)
        article_data = extract_article(data)
        #print(article_data)
        articles_json_list = []

        for article in article_data:
            url = article.get("url")
            data = sf_api_call(url, access_token, instance_url)
            data = flatten_json(data)
            #print(json.dumps(data, indent=4))
            flat_data = extract_information(data, attributes)
            articles_json_list.append(flat_data)

        #print(articles_json_list)
        elastic_search(articles_json_list)

        return '200'

@app.route('/', methods=['GET'])
def getOne():
    try:
        return jsonify({'Data' : dummyData})
    except:
        return 'error'


if __name__ == "__main__":
    app.run(debug=True)

