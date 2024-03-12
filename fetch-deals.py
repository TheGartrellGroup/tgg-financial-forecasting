import requests
import json
import os
import os.path
from dotenv import load_dotenv, find_dotenv

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

project_list = []
for monday_project in results["data"]["items_page_by_column_values"]["items"]:
    project_dict = {}
    project_dict["project_name"] = monday_project["name"]
    project_dict["project_id"] = monday_project["id"]
    project_dict["project_state"] = monday_project["state"]

    # Iterate over column values
    for board_column in monday_project["column_values"]:
        column_value = board_column["text"]
        column_name = board_column["column"]["title"]
        project_dict[column_name] = column_value

    print(project_dict["project_name"])
    project_list.append(project_dict)

print("Done formatting Monday.com results....")

print(results)


def update_values(spreadsheet_id, range_name, value_input_option, _values):
    creds, _ = google.auth.default()
    try:
        service = build("sheets", "v4", credentials=creds)
        values = [
            [
                # Cell values ...
            ],
            # Additional rows ...
        ]
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
