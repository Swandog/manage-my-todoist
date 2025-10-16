import os

api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI

api = TodoistAPI(api_token)
print(api)

def find_tasks_i_do_every_day():
    query_filter="#Do\ Every\ Day & /Tasks\ To\ Do\ Every\ Day"
    tasks=[t for tl in api.filter_tasks(query=query_filter) for t in tl ]
    return tasks


def find_everyday_tasks_to_create(tasks):
    exit(1)

# Find tasks to do every day
tasks_i_do_every_day=find_tasks_i_do_every_day()
# print(tasks_i_do_every_day)
for x in tasks_i_do_every_day:
    print(x.content)

# Filter out tasks already in "Today" project
tasks_to_add=find_everyday_tasks_to_create(tasks_i_do_every_day)