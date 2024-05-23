# This script is designed to be used along with the start-preview Github Action 
# This scipt deletes any preview project not tied to a PR currently Open or in Draft
# To run, update the variables in Lines 13-17 accordingly and adjust Lines 57-60 as needed

import os
import requests
import json
import subprocess
from github import Github
from github import Auth

# Update these variables
lightdash_url = 'https://app.lightdash.cloud/api/v1/' # URL used for Lightdash API requests
api_key = '' # Token for Lightdash API
lightdash_domain = 'https://app.lightdash.cloud/' # URL used to login with Lightdash CLI
github_token = '' # Token for Github API
git_repo = '' # Name of your Github Repo
# Headers for Lightdash API requests
headers = {
    'Authorization': f'ApiKey {api_key}',
    'Content-Type': 'application/json',
}

if __name__ == '__main__':
    ## USE LIGHTDASH API TO GET LIST OF ACTIVE PREVIEW PROJECTS
    # GET request to get list of all active projects
    r = requests.get(f'{lightdash_url}org/projects', headers = headers)
    print(r)
    # Convert response to json and results
    r_json = json.loads(r.text)
    projects = r_json['results']
    # Filter to preview projects only
    previews = []
    for i in range(0, len(projects)):
        if projects[i]['type'] == 'PREVIEW':
            previews.append(projects[i])
    # Print results
    tot_previews = len(previews)
    print(f'Identified {tot_previews} total Lightdash previews')

    ## USE GITHUB API TO GET LIST OF BRANCHES FROM OPEN PR'S (Draft or Ready for Review)
    # Token authentication
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    g.get_user().login
    # Connect to data-platform repo
    repo = g.get_repo(git_repo)
    # Get all open pull requests
    pull_requests = list(repo.get_pulls(base = 'main'))
    # Close connection
    g.close()
    # Convert to list of branch names (delete leading "collectorsgroup:{name}/")
    branches = []
    for i in pull_requests:
        # Isolate head branch name
        val = i.head.label
        # OPTIONAL: If part of an organization, remove '{org_name}:' from beginning of branch name
        new = val.replace('{org_name}:','')
        # OPTIONAL: If using naming convention {author_name}/{branch-name}, remove all characters before '/' and add to list
        idx = new.find('/') + 1
        clean = new[idx:]
        branches.append(clean)
    # Print results
    tot_branches = len(branches)
    print(f'Identified {tot_branches} total branches for open PRs')

    ## COMPARE PREVIEWS TO BRANCHES FROM OPEN PR'S - ID NON-PR PREVIEWS
    to_delete = []
    for i in range(0,len(previews)):
        if previews[i]['name'] not in branches:
            to_delete.append(previews[i])
    # Print results
    tot_deletes = len(to_delete)
    if tot_deletes == 0:
        print('No previews to be deleted, process completed')
    else:
        print(f'Identified {tot_deletes} Lightdash previews to be deleted')

        ## CLOSE UNNEEDED LIGHTDASH PREVIEWS
        to_delete = []
    for i in range(0,len(previews)):
        if previews[i]['name'] not in branches:
            to_delete.append(previews[i])
    # Print results
    tot_deletes = len(to_delete)
    if tot_deletes == 0:
        print('No previews to be deleted, process completed')
    else:
        print(f"Identified {tot_deletes} Lightdash previews to be deleted")
        ## CLOSE UNNEEDED LIGHTDASH PREVIEWS
        deleted = 0
        not_deleted = []
        for i in to_delete:
            print(f"Deleting preview: {i['name']} ...")
            delete = requests.delete(f"{lightdash_url}org/projects/{i['projectUuid']}", headers = headers)
            if delete.status_code == 200:
                deleted += 1
            else:
                not_deleted.append(i)
                print(f"Failed to delete preview: {i['name']}")
        print(f'Successfully deleted {deleted} previews')
        if len(not_deleted) == 0:
            print('No previews failed to be deleted')
        else:
            print(f'Could not delete {len(not_deleted)} previews:')
            for i in not_deleted:
                print(i['name'])
