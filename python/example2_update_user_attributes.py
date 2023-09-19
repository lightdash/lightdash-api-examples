from lightdash.api_client import LightdashApiClient
import pandas as pd

# Update these variables
TARGET_URL = 'http://localhost:3000/api/v1/'
TARGET_API_KEY = 'fbf7a899dc3e616e5cacd1fa92588425'
CSV_FILEPATH = '~/Documents/test.csv' #This file should have "email" and "value" columns
ATTRIBUTE_NAME = 'fruit'


if __name__ == "__main__":
    target = LightdashApiClient(TARGET_URL, TARGET_API_KEY)
    df_user_attributes_to_grant = pd.read_csv(CSV_FILEPATH)

    print("Getting all users")
    df_users = pd.DataFrame.from_dict(target.users(), orient='columns')
    print("Getting all user attributes")
    df_user_attributes=pd.DataFrame.from_dict(target.user_attributes(), orient='columns')

    if df_user_attributes.empty:
        print(f"Exit: Organization has no user attributes")
        exit(1)

    print(f"Find attribute with name: {ATTRIBUTE_NAME}")
    attribute = df_user_attributes[df_user_attributes['name'] == ATTRIBUTE_NAME].iloc[0]

    new_user_attribute_values = {}
    # Convert current user attribute values to dictionary
    for index, i in enumerate(attribute["users"]):
        new_user_attribute_values[i["userUuid"]] = {
            "userUuid": i["userUuid"],
            "value": i["value"],
        }
    # Update dictionary with new values
    for idx, row in df_user_attributes_to_grant.iterrows():
        email = row["email"]
        value = row["value"]
        print(f'Find user with email: {email}')
        match_users = df_users[df_users['email'] == email]

        if match_users.empty:
            print(f'Skipping: User {email} does not exist in organization')
        else:
            print(f'Updating attribute {ATTRIBUTE_NAME} for {email} to {value}')
            userUuid = match_users.iloc[0]["userUuid"]
            new_user_attribute_values[userUuid] = {
                "userUuid": userUuid,
                "value": value,
            }

    new_user_attribute_values = {
        "name": attribute["name"],
        "users": list(new_user_attribute_values.values()),
    }

    if "description" in attribute:
        new_user_attribute_values["description"] = attribute["description"]

    if "attributeDefault" in attribute:
        new_user_attribute_values["attributeDefault"] = attribute["attributeDefault"]

    target.update_user_attribute(
        attribute["uuid"],
        new_user_attribute_values,
    )
    print(f'Updated user attributes with success')
