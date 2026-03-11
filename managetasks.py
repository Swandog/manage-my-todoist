from datetime import date, datetime, time
import logging
from typing import Optional
import itertools
import argparse

from todoist_api_python.api import TodoistAPI
from todoist_api_python import models

every_day_label = "Every Day"
once_a_week_label = "Once_A_Week"


def describe_task(task: models.Task):
    return f'task.id ("{task.content}")'


def find_one_expected(itera, filtera):
    res = [thing for things in itera for thing in things if filtera(thing)]
    if len(res) != 1:
        raise RuntimeError("WHA HAPPEN")

    return res[0]


def find_project_by_name(api, name: str):
    project = find_one_expected(api.get_projects(), lambda p: p.name == name)
    return project


def find_section_in_project(api, project: models.Project, section_name: str):
    section = find_one_expected(
        api.get_sections(project_id=project.id), lambda s: s.name == section_name
    )
    return section


def task_due_datetime(task: models.Task) -> Optional[datetime]:
    if not task.due:
        return None
    else:
        due = task.due.date
        if isinstance(due, date):
            return datetime.combine(due, time.min)
        else:
            return due


def main(api_token, loglevel, dry_run=False):
    logger = logging.getLogger(__name__)
    logger.setLevel(loglevel)
    sh = logging.StreamHandler()
    logger.addHandler(sh)

    api = TodoistAPI(api_token)

    do_every_day_project = find_project_by_name(api, "Do Every Day")
    logger.debug(f"do_every_day_project = {do_every_day_project}")

    tasks_to_do_every_day_section = find_section_in_project(
        api, do_every_day_project, "Tasks To Do Every Day"
    )
    logger.debug(f"tasks_to_do_every_day_section = {tasks_to_do_every_day_section}")

    tasks_i_do_every_day = [
        task
        for tasks in api.get_tasks(section_id=tasks_to_do_every_day_section.id)
        for task in tasks
    ]

    logger.debug("tasks found that I do every day:")
    for x in tasks_i_do_every_day:
        logger.debug(f"    {describe_task(x)}")

    # Filter out tasks already in "Today" project
    # First, find all possible tasks in the project
    today_project = find_project_by_name(api, "Today")
    logger.debug(f"today_project = {today_project}")

    every_day_tasks_in_today = {
        task.content: task
        for tasks in api.get_tasks(project_id=today_project.id, label=every_day_label)
        for task in tasks
    }
    logger.debug(f"every_day_tasks_in_today = {every_day_tasks_in_today}")

    # Then, find all tasks without a matching mate in Today
    tasks_to_add = []
    for task in tasks_i_do_every_day:
        if task.content in every_day_tasks_in_today:
            logger.debug(
                f"task {describe_task(task)} was found in Today: {every_day_tasks_in_today[task.content].id}"
            )
        else:
            logger.debug(
                f"task {describe_task(task)} was not found in Today, marking it for addition"
            )
            tasks_to_add.append(task)

    logger.info(f"Found {len(tasks_to_add)} tasks to add")

    # Add the tasks
    incoming_section = find_section_in_project(api, today_project, "Incoming")
    logger.debug(f"incoming_section = {incoming_section}")
    for task in tasks_to_add:
        if dry_run:
            logger.info(f"\tIn dry run mode, would add task '{task.content}'")
        else:
            logger.info(f"\tAdding task '{task.content}'")
            api.add_task(
                project_id=today_project.id,
                section_id=incoming_section.id,
                content=task.content,
                labels=[every_day_label],
                description=task.description,
            )

    ### Slower Recurrences!
    # If there are any Once A Week tasks in Once A Week that are due, move them to Today/Incoming
    # Also bring over any overdue tasks in the Inbox

    once_a_week_project = find_project_by_name(api, "Once A Week")
    inbox_project = find_project_by_name(api, "Inbox")
    tasks_to_examine = itertools.chain(
        api.get_tasks(project_id=once_a_week_project.id),
        api.get_tasks(project_id=inbox_project.id),
    )
    for task_list in tasks_to_examine:
        for task in task_list:
            logger.debug(f"Examining task {describe_task(task)} in Once A Week")
            if not task.parent_id:
                due = task_due_datetime(task)
                if due:
                    if due < datetime.now():
                        if dry_run:
                            logger.info(
                                f"Dry run mode prevents moving of overdue task {describe_task(task)} ({due})"
                            )
                        else:
                            logger.info(
                                f"Recurring task {describe_task(task)} is overdue ({due}), moving to Today/Incoming"
                            )
                            api.move_task(
                                task_id=task.id, section_id=incoming_section.id
                            )
                    else:
                        logger.debug(
                            f"Found recurring task {describe_task(task)} in Once A Week but it is not overdue ({due})"
                        )

    # If there are any Once A Week tasks in Today that are not due, move them to Once A Week
    oawt_tasks_in_today = [
        task
        for tasks in api.get_tasks(project_id=today_project.id, label=once_a_week_label)
        for task in tasks
    ]
    for task in oawt_tasks_in_today:
        logger.debug(f"Examining Once A Week task {describe_task(task)} in Today")
        if not task.parent_id:
            due = task_due_datetime(task)
            if due:
                if due > datetime.now():
                    if dry_run:
                        logger.info(
                            f"Dry run mode prevents moving of task {describe_task(task)} that is not due ({due})"
                        )
                    else:
                        logger.info(
                            f"Recurring task {describe_task(task)} is not due ({due}), moving to Once A Week"
                        )
                        api.move_task(
                            task_id=task.id, project_id=once_a_week_project.id
                        )
                else:
                    logger.debug(
                        f"Found recurring task {describe_task(task)} in Today but it is due ({due})"
                    )


if __name__ == "__main__":
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="do not actually make changes"
    )

    args = parser.parse_args()

    api_token = os.environ["TODOIST_API_TOKEN"]
    loglevel = os.environ.get("LOG_LEVEL") or "INFO"

    main(api_token, loglevel, args.dry_run)
