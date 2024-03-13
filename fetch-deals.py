import requests
import json
import os
import os.path
from dotenv import load_dotenv, find_dotenv

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
SAMPLE_RANGE_NAME = "Class Data!A2:E"

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


def get_creds():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId="", range="").execute()
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return

        print("Name, Major:")
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print(f"{row[0]}, {row[4]}")
    except HttpError as err:
        print(err)
