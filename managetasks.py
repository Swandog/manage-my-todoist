import os

api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI

api = TodoistAPI(api_token)
print(api)

projects = api.get_projects()
for project in projects:
    print("PROJECT")
    for proj in project:
        print("   " + proj.name)