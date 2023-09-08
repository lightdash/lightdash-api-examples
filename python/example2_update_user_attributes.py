from lightdash.api_client import LightdashApiClient
import pandas as pd

# Update these variables
TARGET_URL = 'https://app.lightdash.cloud/api/v1/'
TARGET_API_KEY = ''
CSV_FILEPATH = '~/Documents/user_permission_list.csv' #This file should have "email" and "role" columns
ATTRIBUTE_NAME = ""


if __name__ == "__main__":
    target = LightdashApiClient(TARGET_URL, TARGET_API_KEY)
    df_user_perms_to_grant = pd.read_csv(USER_PERMS_FILEPATH)

    print("Getting all users")
    all_users = target.users()
    print("Getting all user attributes")
    all_attributes = target.user_attributes()

    print(f"Find attribute with name {ATTRIBUTE_NAME}")
    attribute = [ua for ua in all_attributes if ua["name"] == ATTRIBUTE_NAME][0]

    new_user_attribute_values = {}
    # Convert current user attribute values to dictionary
    for index, i in enumerate(attribute["users"]):
        new_user_attribute_values[i["userUuid"]] = {
            "userUuid": i["userUuid"],
            "value": i["value"],
        }
    # Update dictionary with new values
    for idx, user_attribute_value in enumerate(USER_ATTRIBUTE_VALUES):
        print(f'Find user with email {user_attribute_value["email"]}')
        user = [u for u in all_users if u["email"] == user_attribute_value["email"]][0]
        new_user_attribute_values[user["userUuid"]] = {
            "userUuid": user["userUuid"],
            "value": user_attribute_value["value"],
        }

    print(f'Updating user attribute {attribute["name"]}')
    target.update_user_attribute(
        attribute["uuid"],
        {
            "name": attribute["name"],
            "description": attribute["description"],
            "users": list(new_user_attribute_values.values()),
        },
    )
