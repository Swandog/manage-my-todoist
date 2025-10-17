import os
import logging

logger=logging.getLogger(__name__)
loglevel = os.environ.get("LOG_LEVEL")
if loglevel:
    logger.setLevel(loglevel)
    sh=logging.StreamHandler()
    logger.addHandler(sh)

every_day_label="Every Day"
api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI
from todoist_api_python import models

api = TodoistAPI(api_token)

def find_one_expected(itera, filtera):
    res=[thing for things in itera for thing in things if filtera(thing)]
    if len(res) != 1:
        raise RuntimeError("WHA HAPPEN")

    return res[0]

def find_project_by_name(name: str):
    project = find_one_expected(api.get_projects(), lambda p: p.name == name)
    return project

def find_section_in_project(project: models.Project, section_name: str):
    section = find_one_expected(api.get_sections(project_id=project.id), lambda s: s.name == section_name)
    return section

do_every_day_project=find_project_by_name("Do Every Day")
logger.debug(f"do_every_day_project = {do_every_day_project}")

tasks_to_do_every_day_section=find_section_in_project(do_every_day_project, "Tasks To Do Every Day")
logger.debug(f"tasks_to_do_every_day_section = {tasks_to_do_every_day_section}")

tasks_i_do_every_day=[task for tasks in api.get_tasks(section_id=tasks_to_do_every_day_section.id) for task in tasks]

logger.debug("tasks found that I do every day:")
for x in tasks_i_do_every_day:
    logger.debug(f"    {x.content}")

# Filter out tasks already in "Today" project
# First, find all possible tasks in the project
today_project=find_project_by_name("Today")
logger.debug(f"today_project = {today_project}")

every_day_tasks_in_today={task.content: task for tasks in api.get_tasks(project_id=today_project.id, label=every_day_label) for task in tasks}
logger.debug(f"every_day_tasks_in_today = {every_day_tasks_in_today}")

# Then, find all tasks without a matching mate in Today
tasks_to_add=[]
for task in tasks_i_do_every_day:
    if task.content in every_day_tasks_in_today:
        logger.debug(f"task {task.id} ({task.content:<40}) was found in Today: {every_day_tasks_in_today[task.content].id}")
    else:
        logger.debug(f"task {task.id} ({task.content:<40}) was not found in Today, marking it for addition")
        tasks_to_add.append(task)

print(f"Found {len(tasks_to_add)} tasks to add")

# Add the tasks
incoming_section=find_section_in_project(today_project, "Incoming")
logger.debug(f"incoming_section = {incoming_section}")
for task in tasks_to_add:
    print(f"\tAdding task '{task.content}'")
    api.add_task(project_id=today_project.id, section_id=incoming_section.id, content=task.content, labels=[every_day_label])
