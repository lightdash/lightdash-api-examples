from lightdash.api_client import LightdashApiClient
import pandas as pd

TARGET_URL = 'https://app.lightdash.cloud/api/v1/'
TARGET_API_KEY = ''
TARGET_PROJECT_ID = ''
USER_PERMS_FILEPATH = '~/Documents/my_file.csv' #This file should have "email" and "role" columns
ROLES=['viewer', 'interactive_viewer', 'editor', 'developer', 'admin']

if __name__ == '__main__':
    target = LightdashApiClient(TARGET_URL, TARGET_API_KEY, TARGET_PROJECT_ID)
    df_user_perms_to_grant = pd.read_csv(USER_PERMS_FILEPATH)

    # Get all organization and project access attributes for users on the permission list into one dataframe
    df_org_users=pd.DataFrame.from_dict(target.users(), orient='columns')
    df_user_perms_to_grant=df_user_perms_to_grant.join(df_org_users.set_index('email'), on='email', rsuffix='_org')

    df_user_access_current = pd.DataFrame.from_dict(target.get_project_access_list(TARGET_PROJECT_ID), orient='columns')
    df_user_access_current.columns=['user_uuid', 'email', 'current_role', 'first_name','project_uuid','last_name']
    df_combined = df_user_perms_to_grant.join(df_user_access_current.set_index('email'), on='email')

    for index, row in df_combined.iterrows():        
        email = row['email']
        new_role = row['role']
        current_role = row['current_role']
        has_existing_project_role = row['current_role'] is not None
        has_existing_org_role = row['role_org'] is not None       
        access_json = {'sendEmail': False, 'role': new_role, 'email': email}
        role_json = {'role':new_role}       

        if not has_existing_org_role:
            print(f'User {email} does not exist in organization')
            continue
        elif not has_existing_project_role:
            print(f'Granting role {new_role} to {email}')
            target.grant_project_access_to_user(TARGET_PROJECT_ID, access)
        elif ROLES.index(current_role) < ROLES.index(new_role):
            print(f'Updating role for {email} from {current_role} to {new_role}')
            target.update_project_access_for_user(TARGET_PROJECT_ID, row['user_uuid'], role_json)
        elif ROLES.index(current_role) >= ROLES.index(new_role):
            print(f'Skipping: {email} already has {current_role} access')
            
    