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
    
    # Handle different possible response structures
    groups_data = None
    if isinstance(data, dict):
        if 'results' in data and isinstance(data['results'], dict) and 'data' in data['results']:
            # Structure: {"status": "ok", "results": {"data": [groups]}}
            groups_data = data['results']['data']
        elif 'results' in data and isinstance(data['results'], list):
            # Structure: {"results": [groups]}
            groups_data = data['results']
        elif 'data' in data:
            # Structure: {"data": [groups]}
            groups_data = data['data']
        else:
            return users
    elif isinstance(data, list):
        groups_data = data
    else:
        return users
    
    for group in groups_data:
        if not isinstance(group, dict):
            continue
            
        group_name = group.get('name', 'Unknown Group')
        
        # Handle different member structures
        members = []
        if 'members' in group:
            members = group['members']
        elif 'memberUuids' in group:
            # If we only have UUIDs, we can't get names/emails
            continue
        else:
            continue
        
        for member in members:
            if not isinstance(member, dict):
                continue
                
            email = member.get('email', 'Unknown Email')
            first_name = member.get('firstName', '')
            last_name = member.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip() or 'Unknown Name'
            
            users.append({
                'Group': group_name,
                'Email': email,
                'Name': full_name,
            })
    
    return users

def fetch_all_groups():
    result = fetch_groups()
    all_users = parse_groups(result)
    return all_users

if __name__ == "__main__":
    # Validate API token
    if not API_KEY or API_KEY == "YOUR_API_TOKEN":
        print("❌ Error: Please update API_KEY in the script with your actual API token.")
        exit(1)
    
    try:
        all_users_data = fetch_all_groups()
        
        if not all_users_data:
            print("⚠️  No user data found.")
        else:
            df = pd.DataFrame(all_users_data)
            
            if EXPORT_METHOD == 'excel':
                filename = 'lightdash_groups.xlsx'
                df.to_excel(filename, index=False)
                print(f"✅ Excel export successful: {filename}")
            elif EXPORT_METHOD == 'csv':
                filename = 'lightdash_groups.csv'
                df.to_csv(filename, index=False)
                print(f"✅ CSV export successful: {filename}")
            else:
                raise ValueError(f"Invalid export method: {EXPORT_METHOD}. Use 'csv' or 'excel'.")
            
            # Show summary
            print(f"\n📊 Summary:")
            print(f"Total users exported: {len(all_users_data)}")
            print(f"Unique groups: {df['Group'].nunique() if not df.empty else 0}")
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        raise