# This script will delete all empty Spaces in a given Project
from lightdash.api_client import LightdashApiClient

# Update these variables
TARGET_URL = 'https://app.lightdash.cloud/api/v1/'
TARGET_API_KEY = '' # Your personal Personal Access Token from Lightdash
TARGET_PROJECT_ID = '5a5e6741-cc9b-49d5-89b1-86c2639f155e' # Project ID to delete empty Spaces

if __name__ == '__main__':
    target_client = LightdashApiClient(TARGET_URL, TARGET_API_KEY, TARGET_PROJECT_ID)
    
    # Get all spaces
    print('Getting all spaces')
    all_spaces = target_client.spaces(summary=True)

    # Identify empty spaces
    print('Identifying empty spaces')
    empty_spaces = []
    for space in all_spaces:
        if space['chartCount'] == '0' and space['dashboardCount'] == '0':
            empty_spaces.append([space['uuid'], space['name']])
    print(f'Identified {len(empty_spaces)} empty spaces to delete')
    
    # Delete empty spaces Sapces
    print('Deleting empty spaces . . .')
    for i in empty_spaces:
        print(f'Deleting space: {i[1]}')
        target_client.delete_space(i[0])
    print('All empty spaces deleted!')