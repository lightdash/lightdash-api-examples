from lightdash.api_client import LightdashApiClient

# Lightdash configuration
TARGET_URL = 'https://{YOUR_INSTANCE_URL}.lightdash.cloud/api/v1/'
TARGET_API_KEY = ''
TARGET_PROJECT_ID = ''
# Define the space hierarchy to be created
SPACE_HIERARCHY = [
    {
        "name": "Marketing",
        "isPrivate": False,
        "children": [
            {
                "name": "Campaigns",
                "isPrivate": False,
                "children": [
                    {
                        "name": "Email Campaigns",
                        "isPrivate": True,
                        "children": []
                    },
                    {
                        "name": "Social Media",
                        "isPrivate": False,
                        "children": [
                            {
                                "name": "Facebook",
                                "isPrivate": False,
                                "children": []
                            },
                            {
                                "name": "Twitter",
                                "isPrivate": False,
                                "children": []
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Analytics",
                "isPrivate": False,
                "children": [
                    {
                        "name": "Web Analytics",
                        "isPrivate": False,
                        "children": []
                    },
                    {
                        "name": "Customer Analytics",
                        "isPrivate": True,
                        "children": []
                    }
                ]
            }
        ]
    },
    {
        "name": "Sales",
        "isPrivate": False,
        "children": [
            {
                "name": "Lead Generation",
                "isPrivate": False,
                "children": []
            },
            {
                "name": "Revenue Tracking",
                "isPrivate": True,
                "children": []
            }
        ]
    }
]

def create_space_tree(client, space_config, parent_path="", parent_uuid=None, created_spaces=None):
    """
    Recursively create spaces according to the hierarchy defined in space_config
    
    Args:
        client: LightdashApiClient instance
        space_config: Dictionary defining the space and its children
        parent_path: String representing the path to the parent (for logging)
        parent_uuid: UUID of the parent space
        created_spaces: List to track created spaces
    
    Returns:
        Dictionary containing the created space information
    """
    if created_spaces is None:
        created_spaces = []
    
    # Create current space
    space_data = {
        'name': space_config['name'],
        'isPrivate': space_config.get('isPrivate', False)
    }
    
    # Set parent space UUID if this is a child space
    if parent_uuid:
        space_data['parentSpaceUuid'] = parent_uuid
    
    current_path = f"{parent_path}/{space_config['name']}" if parent_path else space_config['name']
    print(f"Creating space: {current_path}")
    
    try:
        created_space = client.create_empty_space(space_data)
        created_spaces.append({
            'path': current_path,
            'name': space_config['name'],
            'uuid': created_space['uuid'],
            'isPrivate': space_config.get('isPrivate', False),
            'parentSpaceUuid': parent_uuid
        })
        print(f"✓ Successfully created space: {current_path} (UUID: {created_space['uuid']})")
        
        # Create child spaces with this space as their parent
        for child in space_config.get('children', []):
            create_space_tree(client, child, current_path, created_space['uuid'], created_spaces)
            
        return created_space
        
    except Exception as e:
        print(f"✗ Failed to create space: {current_path}")
        print(f"  Error: {str(e)}")
        return None

def print_space_tree(space_configs, indent=0):
    """
    Print a visual representation of the space hierarchy
    """
    if isinstance(space_configs, dict):
        space_configs = [space_configs]
    
    for space_config in space_configs:
        prefix = "  " * indent + ("├── " if indent > 0 else "")
        privacy_indicator = "🔒" if space_config.get('isPrivate', False) else "🌐"
        print(f"{prefix}{privacy_indicator} {space_config['name']}")
        
        for child in space_config.get('children', []):
            print_space_tree(child, indent + 1)

if __name__ == '__main__':
    if not TARGET_API_KEY or not TARGET_PROJECT_ID:
        print("Please set TARGET_API_KEY and TARGET_PROJECT_ID before running this script")
        exit(1)
    
    print("Space hierarchy to be created:")
    print("=" * 50)
    print_space_tree(SPACE_HIERARCHY)
    print("=" * 50)
    
    client = LightdashApiClient(TARGET_URL, TARGET_API_KEY, TARGET_PROJECT_ID)
    
    print("\nStarting space creation...")
    created_spaces = []
    for root_space in SPACE_HIERARCHY:
        create_space_tree(client, root_space, created_spaces=created_spaces)
    
    print(f"\nSpace creation completed!")
    print(f"Total spaces created: {len(created_spaces)}")
    print("\nCreated spaces summary:")
    print("-" * 50)
    for space in created_spaces:
        privacy_indicator = "🔒" if space['isPrivate'] else "🌐"
        print(f"{privacy_indicator} {space['path']} (UUID: {space['uuid']})")