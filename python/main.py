from lightdash.api_client import LightdashApiClient

# Lightdash space to copy
SOURCE_URL = 'http://localhost:8080/api/v1/'
SOURCE_API_KEY = ''
SOURCE_PROJECT_ID = ''
SOURCE_SPACE_ID = ''

# Lightdash project to create new space
TARGET_URL = 'http://localhost:8080/api/v1/'
TARGET_API_KEY = ''
TARGET_PROJECT_ID = ''

if __name__ == '__main__':
    source = LightdashApiClient(SOURCE_URL, SOURCE_API_KEY, SOURCE_PROJECT_ID)
    space = source.space(SOURCE_SPACE_ID, summary=False)

    target = LightdashApiClient(TARGET_URL, TARGET_API_KEY, TARGET_PROJECT_ID)
    target.create_space(space)
