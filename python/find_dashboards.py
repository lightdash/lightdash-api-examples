#!/usr/bin/env python3
"""
Fetch all dashboards from a specific Lightdash project using the v2 Content API

This script helps with dashboard cleanup by providing:
- Complete list of all dashboards with metadata for a specific project
- View counts and first viewed dates
- Creation and last modification dates
- Dashboard organization by spaces
- Cleanup recommendations based on usage patterns

REQUIRED CONFIGURATION:
- API_URL: Your Lightdash instance URL
- API_KEY: Your personal access token
- PROJECT_UUID: The specific project UUID to analyze (REQUIRED for security)

NOTE: The Lightdash API does not currently provide "last viewed" dates.
For true usage analytics, you'll need to query your database using
Lightdash query tags as mentioned in the documentation:
https://docs.lightdash.com/references/usage-analytics#query-tags
"""

import requests
import pandas as pd
from typing import List, Dict, Any
import json

# Configuration
API_URL = 'https://{YOUR_INSTANCE_URL}.lightdash.cloud'  # Update with your instance URL
API_KEY = ''  # Update with your API key
PROJECT_UUID = ''  # REQUIRED: Update with your project UUID
EXPORT_METHOD = 'csv'  # or 'csv' or 'json'

# you can run this script with: poetry run python find_dashboards.py

session = requests.Session()
session.headers.update({
    'Authorization': f'ApiKey {API_KEY}',
    'Content-Type': 'application/json',
})

def fetch_content_page(page: int = 1, page_size: int = 100, project_uuids: List[str] = None) -> Dict[str, Any]:
    """Fetch a single page of dashboard content"""
    endpoint = f"{API_URL}/api/v2/content"
    
    params = {
        'contentTypes': 'dashboard',  # Only fetch dashboards
        'page': page,
        'pageSize': page_size,
        'sortBy': 'name',
        'sortDirection': 'asc'
    }
    
    # Add project filters if specified
    if project_uuids:
        params['projectUuids'] = project_uuids
    
    response = session.get(endpoint, params=params)
    response.raise_for_status()
    return response.json()

def fetch_all_dashboards(project_uuids: List[str]) -> List[Dict[str, Any]]:
    """Fetch all dashboards with pagination"""
    all_dashboards = []
    page = 1
    page_size = 100
    
    while True:
        print(f"📄 Fetching page {page}...", end=" ", flush=True)
        data = fetch_content_page(page, page_size, project_uuids)
        
        # Extract dashboards from response
        if 'results' in data and 'data' in data['results']:
            dashboards = data['results']['data']
            all_dashboards.extend(dashboards)
            print(f"✓ ({len(dashboards)} dashboards)")
            
            # Check if there are more pages
            pagination = data['results'].get('pagination', {})
            total_pages = pagination.get('totalPages', 1)
            
            if page >= total_pages:
                print(f"📝 Completed fetching {total_pages} page(s)")
                break
            page += 1
        else:
            print("⚠️  Unexpected response structure")
            break
    
    return all_dashboards

def parse_dashboards(dashboards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse dashboard data into a structured format"""
    parsed_data = []
    
    for dashboard in dashboards:
        # Extract nested data safely
        project_info = dashboard.get('project', {})
        organization_info = dashboard.get('organization', {})
        space_info = dashboard.get('space', {})
        created_by = dashboard.get('createdBy', {})
        last_updated_by = dashboard.get('lastUpdatedBy', {})
        
        # Create full name for users
        created_by_name = ''
        if created_by:
            first_name = created_by.get('firstName') or ''
            last_name = created_by.get('lastName') or ''
            created_by_name = f"{first_name} {last_name}".strip()
        
        updated_by_name = ''
        if last_updated_by:
            first_name = last_updated_by.get('firstName') or ''
            last_name = last_updated_by.get('lastName') or ''
            updated_by_name = f"{first_name} {last_name}".strip()
        
        parsed_data.append({
            'uuid': dashboard.get('uuid', ''),
            'name': dashboard.get('name', ''),
            'slug': dashboard.get('slug', ''),
            'description': dashboard.get('description', ''),
            'content_type': dashboard.get('contentType', ''),
            'created_at': dashboard.get('createdAt', ''),
            'created_by': {
                'uuid': created_by.get('uuid', '') if created_by else '',
                'name': created_by_name,
                'first_name': created_by.get('firstName', '') if created_by else '',
                'last_name': created_by.get('lastName', '') if created_by else ''
            },
            'last_updated_at': dashboard.get('lastUpdatedAt', ''),
            'last_updated_by': {
                'uuid': last_updated_by.get('uuid', '') if last_updated_by else '',
                'name': updated_by_name,
                'first_name': last_updated_by.get('firstName', '') if last_updated_by else '',
                'last_name': last_updated_by.get('lastName', '') if last_updated_by else ''
            },
            'project': {
                'uuid': project_info.get('uuid', ''),
                'name': project_info.get('name', '')
            },
            'organization': {
                'uuid': organization_info.get('uuid', ''),
                'name': organization_info.get('name', '')
            },
            'space': {
                'uuid': space_info.get('uuid', ''),
                'name': space_info.get('name', '')
            },
            'views': dashboard.get('views', 0),
            'first_viewed_at': dashboard.get('firstViewedAt', ''),
            'pinned_list_uuid': dashboard.get('pinnedList', {}).get('uuid', '') if dashboard.get('pinnedList') else None,
            'is_pinned': dashboard.get('pinnedList') is not None,
            'has_description': bool((dashboard.get('description') or '').strip()),
            'url_slug': dashboard.get('slug', ''),
            # Additional computed fields for analysis
            'days_since_creation': None,  # Will be computed if needed
            'days_since_last_update': None,  # Will be computed if needed
        })
    
    return parsed_data

def export_dashboards(dashboards: List[Dict[str, Any]], export_method: str = 'excel'):
    """Export dashboards to file"""
    if not dashboards:
        print("⚠️  No dashboards to export.")
        return
    
    if export_method == 'json':
        filename = 'lightdash_dashboards.json'
        
        # Create comprehensive JSON structure with metadata
        from datetime import datetime
        
        # Calculate summary statistics
        total_dashboards = len(dashboards)
        unique_projects = len(set(d['project']['uuid'] for d in dashboards if d['project']['uuid']))
        unique_spaces = len(set(d['space']['uuid'] for d in dashboards if d['space']['uuid']))
        unique_organizations = len(set(d['organization']['uuid'] for d in dashboards if d['organization']['uuid']))
        total_views = sum(d.get('views', 0) for d in dashboards)
        dashboards_with_descriptions = sum(1 for d in dashboards if d.get('has_description'))
        pinned_dashboards = sum(1 for d in dashboards if d.get('is_pinned'))
        
        # Group by project for easy analysis
        dashboards_by_project = {}
        dashboards_by_space = {}
        
        for dashboard in dashboards:
            project_name = dashboard['project']['name']
            space_name = dashboard['space']['name']
            
            if project_name not in dashboards_by_project:
                dashboards_by_project[project_name] = []
            dashboards_by_project[project_name].append(dashboard)
            
            if space_name not in dashboards_by_space:
                dashboards_by_space[space_name] = []
            dashboards_by_space[space_name].append(dashboard)
        
        # Create structured output
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'api_url': API_URL,
                'project_uuid': PROJECT_UUID,
                'project_name': dashboards[0]['project']['name'] if dashboards else 'Unknown',
                'total_dashboards': total_dashboards,
                'unique_projects': unique_projects,
                'unique_spaces': unique_spaces,
                'unique_organizations': unique_organizations,
                'total_views': total_views,
                'dashboards_with_descriptions': dashboards_with_descriptions,
                'pinned_dashboards': pinned_dashboards,
                'export_method': export_method
            },
            'summary_stats': {
                'projects': {name: len(dashes) for name, dashes in dashboards_by_project.items()},
                'spaces': {name: len(dashes) for name, dashes in dashboards_by_space.items()},
                'top_viewed_dashboards': sorted(
                    [{'name': d['name'], 'views': d['views'], 'project': d['project']['name']} 
                     for d in dashboards], 
                    key=lambda x: x['views'], reverse=True
                )[:10]
            },
            'dashboards': dashboards,
            'dashboards_by_project': dashboards_by_project,
            'dashboards_by_space': dashboards_by_space
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
        print(f"✅ Enhanced JSON export successful: {filename}")
        print(f"   📊 Exported {total_dashboards} dashboards with metadata and groupings")
    else:
        # Create flattened DataFrame for Excel/CSV export
        flattened_data = []
        for dashboard in dashboards:
            flattened_data.append({
                'UUID': dashboard.get('uuid', ''),
                'Name': dashboard.get('name', ''),
                'Slug': dashboard.get('slug', ''),
                'Description': dashboard.get('description') or '',
                'Content Type': dashboard.get('content_type', ''),
                'Created At': dashboard.get('created_at', ''),
                'Created By Name': dashboard.get('created_by', {}).get('name', ''),
                'Created By UUID': dashboard.get('created_by', {}).get('uuid', ''),
                'Last Updated At': dashboard.get('last_updated_at', ''),
                'Last Updated By Name': dashboard.get('last_updated_by', {}).get('name', ''),
                'Last Updated By UUID': dashboard.get('last_updated_by', {}).get('uuid', ''),
                'Project UUID': dashboard.get('project', {}).get('uuid', ''),
                'Project Name': dashboard.get('project', {}).get('name', ''),
                'Organization UUID': dashboard.get('organization', {}).get('uuid', ''),
                'Organization Name': dashboard.get('organization', {}).get('name', ''),
                'Space UUID': dashboard.get('space', {}).get('uuid', ''),
                'Space Name': dashboard.get('space', {}).get('name', ''),
                'Views': dashboard.get('views', 0),
                'First Viewed At': dashboard.get('first_viewed_at', ''),
                'Pinned List UUID': dashboard.get('pinned_list_uuid', ''),
                'Is Pinned': dashboard.get('is_pinned', False),
                'Has Description': dashboard.get('has_description', False),
                'URL Slug': dashboard.get('url_slug', '')
            })
        
        df = pd.DataFrame(flattened_data)
        
        if export_method == 'excel':
            filename = 'lightdash_dashboards.xlsx'
            # Create Excel with multiple sheets for better organization
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main dashboard data
                df.to_excel(writer, sheet_name='Dashboards', index=False)
                
                # Summary statistics
                summary_df = pd.DataFrame({
                    'Metric': [
                        'Total Dashboards',
                        'Unique Organizations',
                        'Unique Projects',
                        'Unique Spaces',
                        'Dashboards with Description',
                        'Pinned Dashboards',
                        'Total Views',
                        'Average Views per Dashboard'
                    ],
                    'Value': [
                        len(df),
                        df['Organization UUID'].nunique(),
                        df['Project UUID'].nunique(),
                        df['Space UUID'].nunique(),
                        df['Has Description'].sum(),
                        df['Is Pinned'].sum(),
                        df['Views'].sum(),
                        df['Views'].mean() if not df.empty else 0
                    ]
                })
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Dashboards by project
                project_summary = df.groupby('Project Name').agg({
                    'Name': 'count',
                    'Views': ['sum', 'mean'],
                    'Has Description': 'sum'
                }).round(2)
                project_summary.columns = ['Dashboard Count', 'Total Views', 'Avg Views', 'With Description']
                project_summary = project_summary.reset_index().sort_values('Dashboard Count', ascending=False)
                project_summary.to_excel(writer, sheet_name='By Project', index=False)
                
                # Dashboards by space
                space_summary = df.groupby('Space Name').agg({
                    'Name': 'count',
                    'Views': ['sum', 'mean'],
                    'Has Description': 'sum'
                }).round(2)
                space_summary.columns = ['Dashboard Count', 'Total Views', 'Avg Views', 'With Description']
                space_summary = space_summary.reset_index().sort_values('Dashboard Count', ascending=False)
                space_summary.to_excel(writer, sheet_name='By Space', index=False)
                
                # Top creators
                creator_summary = df[df['Created By Name'] != ''].groupby('Created By Name').agg({
                    'Name': 'count',
                    'Views': 'sum'
                }).rename(columns={'Name': 'Dashboards Created', 'Views': 'Total Views on Created Dashboards'})
                creator_summary = creator_summary.reset_index().sort_values('Dashboards Created', ascending=False)
                creator_summary.to_excel(writer, sheet_name='Top Creators', index=False)
                
            print(f"✅ Enhanced Excel export successful: {filename}")
            print(f"   📊 Created sheets: Dashboards, Summary, By Project, By Space, Top Creators")
            
        elif export_method == 'csv':
            filename = 'lightdash_dashboards.csv'
            df.to_csv(filename, index=False)
            print(f"✅ CSV export successful: {filename}")
            
            # Also create a dashboard cleanup-focused CSV
            cleanup_filename = 'lightdash_dashboards_cleanup.csv'
            cleanup_data = []
            for dashboard in dashboards:
                # Calculate days since creation and last update
                from datetime import datetime
                try:
                    created_date = datetime.fromisoformat(dashboard.get('created_at', '').replace('Z', '+00:00'))
                    days_since_creation = (datetime.now(created_date.tzinfo) - created_date).days
                except:
                    days_since_creation = None
                
                try:
                    updated_date = datetime.fromisoformat(dashboard.get('last_updated_at', '').replace('Z', '+00:00'))
                    days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days
                except:
                    days_since_update = None
                
                # Cleanup recommendation
                views = dashboard.get('views', 0)
                cleanup_recommendation = ""
                if views == 0:
                    cleanup_recommendation = "NEVER_VIEWED - Consider archiving"
                elif views <= 5:
                    cleanup_recommendation = "LOW_ENGAGEMENT - Review usage"
                elif days_since_update and days_since_update > 180:
                    cleanup_recommendation = "STALE - Not updated in 6+ months"
                elif not dashboard.get('has_description'):
                    cleanup_recommendation = "NO_DESCRIPTION - Add description"
                else:
                    cleanup_recommendation = "ACTIVE - Keep"
                
                cleanup_data.append({
                    'Dashboard_Name': dashboard.get('name', ''),
                    'Dashboard_UUID': dashboard.get('uuid', ''),
                    'Project_Name': dashboard.get('project', {}).get('name', ''),
                    'Space_Name': dashboard.get('space', {}).get('name', ''),
                    'Total_Views': views,
                    'Created_Date': dashboard.get('created_at', '')[:10],
                    'Last_Updated_Date': dashboard.get('last_updated_at', '')[:10],
                    'Days_Since_Creation': days_since_creation,
                    'Days_Since_Update': days_since_update,
                    'Has_Description': dashboard.get('has_description', False),
                    'Is_Pinned': dashboard.get('is_pinned', False),
                    'First_Viewed_Date': dashboard.get('first_viewed_at', '')[:10] if dashboard.get('first_viewed_at') else '',
                    'Cleanup_Recommendation': cleanup_recommendation,
                    'Dashboard_URL_Slug': dashboard.get('slug', '')
                })
            
            cleanup_df = pd.DataFrame(cleanup_data)
            cleanup_df = cleanup_df.sort_values(['Total_Views', 'Days_Since_Update'], ascending=[True, False])
            cleanup_df.to_csv(cleanup_filename, index=False)
            print(f"✅ Dashboard cleanup CSV created: {cleanup_filename}")
            print(f"   🧹 Sorted by views (lowest first) and staleness for easy cleanup decisions")
        else:
            raise ValueError(f"Invalid export method: {export_method}. Use 'csv', 'excel', or 'json'.")
    
    return filename

def print_dashboard_summary(dashboards: List[Dict[str, Any]]):
    """Print a comprehensive summary of dashboard data to console"""
    if not dashboards:
        print("⚠️  No dashboards to analyze.")
        return
    
    print("\n" + "="*80)
    print("📊 LIGHTDASH DASHBOARD ANALYSIS SUMMARY")
    print("="*80)
    
    # Basic statistics
    total_dashboards = len(dashboards)
    unique_projects = len(set(d['project']['uuid'] for d in dashboards if d['project']['uuid']))
    unique_spaces = len(set(d['space']['uuid'] for d in dashboards if d['space']['uuid']))
    unique_organizations = len(set(d['organization']['uuid'] for d in dashboards if d['organization']['uuid']))
    total_views = sum(d.get('views', 0) for d in dashboards)
    dashboards_with_descriptions = sum(1 for d in dashboards if d.get('has_description'))
    pinned_dashboards = sum(1 for d in dashboards if d.get('is_pinned'))
    
    print(f"\n📈 OVERVIEW:")
    print(f"   Total Dashboards: {total_dashboards:,}")
    print(f"   Unique Organizations: {unique_organizations}")
    print(f"   Unique Projects: {unique_projects}")
    print(f"   Unique Spaces: {unique_spaces}")
    print(f"   Total Views: {total_views:,}")
    print(f"   Dashboards with Descriptions: {dashboards_with_descriptions} ({dashboards_with_descriptions/total_dashboards*100:.1f}%)")
    print(f"   Pinned Dashboards: {pinned_dashboards} ({pinned_dashboards/total_dashboards*100:.1f}%)")
    
    # Top viewed dashboards
    print(f"\n🔥 TOP 10 MOST VIEWED DASHBOARDS:")
    top_viewed = sorted(dashboards, key=lambda x: x.get('views', 0), reverse=True)[:10]
    for i, dashboard in enumerate(top_viewed, 1):
        views = dashboard.get('views', 0)
        name = dashboard.get('name', 'Unnamed')[:40]
        uuid = dashboard.get('uuid', '')[:8]
        space = dashboard.get('space', {}).get('name', 'Unknown')[:20]
        print(f"   {i:2d}. {name:<42} | {uuid} | {views:>6,} views | {space}")
    
    # Projects breakdown
    print(f"\n🏗️  DASHBOARDS BY PROJECT:")
    project_counts = {}
    project_views = {}
    for dashboard in dashboards:
        project_name = dashboard.get('project', {}).get('name', 'Unknown')
        project_counts[project_name] = project_counts.get(project_name, 0) + 1
        project_views[project_name] = project_views.get(project_name, 0) + dashboard.get('views', 0)
    
    sorted_projects = sorted(project_counts.items(), key=lambda x: x[1], reverse=True)
    for project_name, count in sorted_projects[:10]:  # Show top 10 projects
        views = project_views[project_name]
        avg_views = views / count if count > 0 else 0
        print(f"   {project_name:<40} | {count:>3} dashboards | {views:>8,} total views | {avg_views:>6.1f} avg")
    
    if len(sorted_projects) > 10:
        print(f"   ... and {len(sorted_projects) - 10} more projects")
    
    # Spaces breakdown
    print(f"\n🏠 DASHBOARDS BY SPACE:")
    space_counts = {}
    space_views = {}
    for dashboard in dashboards:
        space_name = dashboard.get('space', {}).get('name', 'Unknown')
        space_counts[space_name] = space_counts.get(space_name, 0) + 1
        space_views[space_name] = space_views.get(space_name, 0) + dashboard.get('views', 0)
    
    sorted_spaces = sorted(space_counts.items(), key=lambda x: x[1], reverse=True)
    for space_name, count in sorted_spaces[:10]:  # Show top 10 spaces
        views = space_views[space_name]
        avg_views = views / count if count > 0 else 0
        print(f"   {space_name:<40} | {count:>3} dashboards | {views:>8,} total views | {avg_views:>6.1f} avg")
    
    if len(sorted_spaces) > 10:
        print(f"   ... and {len(sorted_spaces) - 10} more spaces")
    
    # Activity analysis
    print(f"\n🎯 ACTIVITY INSIGHTS:")
    
    # Most active creators
    creator_counts = {}
    for dashboard in dashboards:
        creator_name = (dashboard.get('created_by', {}).get('name') or 'Unknown').strip()
        if creator_name and creator_name != 'Unknown':
            creator_counts[creator_name] = creator_counts.get(creator_name, 0) + 1
    
    if creator_counts:
        print(f"   Top Dashboard Creators:")
        sorted_creators = sorted(creator_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for creator, count in sorted_creators:
            print(f"   - {creator:<30} | {count:>3} dashboards")
    
    # Recently updated dashboards
    print(f"\n🕒 RECENTLY UPDATED DASHBOARDS:")
    recent_dashboards = [d for d in dashboards if d.get('last_updated_at')]
    recent_dashboards.sort(key=lambda x: x.get('last_updated_at', ''), reverse=True)
    
    for dashboard in recent_dashboards[:10]:
        name = dashboard.get('name', 'Unnamed')[:40]
        uuid = dashboard.get('uuid', '')[:8]
        updated_at = dashboard.get('last_updated_at', '')[:10]  # Just the date
        updated_by = (dashboard.get('last_updated_by', {}).get('name') or 'Unknown')[:15]
        views = dashboard.get('views', 0)
        print(f"   - {name:<42} | {uuid} | {updated_at} | by {updated_by:<17} | {views:>4} views")
    
    # Views distribution
    print(f"\n📊 VIEWS DISTRIBUTION:")
    view_ranges = [
        (0, 0, "No views"),
        (1, 10, "1-10 views"),
        (11, 50, "11-50 views"),
        (51, 100, "51-100 views"),
        (101, 500, "101-500 views"),
        (501, 1000, "501-1000 views"),
        (1001, float('inf'), "1000+ views")
    ]
    
    for min_views, max_views, label in view_ranges:
        count = sum(1 for d in dashboards if min_views <= d.get('views', 0) <= max_views)
        percentage = count / total_dashboards * 100 if total_dashboards > 0 else 0
        bar = "█" * int(percentage / 5)  # Simple bar chart
        print(f"   {label:<15} | {count:>4} dashboards ({percentage:>5.1f}%) {bar}")
    
    # Dashboard cleanup recommendations
    print(f"\n🧹 DASHBOARD CLEANUP RECOMMENDATIONS:")
    
    # Dashboards with zero views
    zero_views = [d for d in dashboards if d.get('views', 0) == 0]
    if zero_views:
        print(f"   📱 {len(zero_views)} dashboards have NEVER been viewed:")
        for dashboard in sorted(zero_views, key=lambda x: x.get('created_at', ''))[:10]:
            name = dashboard.get('name', 'Unnamed')[:40]
            uuid = dashboard.get('uuid', '')[:8]
            created_at = dashboard.get('created_at', '')[:10]
            space = dashboard.get('space', {}).get('name', 'Unknown')[:20]
            print(f"   - {name:<42} | {uuid} | Created: {created_at} | {space}")
        if len(zero_views) > 10:
            print(f"   ... and {len(zero_views) - 10} more dashboards with zero views")
    
    # Low-engagement dashboards (1-5 views)
    low_engagement = [d for d in dashboards if 1 <= d.get('views', 0) <= 5]
    if low_engagement:
        print(f"   🔹 {len(low_engagement)} dashboards have very low engagement (1-5 views):")
        for dashboard in sorted(low_engagement, key=lambda x: x.get('views', 0))[:10]:
            name = dashboard.get('name', 'Unnamed')[:40]
            uuid = dashboard.get('uuid', '')[:8]
            views = dashboard.get('views', 0)
            space = dashboard.get('space', {}).get('name', 'Unknown')[:20]
            print(f"   - {name:<42} | {uuid} | {views} views | {space}")
        if len(low_engagement) > 10:
            print(f"   ... and {len(low_engagement) - 10} more low-engagement dashboards")
    
    # Old dashboards without recent updates
    from datetime import datetime, timedelta
    
    # Parse dates and find old dashboards
    cutoff_date = (datetime.now() - timedelta(days=180)).isoformat()  # 6 months ago
    old_dashboards = []
    
    for dashboard in dashboards:
        last_updated = dashboard.get('last_updated_at', '')
        if last_updated and last_updated < cutoff_date:
            old_dashboards.append(dashboard)
    
    if old_dashboards:
        print(f"   📅 {len(old_dashboards)} dashboards haven't been updated in 6+ months:")
        for dashboard in sorted(old_dashboards, key=lambda x: x.get('last_updated_at', ''))[:10]:
            name = dashboard.get('name', 'Unnamed')[:40]
            uuid = dashboard.get('uuid', '')[:8]
            updated_at = dashboard.get('last_updated_at', '')[:10]
            views = dashboard.get('views', 0)
            print(f"   - {name:<42} | {uuid} | Updated: {updated_at} | {views} views")
        if len(old_dashboards) > 10:
            print(f"   ... and {len(old_dashboards) - 10} more stale dashboards")
    
    # Dashboards without descriptions
    no_description = [d for d in dashboards if not d.get('has_description')]
    if no_description:
        print(f"   📝 {len(no_description)} dashboards lack descriptions:")
        for dashboard in sorted(no_description, key=lambda x: x.get('views', 0), reverse=True)[:10]:
            name = dashboard.get('name', 'Unnamed')[:40]
            uuid = dashboard.get('uuid', '')[:8]
            views = dashboard.get('views', 0)
            space = dashboard.get('space', {}).get('name', 'Unknown')[:20]
            print(f"   - {name:<42} | {uuid} | {views} views | {space}")
        if len(no_description) > 10:
            print(f"   ... and {len(no_description) - 10} more dashboards without descriptions")
    
    print(f"\n💡 CLEANUP SUGGESTIONS:")
    if zero_views:
        print(f"   • Consider archiving/deleting {len(zero_views)} dashboards with zero views")
    if low_engagement:
        print(f"   • Review {len(low_engagement)} dashboards with minimal engagement")
    if old_dashboards:
        print(f"   • Audit {len(old_dashboards)} dashboards not updated recently")
    if no_description:
        print(f"   • Add descriptions to {len(no_description)} dashboards for better discovery")
    
    print(f"\n💡 HOW TO USE DASHBOARD UUIDs:")
    print(f"   Dashboard URLs follow this pattern:")
    print(f"   {API_URL}/projects/{PROJECT_UUID}/dashboards/{{DASHBOARD_UUID}}/view")
    print(f"   ")
    print(f"   Example: To view dashboard {dashboards[0].get('uuid', '')[:8]}... visit:")
    print(f"   {API_URL}/projects/{PROJECT_UUID}/dashboards/{dashboards[0].get('uuid', '')}/view")
    
    print(f"\n⚠️  IMPORTANT NOTE:")
    print(f"   This analysis is based on total view counts and creation/modification dates.")
    print(f"   For actual 'last viewed' dates, you'll need to query your database using")
    print(f"   Lightdash query tags. See: https://docs.lightdash.com/references/usage-analytics")

    print("\n" + "="*80)

def main():
    """Main execution function"""
    # Validate API configuration
    if not API_KEY or API_KEY == '<yourkey>':
        print("❌ Error: Please update API_KEY in the script with your actual API token.")
        print("   Get your API key from: https://docs.lightdash.com/guides/cli/how-to-create-a-personal-access-token")
        exit(1)
    
    if not API_URL or '<yourinstance>' in API_URL:
        print("❌ Error: Please update API_URL in the script with your Lightdash instance URL.")
        print("   Example: https://your-org.lightdash.cloud")
        exit(1)
    
    if not PROJECT_UUID or PROJECT_UUID == '<your-project-uuid>':
        print("❌ Error: Please update PROJECT_UUID in the script with your project UUID.")
        print("   You can find your project UUID in the URL when viewing a project:")
        print("   https://your-org.lightdash.cloud/projects/{PROJECT_UUID}/...")
        print("   Or use the API to list projects: GET /api/v1/projects")
        exit(1)
    
    try:
        print("🚀 Starting dashboard fetch...")
        print(f"📁 Targeting project: {PROJECT_UUID}")
        
        # Use the required project UUID
        project_uuids = [PROJECT_UUID]
        
        # Fetch all dashboards for the specified project
        raw_dashboards = fetch_all_dashboards(project_uuids)
        
        if not raw_dashboards:
            print("⚠️  No dashboards found.")
            exit(0)
        
        print(f"✅ Fetched {len(raw_dashboards)} dashboards")
        
        # Parse dashboard data
        parsed_dashboards = parse_dashboards(raw_dashboards)
        
        # Export to file
        filename = export_dashboards(parsed_dashboards, EXPORT_METHOD)
        
        # Enhanced console output with detailed analysis
        print_dashboard_summary(parsed_dashboards)
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response:
            print(f"Response: {e.response.text}")
        raise
    except Exception as e:
        print(f"❌ Script failed: {e}")
        raise

if __name__ == "__main__":
    main()