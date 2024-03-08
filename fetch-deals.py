import requests
import json
import os
import os.path

apiKey = os.environ.get("API_KEY")
boardId = os.environ.get("DEALS_BOARD")
apiUrl = "https://api.monday.com/v2"
headers = {"Authorization": apiKey, "API-Version": "2023-04"}

query = f"""
{{
  boards(ids: {boardId}) {{
    items_page {{
      items {{
        id
        name
        column_values(ids: ["numbers", "numbers0", "numbers6", "text", "date", "date9"]) {{
          value
          text
          column {{
            id
            title
            description
          }}
        }}
      }}
    }}
  }}
}}
"""

data = {"query": query}

response = requests.post(url=apiUrl, json=data, headers=headers)
print(response.json())
