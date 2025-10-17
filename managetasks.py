from datetime import datetime
import os
import logging

logger=logging.getLogger(__name__)
loglevel = os.environ.get("LOG_LEVEL") or "INFO"
logger.setLevel(loglevel)
sh=logging.StreamHandler()
logger.addHandler(sh)

every_day_label="Every Day"
once_a_week_label="Once_A_Week"
api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI
from todoist_api_python import models

api = TodoistAPI(api_token)

def describe_task(task: models.Task):
    return f"task.id (\"{task.content}\")"

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
    logger.debug(f"    {describe_task(x)}")

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
        logger.debug(f"task {describe_task(task)} was found in Today: {every_day_tasks_in_today[task.content].id}")
    else:
        logger.debug(f"task {describe_task(task)} was not found in Today, marking it for addition")
        tasks_to_add.append(task)

logger.info(f"Found {len(tasks_to_add)} tasks to add")

# Add the tasks
incoming_section=find_section_in_project(today_project, "Incoming")
logger.debug(f"incoming_section = {incoming_section}")
for task in tasks_to_add:
    logger.info(f"\tAdding task '{task.content}'")
    api.add_task(project_id=today_project.id, section_id=incoming_section.id, content=task.content, labels=[every_day_label])

### Slower Recurrences!
# If there are any Once A Week tasks in Once A Week that are due, move them to Today/Incoming

once_a_week_project=find_project_by_name("Once A Week")
oawt_tasks=[task for tasks in api.get_tasks(project_id=once_a_week_project.id) for task in tasks]
for task in oawt_tasks:
    logger.debug(f"Examining task {describe_task(task)} in Once A Week")
    if not task.parent_id and task.due:
        if task.due.date < datetime.now():
            logger.info(f"Recurring task {describe_task(task)} is overdue ({task.due.date}), moving to Today/Incoming")
            api.move_task(task_id=task.id, section_id=incoming_section.id)
        else:
            logger.debug(f"Found recurring task {describe_task(task)} in Once A Week but it is not overdue ({task.due.date})")


# If there are any Once A Week tasks in Today that are not due, move them to Once A Week
oawt_tasks_in_today=[task for tasks in api.get_tasks(project_id=today_project.id, label=once_a_week_label) for task in tasks]
for task in oawt_tasks_in_today:
    logger.debug(f"Examining Once A Week task {describe_task(task)} in Today")
    if not task.parent_id and task.due:
        if task.due.date > datetime.now():
            logger.info(f"Recurring task {describe_task(task)} is not due ({task.due.date}), moving to Once A Week")
            api.move_task(task_id=task.id, project_id=once_a_week_project.id)
        else:
            logger.debug(f"Found recurring task {describe_task(task)} in Today but it due ({task.due.date})")
