import requests
import json

apiKey = ''
apiUrl = "https://api.monday.com/v2"
headers = {"Authorization" : apiKey, "API-Version" : "2023-04"}

query = '''
query {
    boards(ids: 5045561244) {
        items_page {
            items {
                id 
                name 
            }
        }
    }
}
'''

data = {'query' : query}

response = requests.post(url=apiUrl, json=data, headers=headers)
print(response.json())
