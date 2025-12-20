"""
Admin Dashboard for AI Chatbot System

A comprehensive Gradio-based dashboard for managing the chatbot system.
Includes counsellor management, ticket monitoring, system stats, and configuration.
"""

import gradio as gr
import database.db as db
import counsellors
import ticket
import pandas as pd
from datetime import datetime, timedelta
import logging
from counsellor_handler import create_counsellor
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_stats():
    """Get current system statistics."""
    try:
        # Update stats first
        db.update_system_stats()
        
        # Get all stats
        stats = db.get_all_system_configs(category='stats')
        config = db.get_all_system_configs(category='config')
        health = db.get_all_system_configs(category='health')
        
        # Build stats dictionary
        stats_dict = {
            'Total Users': stats['stats']['total_users']['value'] if stats else 0,
            'Total Messages': stats['stats']['total_messages']['value'] if stats else 0,
            'Active Tickets': stats['stats']['active_tickets']['value'] if stats else 0,
            'Total Counsellors': len(db.get_counsellors()),
            'DB Version': health['health']['db_version']['value'] if health else 0,
            'Maintenance Mode': 'ON' if config['config']['maintenance_mode']['value'] else 'OFF',
            'AI Model': config['config']['ai_model_version']['value'] if config else 'N/A'
        }
        
        return stats_dict
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {}


def format_stats_for_display(stats_dict):
    """Format stats dictionary for Gradio display."""
    df = pd.DataFrame([
        {'Metric': k, 'Value': v} 
        for k, v in stats_dict.items()
    ])
    return df


def get_counsellors_data():
    """Get all counsellors as DataFrame."""
    try:
        counsellors_list = db.get_counsellors_details()
        
        if not counsellors_list:
            return pd.DataFrame(columns=['ID', 'Username', 'Name', 'Email', 'Phone', 'Current Ticket'])
        
        data = []
        for c in counsellors_list:
            data.append({
                'ID': c[0],
                'Username': c[2],
                'Name': c[1] if c[1] else 'N/A',
                'Email': c[4] if c[4] else 'N/A',
                'Phone': c[5] if c[5] else 'N/A',
                'Current Ticket': c[7] if c[7] else 'None'
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting counsellors data: {e}")
        return pd.DataFrame(columns=['ID', 'Username', 'Name', 'Email', 'Phone', 'Current Ticket'])


def get_tickets_data():
    """Get all tickets as DataFrame."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, status, handler, user, created_at, closed_at 
            FROM tickets 
            ORDER BY created_at DESC 
            LIMIT 100
        """)
        tickets = cur.fetchall()
        db.close_db(conn)
        
        if not tickets:
            return pd.DataFrame(columns=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'])
        
        data = []
        for t in tickets:
            data.append({
                'Ticket ID': t[0],
                'Status': t[1],
                'Handler': t[2] if t[2] else 'Unassigned',
                'User': t[3],
                'Created': t[4],
                'Closed': t[5] if t[5] else 'Open'
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting tickets data: {e}")
        return pd.DataFrame(columns=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'])


def get_recent_messages(limit=50):
    """Get recent messages as DataFrame."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT _from, _to, _type, content, timestamp 
            FROM messages 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        messages = cur.fetchall()
        db.close_db(conn)
        
        if not messages:
            return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])
        
        data = []
        for m in messages:
            data.append({
                'From': m[0],
                'To': m[1],
                'Type': m[2],
                'Content': m[3][:100] + '...' if len(m[3]) > 100 else m[3],
                'Timestamp': m[4]
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

def refresh_overview():
    """Refresh overview statistics."""
    stats = get_system_stats()
    stats_df = format_stats_for_display(stats)
    
    # Get recent activity
    recent_tickets = get_tickets_data().head(5)
    recent_messages = get_recent_messages(5)
    
    return stats_df, recent_tickets, recent_messages


def build_overview_tab():
    """Build the Overview tab."""
    # Get initial data
    stats_df, tickets_df, messages_df = refresh_overview()
    
    with gr.Tab("📊 Overview"):
        gr.Markdown("## System Dashboard")
        
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Stats", variant="primary")
        
        with gr.Row():
            stats_display = gr.Dataframe(
                value=stats_df,
                headers=['Metric', 'Value'],
                label="System Statistics",
                interactive=False
            )
        
        gr.Markdown("### Recent Activity")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Recent Tickets")
                recent_tickets = gr.Dataframe(
                    value=tickets_df,
                    headers=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'],
                    label="Latest Tickets",
                    interactive=False
                )
            
            with gr.Column():
                gr.Markdown("#### Recent Messages")
                recent_messages = gr.Dataframe(
                    value=messages_df,
                    headers=['From', 'To', 'Type', 'Content', 'Timestamp'],
                    label="Latest Messages",
                    interactive=False
                )
        
        # Set up refresh button
        refresh_btn.click(
            fn=refresh_overview,
            outputs=[stats_display, recent_tickets, recent_messages]
        )


# =============================================================================
# TAB 2: COUNSELLORS
# =============================================================================

def refresh_counsellors():
    """Refresh counsellors list."""
    return get_counsellors_data()


def create_counsellor_from_form(username, name, email, password, phone, whatsapp):
    """Create a new counsellor from form inputs."""
    try:
        if not username or not email:
            return "❌ Error: Username and email are required", refresh_counsellors()
        
        # Call create_counsellor function
        create_counsellor(
            username=username,
            password=password if password else "changeme123",
            email=email,
            name=name if name else username,
            whatsapp_number=whatsapp if whatsapp else None
        )
        
        return f"✅ Counsellor '{username}' created successfully!", refresh_counsellors()
    
    except Exception as e:
        logger.error(f"Error creating counsellor: {e}")
        return f"❌ Error: {str(e)}", refresh_counsellors()


def delete_counsellor_action(username):
    """Delete a counsellor."""
    try:
        if not username:
            return "❌ Error: Please enter a username", refresh_counsellors()
        
        if counsellors.remove_counsellor(username):
            return f"✅ Counsellor '{username}' deleted successfully!", refresh_counsellors()
        else:
            return f"❌ Error: Failed to delete counsellor '{username}'", refresh_counsellors()
    
    except Exception as e:
        logger.error(f"Error deleting counsellor: {e}")
        return f"❌ Error: {str(e)}", refresh_counsellors()


def build_counsellors_tab():
    """Build the Counsellors tab."""
    # Get initial data
    initial_counsellors = refresh_counsellors()
    
    with gr.Tab("👥 Counsellors"):
        gr.Markdown("## Counsellor Management")
        
        with gr.Row():
            refresh_counsellors_btn = gr.Button("🔄 Refresh List", variant="secondary")
        
        counsellors_list = gr.Dataframe(
            value=initial_counsellors,
            headers=['ID', 'Username', 'Name', 'Email', 'Phone', 'Current Ticket'],
            label="All Counsellors",
            interactive=False
        )
        
        gr.Markdown("### Create New Counsellor")
        
        with gr.Row():
            with gr.Column():
                new_username = gr.Textbox(label="Username*", placeholder="alice")
                new_name = gr.Textbox(label="Full Name", placeholder="Alice Smith")
                new_email = gr.Textbox(label="Email*", placeholder="alice@example.com")
            
            with gr.Column():
                new_password = gr.Textbox(label="Password", placeholder="Leave empty for default", type="password")
                new_phone = gr.Textbox(label="Phone", placeholder="237612345678")
                new_whatsapp = gr.Textbox(label="WhatsApp Number", placeholder="237612345678")
        
        create_btn = gr.Button("➕ Create Counsellor", variant="primary")
        create_result = gr.Textbox(label="Result", interactive=False)
        
        gr.Markdown("### Delete Counsellor")
        
        with gr.Row():
            delete_username = gr.Textbox(label="Username to Delete", placeholder="username")
            delete_btn = gr.Button("🗑️ Delete", variant="stop")
        
        delete_result = gr.Textbox(label="Result", interactive=False)
        
        # Set up button actions
        refresh_counsellors_btn.click(
            fn=refresh_counsellors,
            outputs=counsellors_list
        )
        
        create_btn.click(
            fn=create_counsellor_from_form,
            inputs=[new_username, new_name, new_email, new_password, new_phone, new_whatsapp],
            outputs=[create_result, counsellors_list]
        )
        
        delete_btn.click(
            fn=delete_counsellor_action,
            inputs=delete_username,
            outputs=[delete_result, counsellors_list]
        )


# =============================================================================
# TAB 3: TICKETS
# =============================================================================

def refresh_tickets():
    """Refresh tickets list."""
    return get_tickets_data()


def get_ticket_details(ticket_id):
    """Get detailed information about a ticket."""
    try:
        if not ticket_id:
            return "Please enter a ticket ID"
        
        ticket_data = ticket.get_ticket(ticket_id)
        
        if not ticket_data:
            return f"Ticket '{ticket_id}' not found"
        
        # Format ticket details
        details = f"""
**Ticket ID:** {ticket_data.get('id', 'N/A')}
**Status:** {ticket_data.get('status', 'N/A')}
**Handler:** {ticket_data.get('handler', 'Unassigned')}
**User:** {ticket_data.get('user', 'N/A')}
**Created:** {ticket_data.get('created_at', 'N/A')}
**Closed:** {ticket_data.get('closed_at', 'Open')}

**Transcript:**
{ticket_data.get('transcript', 'No transcript available')}
"""
        return details
    
    except Exception as e:
        logger.error(f"Error getting ticket details: {e}")
        return f"Error: {str(e)}"


def build_tickets_tab():
    """Build the Tickets tab."""
    # Get initial data
    initial_tickets = refresh_tickets()
    
    with gr.Tab("🎫 Tickets"):
        gr.Markdown("## Ticket Management")
        
        with gr.Row():
            refresh_tickets_btn = gr.Button("🔄 Refresh Tickets", variant="secondary")
        
        tickets_list = gr.Dataframe(
            value=initial_tickets,
            headers=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'],
            label="All Tickets",
            interactive=False
        )
        
        gr.Markdown("### View Ticket Details")
        
        with gr.Row():
            ticket_id_input = gr.Textbox(label="Ticket ID", placeholder="Enter ticket ID")
            view_ticket_btn = gr.Button("🔍 View Details", variant="primary")
        
        ticket_details = gr.Markdown(label="Ticket Details")
        
        # Set up button actions
        refresh_tickets_btn.click(
            fn=refresh_tickets,
            outputs=tickets_list
        )
        
        view_ticket_btn.click(
            fn=get_ticket_details,
            inputs=ticket_id_input,
            outputs=ticket_details
        )


# =============================================================================
# TAB 4: MESSAGES
# =============================================================================

def search_messages(search_term, limit=50):
    """Search messages by content or user."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        
        if search_term:
            cur.execute("""
                SELECT _from, _to, _type, content, timestamp 
                FROM messages 
                WHERE _from LIKE ? OR _to LIKE ? OR content LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit))
        else:
            cur.execute("""
                SELECT _from, _to, _type, content, timestamp 
                FROM messages 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        messages = cur.fetchall()
        db.close_db(conn)
        
        if not messages:
            return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])
        
        data = []
        for m in messages:
            data.append({
                'From': m[0],
                'To': m[1],
                'Type': m[2],
                'Content': m[3],
                'Timestamp': m[4]
            })
        
        return pd.DataFrame(data)
    
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])


def build_messages_tab():
    """Build the Messages tab."""
    # Get initial data
    initial_messages = get_recent_messages(50)
    
    with gr.Tab("💬 Messages"):
        gr.Markdown("## Message Log")
        
        with gr.Row():
            search_input = gr.Textbox(label="Search", placeholder="Search by user or content")
            search_btn = gr.Button("🔍 Search", variant="primary")
            refresh_messages_btn = gr.Button("🔄 Refresh", variant="secondary")
        
        messages_list = gr.Dataframe(
            value=initial_messages,
            headers=['From', 'To', 'Type', 'Content', 'Timestamp'],
            label="Messages",
            interactive=False
        )
        
        # Set up button actions
        search_btn.click(
            fn=search_messages,
            inputs=search_input,
            outputs=messages_list
        )
        
        refresh_messages_btn.click(
            fn=lambda: get_recent_messages(50),
            outputs=messages_list
        )


# =============================================================================
# TAB 5: SETTINGS
# =============================================================================

def get_system_configs():
    """Get all system configurations."""
    try:
        all_configs = db.get_all_system_configs()
        
        data = []
        for category, configs in all_configs.items():
            for key, info in configs.items():
                data.append({
                    'Category': category,
                    'Key': key,
                    'Value': str(info['value']),
                    'Type': info['data_type'],
                    'Description': info['description'],
                    'Editable': 'Yes' if info['is_editable'] else 'No'
                })
        
        return pd.DataFrame(data)
    
    except Exception as e:
        logger.error(f"Error getting system configs: {e}")
        return pd.DataFrame(columns=['Category', 'Key', 'Value', 'Type', 'Description', 'Editable'])


def update_config(key, value, category='config'):
    """Update a system configuration."""
    try:
        if not key or not value:
            return "❌ Error: Key and value are required", get_system_configs()
        
        if db.set_system_config(key, value, category):
            return f"✅ Configuration '{key}' updated successfully!", get_system_configs()
        else:
            return f"❌ Error: Failed to update '{key}'. It may not be editable.", get_system_configs()
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return f"❌ Error: {str(e)}", get_system_configs()


def build_settings_tab():
    """Build the Settings tab."""
    # Get initial data
    initial_configs = get_system_configs()
    
    with gr.Tab("⚙️ Settings"):
        gr.Markdown("## System Configuration")
        
        with gr.Row():
            refresh_configs_btn = gr.Button("🔄 Refresh Configs", variant="secondary")
        
        configs_list = gr.Dataframe(
            value=initial_configs,
            headers=['Category', 'Key', 'Value', 'Type', 'Description', 'Editable'],
            label="System Configurations",
            interactive=False
        )
        
        gr.Markdown("### Update Configuration")
        gr.Markdown("*Only editable configurations can be updated*")
        
        with gr.Row():
            config_category = gr.Dropdown(
                choices=['config', 'stats', 'health'],
                value='config',
                label="Category"
            )
            config_key = gr.Textbox(label="Config Key", placeholder="maintenance_mode")
        
        config_value = gr.Textbox(label="New Value", placeholder="true")
        update_btn = gr.Button("💾 Update Config", variant="primary")
        update_result = gr.Textbox(label="Result", interactive=False)
        
        # Set up button actions
        refresh_configs_btn.click(
            fn=get_system_configs,
            outputs=configs_list
        )
        
        update_btn.click(
            fn=update_config,
            inputs=[config_key, config_value, config_category],
            outputs=[update_result, configs_list]
        )


# =============================================================================
# MAIN DASHBOARD
# =============================================================================

def build_dashboard():
    """Build the complete dashboard."""
    with gr.Blocks(title="AI Chatbot Admin Dashboard", theme=gr.themes.Soft()) as dashboard:
        
        gr.Markdown("""
        #AI Chatbot Admin Dashboard
        ### Manage counsellors, monitor tickets, and configure system settings
        """)
        
        # Build all tabs
        build_overview_tab()
        build_counsellors_tab()
        build_tickets_tab()
        build_messages_tab()
        build_settings_tab()
        
        gr.Markdown("""
        ---
        **Dashboard Version:** 1.0 | **Database:** SQLite | **Framework:** Gradio
        """)
    
    return dashboard


if __name__ == "__main__":
    # Build and launch dashboard
    dashboard = build_dashboard()
    
    # Launch on a different port than Flask (which uses PORT from .env)
    dashboard_port = int(os.getenv('DASHBOARD_PORT', 7860))
    
    print(f"\n{'='*70}")
    print(f"🚀 Launching Admin Dashboard on http://localhost:{dashboard_port}")
    print(f"{'='*70}\n")
    
    dashboard.launch(
        server_port=dashboard_port,
        server_name="0.0.0.0",
        share=False,
        show_error=True
    )
