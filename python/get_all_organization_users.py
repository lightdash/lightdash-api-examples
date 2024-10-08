import requests
import pandas as pd

API_URL = 'https://<yourinstance>.lightdash.cloud/api/v1/org/users'
API_KEY = '<yourkey>'
EXPORT_METHOD = 'excel' # or 'csv'

session = requests.Session()
session.headers.update({
    'Authorization': f'ApiKey {API_KEY}',
    'Content-Type': 'application/json',
})

def fetch_users(page=1, page_size=10, include_groups=10000):
    params = {
        'page': page,
        'pageSize': page_size,
        'includeGroups': include_groups,
    }
    response = session.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def parse_users(data):
    users = []
    for user in data['results']['data']:
        groups = ', '.join(group['name'] for group in user.get('groups', []))
        users.append({
            'Name': f"{user['firstName']} {user['lastName']}".strip(),
            'Email': user['email'],
            'Role': user['role'],
            'Groups': groups,
        })
    return users

def fetch_all_users():
    all_users = []
    page = 1
    page_size = 10

    while True:
        result = fetch_users(page=page, page_size=page_size)
        users_data = parse_users(result)
        all_users.extend(users_data)

        # Check if there are more pages
        total_pages = result['results']['pagination']['totalPageCount']
        if page >= total_pages:
            break
        page += 1

    return all_users

all_users_data = fetch_all_users()

df = pd.DataFrame(all_users_data)

if EXPORT_METHOD == 'excel':
    df.to_excel('lightdash_users.xlsx', index=False)
    print("Excel export successful!: lightdash_users.xlsx")
elif EXPORT_METHOD == 'csv':
    df.to_csv('lightdash_users.csv', index=False)
    print("CSV export successful!: lightdash_users.csv")
else:
    raise ValueError(f"Invalid export method: {EXPORT_METHOD}. Use 'csv' or 'excel'.")