import requests
import json
import os
import os.path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

apiKey = os.environ.get("API_KEY")
boardId = os.environ.get("DEALS_BOARD")
apiUrl = "https://api.monday.com/v2"
headers = {"Authorization": apiKey, "API-Version": "2023-10"}

query = f"""
{{
  items_page_by_column_values(
    board_id: {boardId}
    columns: {{column_id: "status", column_values: ["RFP Submitted", "Lead", "Proposal", "Negotiation", "Contract Sent", "Won", "Default Label", "Scope/Discovery"]}}
  ) {{
    cursor
    items {{
      id
      name
      state
      column_values(
        ids: ["status", "numbers", "numbers0", "numbers6", "text", "date", "date9"]
      ) {{
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
"""

data = {"query": query}

response = requests.post(url=apiUrl, json=data, headers=headers)
results = response.json()

print(results)
