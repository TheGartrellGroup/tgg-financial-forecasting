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
import calendar
from datetime import datetime
import math

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv(find_dotenv())

apiKey = os.environ.get("API_KEY")
boardId = os.environ.get("DEALS_BOARD")
spreadsheetId = os.environ.get("SPREADSHEET_ID")
apiUrl = "https://api.monday.com/v2"
headers = {"Authorization": apiKey, "API-Version": "2023-10"}
project_config = None

# READ IN CONFIG.JSON
try:
    with open("config.json", "r") as infile:
        project_config = json.load(infile)
except Exception as e:
    print("Unable to load config.json")
    print(str(e))
    exit()

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
        ids: ["status", "numbers", "numbers0", "numbers1", "numbers6", "text", "date", "date9"]
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


# Filter out for empty required fields
required_fields = project_config["required_fields"]
default_fields = project_config["default_fields"]
empty_fields = []

for project in project_list:
    for field in required_fields:
        if project[field] == "":
            print(f"Removing {project['project_name']} because {field} is empty :( ")
            empty_fields.append(project["project_name"])

empty_set = set(empty_fields)
filtered_list = [x for x in project_list if x["project_name"] not in empty_set]

# Set defaults based on config
for project in filtered_list:
    for field in default_fields:
        # This is gross and should be made better
        if project[list(field.keys())[0:][0]] == "":
            project[list(field.keys())[0:][0]] = str(list(field.values())[0])

print(filtered_list)

formatted_data = []
for project in filtered_list:
    year, month, day = project["Exp Proj Start"].split("-")

    date_object = datetime.strptime(project["Exp Proj Start"], "%Y-%m-%d")
    month_name = date_object.strftime("%B")
    days_in_month = calendar.monthrange(int(year), int(month))
    month_half = math.ceil(days_in_month[1] / 2)


def create_calendar_template():
    output_dict = {}
    current_date = datetime.datetime.now()

    # Datetime objs for 5 years previous/future from current year
    floor_year = current_date.year - 5
    ceiling_year = current_date.year + 5

    # Stub out years
    for year in range(int(floor_year), int(ceiling_year + 1)):

        # ...and months
        output_dict[str(year)] = {}
        for month in range(1, 13):
            output_dict[str(year)][str(month)] = {}
            output_dict[str(year)][str(month)]["name"] = calendar.month_name[month]
            output_dict[str(year)][str(month)]["first_half"] = "01-15"

            # Get digit for last day of the month
            last_day = calendar.monthrange(year, month)[1]
            output_dict[str(year)][str(month)]["second_half"] = "16-" + str(last_day)
    return output_dict


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
        result = sheet.values().get(spreadsheetId=spreadsheetId, range="").execute()
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


if __name__ == "__main__":
    create_calendar_template()
