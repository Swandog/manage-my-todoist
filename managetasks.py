import os

api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI

api = TodoistAPI(api_token)
print(api)

def find_one_expected(itera, filtera):
    res=[thing for things in itera for thing in things if filtera(thing)]
    if len(res) != 1:
        raise RuntimeError("WHA HAPPEN")

    return res[0]

do_every_day_project=find_one_expected(api.get_projects(), lambda p: p.name == "Do Every Day")
print(do_every_day_project)

tasks_to_do_every_day_section=find_one_expected(api.get_sections(project_id=do_every_day_project.id), lambda s: s.name == "Tasks To Do Every Day")
print(tasks_to_do_every_day_section)

tasks_i_do_every_day=[task for tasks in api.get_tasks(section_id=tasks_to_do_every_day_section.id) for task in tasks]

for x in tasks_i_do_every_day:
    print(x.content)

# Filter out tasks already in "Today" project
tasks_to_add=[]

print(tasks_to_add)
