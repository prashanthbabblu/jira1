import requests
from auth_and_headers import jira_auth_and_headers
import json


def get_issue(this_issue_key):
    """Gets all fields set and vacant for the epic or story queried

        Parameters:
            this_issue_key (string): issue identifier eg: D1-1
        Returns:
            Json Object: Object has all fields available set and vacant for the story/epic

   """
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/api/3/issue/{this_issue_key}"

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )
    text_contents = json.loads(response.text)
    return text_contents


def get_single_project(this_project_id):
    """Gets all fields set and vacant for the epic or story queried

       Parameters:
           this_project_id (string): project identifier eg: D1
       Returns:
           Json Object: Object has all project information

    """
    auth, headers, base_url = jira_auth_and_headers()

    # single project
    url = f"{base_url}/rest/api/3/project/{this_project_id}"

    response = requests.request(
       "GET",
       url,
       headers=headers,
       auth=auth
    )
    json_res = json.loads(response.text)
    return json_res


def get_all_projects():
    """Gets all projects in this jira instance, will return archived projects also

       Returns:
           Json Object: describes the projects n this jira instance

    """
    projects_ = []
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/api/3/project/search"

    while url is not None:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        json_res = json.loads(response.text)
        current_list_of_projects = json_res.get('values')
        for proj in current_list_of_projects:
            projects_.append(proj)
        url = json_res.get("nextPage", None)

    return projects_


def create_epic_link(link_from, link_to, link_type):
    """Links epics together in a number of meaningful ways
        Parameters:
            link_from (string): epic key eg: D1-1 this is the new epic, the child
            link_to (string): epic key eg: D1-1 this is the uber epic, the parent
            link_type (string): Relates, Blocks, Cloners, Duplicate
        Returns:
           Json Object:

    """
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/api/3/issueLink"

    payload = json.dumps({
        "outwardIssue": {
            "key": f"{link_from}"
        },
        "inwardIssue": {
            "key": f"{link_to}"
        },
        "type": {
            "name": f"{link_type}"
        }
    })

    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    text_response = "No link created"
    if response.ok:
        text_response = f"{link_from} now {link_type} {link_to}"
    return text_response


def get_emails_from_issue(this_issue_id):
    """Gets all stories attached to an epic

        Parameters:
            this_issue_id (string): issue identifier eg: D1-1
        Returns:
            Json Object: Object has assignee_name, assignee_email, reporter_name, reporter_email

   """
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/api/3/issue/{this_issue_id}"
    people = {}
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    json_res = json.loads(response.text)
    assignee_email = json_res['fields'].get('assignee', {}).get('emailAddress', "No Email listed")
    assignee_name = json_res['fields'].get('assignee', {}).get('displayName', "No Name listed")
    this_assignee = {"assignee_name": assignee_name, "assignee_email": assignee_email}
    people['assignee'] = this_assignee

    reporter_email = json_res['fields'].get('reporter', {}).get('emailAddress', "No Email listed")
    reporter_name = json_res['fields'].get('reporter', {}).get('displayName', "No Name listed")
    this_reporter = {"reporter_name": reporter_name, "reporter_email": reporter_email}
    people['reporter'] = this_reporter
    people['issue_key'] = this_issue_id

    return people


def get_stories_from_epic(epic):
    """Gets all stories attached to an epic

    Parameters: epic (string): Epic identifier eg: SECCOMPPM-93 Returns: Json Object: Key is story key, attributes:
    status_name, status_category, priority_name, project_name and project_key

   """
    epic_name = epic
    start_at = 0
    stories_in_epic = {}
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/agile/1.0/epic/{epic_name}/issue?maxResults=50&start_at={start_at}"
    while url is not None:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth
        )
        ret_json = json.loads(response.text)
        total_expected_results = ret_json.get('total', 0)
        for this_issue in ret_json["issues"]:
            this_issue_key = this_issue.get("key", None)
            stories_in_epic[f'{this_issue_key}'] = {}
            stories_in_epic[f'{this_issue_key}']["status_name"] = this_issue.get(
                'fields', {}).get('status', {}).get('name', None)
            stories_in_epic[f'{this_issue_key}']["status_category"] = this_issue.get(
                'fields', {}).get('status', {}).get('statusCategory', {}).get('key', None)
            stories_in_epic[f'{this_issue_key}']["project_key"] = this_issue.get(
                'fields', {}).get('project', {}).get('key', None)
            stories_in_epic[f'{this_issue_key}']["project_name"] = this_issue.get(
                'fields', {}).get('project', {}).get('name', None)
            stories_in_epic[f'{this_issue_key}']["priority_name"] = this_issue.get(
                'fields', {}).get('priority', {}).get('name', None)
        if len(stories_in_epic) != total_expected_results:
            start_at = start_at + 50
            url = f"{base_url}/rest/agile/1.0/epic/{epic_name}/issue?maxResults=50&start_at={start_at}"
        else:
            url = None

    return stories_in_epic


def add_comment_to_story(this_issue_key, comment):
    auth, headers, base_url = jira_auth_and_headers()
    url = f"{base_url}/rest/api/3/issue/{this_issue_key}/comment"
    comment_template = {'body': {}}
    comment_template['body']['type'] = "doc"
    comment_template['body']['version'] = 1
    comment_template['body']['content'] = []
    content_parent = {"type": "paragraph", "content": []}
    content_child = {"text": f"{comment}", "type": "text"}
    content_parent['content'].append(content_child)
    comment_template['body']['content'].append(content_parent)

    payload = json.dumps(comment_template)

    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    return response


if __name__ == "__main__":
    issue_key = "D2-1"
    issue = get_issue(issue_key)
    print(json.dumps(issue, indent=4))
    #
    # project_key = "D1"
    # project = get_single_project(project_key)
    # print(json.dumps(project, indent=4))
    #
    # projects = get_all_projects()
    # print(json.dumps(projects, indent=4))

    # # First epic key is the new one you create, the second id the one you are linking to
    # # The third input is the type of link - get_issue_link_types.py is in the repo
    # link_res = create_epic_link("D1-7", "D1-23", "Relates")
    # print(link_res)
    #
    # get_emails = get_emails_from_issue('D1-5')
    # print(json.dumps(get_emails, indent=4))
    #
    # epic_name = "D1-7"
    # issues_in_epic = get_stories_from_epic(epic_name)
    # print(json.dumps(issues_in_epic, indent=4))
    #
    # story_id = "D1-7"
    # comment_text = "I made it"
    # res = add_comment_to_story(story_id, comment_text)
    # print(res)

