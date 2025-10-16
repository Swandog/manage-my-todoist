import os
import logging

logger=logging.getLogger(__name__)
loglevel = os.environ.get("LOG_LEVEL")
if loglevel:
    logger.setLevel(loglevel)
    sh=logging.StreamHandler()
    logger.addHandler(sh)


api_token=os.environ["TODOIST_API_TOKEN"]

from todoist_api_python.api import TodoistAPI

api = TodoistAPI(api_token)

def find_one_expected(itera, filtera):
    res=[thing for things in itera for thing in things if filtera(thing)]
    if len(res) != 1:
        raise RuntimeError("WHA HAPPEN")

    return res[0]

def find_project_by_name(name: str):
    project = find_one_expected(api.get_projects(), lambda p: p.name == name)
    return project

do_every_day_project=find_project_by_name("Do Every Day")
logger.debug(f"do_every_day_project = {do_every_day_project}")

tasks_to_do_every_day_section=find_one_expected(api.get_sections(project_id=do_every_day_project.id), lambda s: s.name == "Tasks To Do Every Day")
logger.debug(f"tasks_to_do_every_day_section = {tasks_to_do_every_day_section}")

tasks_i_do_every_day=[task for tasks in api.get_tasks(section_id=tasks_to_do_every_day_section.id) for task in tasks]

logger.debug("tasks found that I do every day:")
for x in tasks_i_do_every_day:
    logger.debug(f"    {x.content}")

# Filter out tasks already in "Today" project
today_project=find_project_by_name("Today")
logger.debug(f"today_project = {today_project}")


tasks_to_add=[]

print(tasks_to_add)
