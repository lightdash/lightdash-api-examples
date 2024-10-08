import requests
import pandas as pd

API_URL = 'https://<yourinstance>.lightdash.cloud/api/v1/org/groups'
API_KEY = '<yourkey>'
EXPORT_METHOD = 'excel' # or 'csv'

session = requests.Session()
session.headers.update({
    'Authorization': f'ApiKey {API_KEY}',
    'Content-Type': 'application/json',
})

def fetch_groups(include_members=10_000):
    params = {
        'includeMembers': include_members,
    }
    response = session.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def parse_groups(data):
    users = []
    for group in data['results']:
        group_name = group['name']
        for member in group['members']:
            users.append({
                'Group': group_name,
                'Email': member['email'],
                'Name': f"{member['firstName']} {member['lastName']}".strip(),
            })
    return users

def fetch_all_groups():
    result = fetch_groups()
    all_users = parse_groups(result)

    return all_users

all_users_data = fetch_all_groups()

df = pd.DataFrame(all_users_data)

if EXPORT_METHOD == 'excel':
    df.to_excel('lightdash_groups.xlsx', index=False)
    print("Excel export successful!")
elif EXPORT_METHOD == 'csv':
    df.to_csv('lightdash_groups.csv', index=False)
    print("CSV export successful!")
else:
    raise ValueError(f"Invalid export method: {EXPORT_METHOD}. Use 'csv' or 'excel'.")