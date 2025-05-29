#!/usr/bin/env python3
import json
from typing import Dict, List, Any
from lightdash.api_client import LightdashApiClient

# How to run: 
# poetry run python get_complete_project_access.py

# Update these with your values
BASE_URL = "https://YOUR_LIGHTDASH_BASE_URL.lightdash.cloud/api/v1/"
PROJECT_UUID = "YOUR_PROJECT_UUID"  # Replace with actual project UUID
API_TOKEN = "YOUR_API_TOKEN"  # Replace with actual API token

def fetch_all_org_users(client: LightdashApiClient) -> List[Dict[str, Any]]:
    """Fetch all organization users with pagination"""
    all_users = []
    page = 1
    page_size = 50  
    
    while True:
        result = client.org_users_with_pagination(page=page, page_size=page_size)
        users_data = result.get('data', [])
        all_users.extend(users_data)
        
        # Check if there are more pages
        pagination = result.get('pagination', {})
        total_pages = pagination.get('totalPageCount', 1)
        if page >= total_pages:
            break
        page += 1
    
    return all_users

def get_complete_project_access(client: LightdashApiClient, project_uuid: str):
    """Get complete project access information using the API client"""
    print(f"Fetching complete project access for: {project_uuid}")
    print("=" * 60)
    
    # Fetch all required data using the API client
    print("📊 Fetching organization users...")
    org_users = fetch_all_org_users(client)
    
    print("🔑 Fetching project access list...")
    project_access = client.get_project_access_list(project_uuid)
    
    print("👥 Fetching project group access...")
    project_groups = client.project_group_accesses(project_uuid)
    
    print("🏢 Fetching organization groups...")
    org_groups_response = client.org_groups()
    org_groups = org_groups_response.get('data', []) if isinstance(org_groups_response, dict) else org_groups_response
    
    # Create lookup dictionaries
    group_lookup = {g["uuid"]: g for g in org_groups}
    project_roles = {u["userUuid"]: u["role"] for u in project_access}
    
    # Calculate group-based access
    group_access = {}
    for group_access_item in project_groups:
        group_uuid = group_access_item["groupUuid"]
        group_role = group_access_item["role"]
        
        if group_uuid in group_lookup:
            group = group_lookup[group_uuid]
            # Handle both 'memberUuids' and 'members' formats
            member_uuids = []
            if 'memberUuids' in group:
                member_uuids = group['memberUuids']
            elif 'members' in group:
                member_uuids = [m['userUuid'] for m in group['members']]
            
            for member_uuid in member_uuids:
                if member_uuid not in group_access:
                    group_access[member_uuid] = []
                group_access[member_uuid].append({
                    "groupName": group["name"],
                    "role": group_role
                })
    
    # Generate complete user list
    complete_access = []
    for user in org_users:
        user_uuid = user["userUuid"]
        access_sources = []
        
        # Organization-level access
        if user["role"] in ["admin", "editor"]:
            access_sources.append({
                "type": "organization",
                "role": user["role"],
                "source": f"Organization {user['role']}"
            })
        
        # Group-based access
        if user_uuid in group_access:
            for group_info in group_access[user_uuid]:
                access_sources.append({
                    "type": "group",
                    "role": group_info["role"],
                    "source": f"Group: {group_info['groupName']}"
                })
        
        # Direct project access
        if user_uuid in project_roles:
            access_sources.append({
                "type": "project",
                "role": project_roles[user_uuid],
                "source": "Direct project membership"
            })
        
        if access_sources:
            # Determine highest role
            role_hierarchy = ["viewer", "interactive_viewer", "editor", "developer", "admin"]
            highest_role = max(access_sources, 
                             key=lambda x: role_hierarchy.index(x["role"]) if x["role"] in role_hierarchy else 0)
            
            complete_access.append({
                "name": f"{user['firstName']} {user['lastName']}",
                "email": user["email"],
                "userUuid": user_uuid,
                "finalRole": highest_role["role"],
                "accessSources": access_sources
            })
    
    return complete_access, {
        "totalOrgUsers": len(org_users),
        "directProjectMembers": len(project_access),
        "groupsWithAccess": len(project_groups),
        "usersWithAccess": len(complete_access)
    }

if __name__ == "__main__":
    # Validate required parameters
    if not API_TOKEN or API_TOKEN == "YOUR_API_TOKEN":
        print("❌ Error: Please update API_TOKEN in the script with your actual API token.")
        exit(1)
    
    if not PROJECT_UUID or PROJECT_UUID == "YOUR_PROJECT_UUID":
        print("❌ Error: Please update PROJECT_UUID in the script with your actual project UUID.")
        exit(1)
    
    try:
        # Initialize the API client
        print("🔐 Initializing Lightdash API client...")
        client = LightdashApiClient(BASE_URL, API_TOKEN, PROJECT_UUID)
        
        print("🔍 Starting data fetch...")
        
        users_with_access, stats = get_complete_project_access(client, PROJECT_UUID)
        
        print("\n📊 STATISTICS:")
        print("-" * 30)
        print(f"Total organization users: {stats['totalOrgUsers']}")
        print(f"Users with project access: {stats['usersWithAccess']}")
        print(f"Direct project members: {stats['directProjectMembers']}")
        print(f"Groups with project access: {stats['groupsWithAccess']}")
        
        print("\n👥 USERS WITH PROJECT ACCESS:")
        print("-" * 50)
        
        for user in sorted(users_with_access, key=lambda x: x["name"]):
            print(f"\n• {user['name']} ({user['email']})")
            print(f"  Final Role: {user['finalRole']}")
            print("  Access Sources:")
            for source in user["accessSources"]:
                print(f"    - {source['source']} (role: {source['role']})")
        
        # Export to JSON
        output_filename = f"project_access_{PROJECT_UUID}.json"
        with open(output_filename, "w") as f:
            json.dump({
                "projectUuid": PROJECT_UUID,
                "stats": stats,
                "usersWithAccess": users_with_access
            }, f, indent=2)
        
        print(f"\n💾 Results exported to: {output_filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}") 