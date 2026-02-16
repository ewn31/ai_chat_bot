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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM CSS
# =============================================================================

DASHBOARD_CSS = """
/* Global Styles */
.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Header */
.dashboard-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    padding: 28px 36px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
.dashboard-header h1 {
    margin: 0 0 6px 0;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.dashboard-header p {
    margin: 0;
    opacity: 0.8;
    font-size: 14px;
    font-weight: 400;
}

/* Stat Cards */
.stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.stat-card .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #1a1a2e;
    line-height: 1.2;
}
.stat-card .stat-label {
    font-size: 13px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
    font-weight: 500;
}
.stat-card.primary { border-top: 3px solid #3b82f6; }
.stat-card.success { border-top: 3px solid #10b981; }
.stat-card.warning { border-top: 3px solid #f59e0b; }
.stat-card.info    { border-top: 3px solid #8b5cf6; }

/* Section Headers */
.section-header {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    padding-bottom: 10px;
    border-bottom: 2px solid #e5e7eb;
    margin: 20px 0 14px 0;
}

/* Status Badges */
.status-active  { color: #059669; font-weight: 600; }
.status-closed  { color: #6b7280; font-weight: 600; }
.status-pending { color: #d97706; font-weight: 600; }

/* Improved Buttons */
.action-btn {
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
    transition: all 0.15s ease !important;
}

/* Form Sections */
.form-section {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 24px;
    margin-top: 16px;
}

/* Table Styling */
.dataframe-container {
    border-radius: 8px !important;
    overflow: hidden !important;
    border: 1px solid #e5e7eb !important;
}

/* Tab Styling */
.tab-nav button {
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
}
.tab-nav button.selected {
    font-weight: 600 !important;
}

/* Alert / Result Boxes */
.result-box {
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-top: 8px;
}

/* Footer */
.dashboard-footer {
    text-align: center;
    padding: 16px 0;
    margin-top: 24px;
    border-top: 1px solid #e5e7eb;
    color: #9ca3af;
    font-size: 12px;
}

/* Danger Zone */
.danger-zone {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 16px;
}
.danger-zone h4 {
    color: #991b1b;
    margin: 0 0 12px 0;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #9ca3af;
    font-size: 14px;
}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_system_stats():
    """Get current system statistics."""
    try:
        db.update_system_stats()

        stats = db.get_all_system_configs(category='stats')
        config = db.get_all_system_configs(category='config')
        health = db.get_all_system_configs(category='health')

        stats_dict = {
            'total_users': stats['stats']['total_users']['value'] if stats else 0,
            'total_messages': stats['stats']['total_messages']['value'] if stats else 0,
            'active_tickets': stats['stats']['active_tickets']['value'] if stats else 0,
            'total_counsellors': len(db.get_counsellors()),
            'db_version': health['health']['db_version']['value'] if health else 0,
            'maintenance_mode': config['config']['maintenance_mode']['value'] if config else False,
            'ai_model': config['config']['ai_model_version']['value'] if config else 'N/A'
        }

        return stats_dict
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {
            'total_users': 0, 'total_messages': 0, 'active_tickets': 0,
            'total_counsellors': 0, 'db_version': 0,
            'maintenance_mode': False, 'ai_model': 'N/A'
        }


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
                'Name': c[1] if c[1] else '-',
                'Email': c[4] if c[4] else '-',
                'Phone': c[5] if c[5] else '-',
                'Current Ticket': c[7] if c[7] else 'Available'
            })

        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting counsellors data: {e}")
        return pd.DataFrame(columns=['ID', 'Username', 'Name', 'Email', 'Phone', 'Current Ticket'])


def get_tickets_data(status_filter='all'):
    """Get tickets as DataFrame with optional status filter."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()

        if status_filter and status_filter != 'all':
            cur.execute("""
                SELECT id, status, handler, user, created_at, closed_at
                FROM tickets
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT 100
            """, (status_filter,))
        else:
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
                'Status': t[1].capitalize() if t[1] else 'Unknown',
                'Handler': t[2] if t[2] else 'Unassigned',
                'User': t[3],
                'Created': t[4],
                'Closed': t[5] if t[5] else '-'
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
            content = m[3] if m[3] else ''
            data.append({
                'From': m[0],
                'To': m[1],
                'Type': m[2],
                'Content': content[:120] + '...' if len(content) > 120 else content,
                'Timestamp': m[4]
            })

        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])


def get_users_data(limit=50):
    """Get users as DataFrame."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT phone_number, language, handler, onboarding_level, age, name
            FROM users
            ORDER BY rowid DESC
            LIMIT ?
        """, (limit,))
        users = cur.fetchall()
        db.close_db(conn)

        if not users:
            return pd.DataFrame(columns=['Phone', 'Language', 'Handler', 'Onboarding', 'Age', 'Name'])

        data = []
        for u in users:
            data.append({
                'Phone': u[0],
                'Language': (u[1] or '-').upper(),
                'Handler': u[2] if u[2] else '-',
                'Onboarding': u[3] if u[3] else '-',
                'Age': u[4] if u[4] else '-',
                'Name': u[5] if u[5] else '-',
            })

        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting users data: {e}")
        return pd.DataFrame(columns=['Phone', 'Language', 'Handler', 'Onboarding', 'Age', 'Name'])


# =============================================================================
# CHART HELPERS
# =============================================================================

CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899']

def _style_chart(fig, ax):
    """Apply consistent styling to a matplotlib chart."""
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fafafa')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.tick_params(colors='#6b7280', labelsize=9)
    ax.title.set_fontsize(13)
    ax.title.set_fontweight('600')
    ax.title.set_color('#1f2937')
    fig.tight_layout(pad=2.0)


def chart_messages_over_time():
    """Line chart of daily message volume over the last 30 days."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT DATE(timestamp) as day, COUNT(*) as count
            FROM messages
            WHERE timestamp >= DATE('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY day
        """)
        rows = cur.fetchall()
        db.close_db(conn)

        fig, ax = plt.subplots(figsize=(7, 3.2))

        if rows:
            days = [datetime.strptime(r[0], '%Y-%m-%d') for r in rows]
            counts = [r[1] for r in rows]
            ax.fill_between(days, counts, alpha=0.15, color=CHART_COLORS[0])
            ax.plot(days, counts, color=CHART_COLORS[0], linewidth=2, marker='o', markersize=4)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
            fig.autofmt_xdate(rotation=30)
        else:
            ax.text(0.5, 0.5, 'No message data yet', ha='center', va='center',
                    transform=ax.transAxes, color='#9ca3af', fontsize=12)

        ax.set_title('Messages (Last 30 Days)')
        ax.set_ylabel('Messages', fontsize=10, color='#6b7280')
        _style_chart(fig, ax)
        return fig
    except Exception as e:
        logger.error(f"Error creating messages chart: {e}")
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.text(0.5, 0.5, 'Chart unavailable', ha='center', va='center',
                transform=ax.transAxes, color='#9ca3af')
        ax.set_axis_off()
        return fig


def chart_ticket_status():
    """Donut chart of ticket status distribution."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
        rows = cur.fetchall()
        db.close_db(conn)

        fig, ax = plt.subplots(figsize=(4, 3.2))

        if rows:
            labels = [r[0].capitalize() if r[0] else 'Unknown' for r in rows]
            sizes = [r[1] for r in rows]
            colors = CHART_COLORS[:len(labels)]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.0f%%', colors=colors,
                startangle=90, pctdistance=0.75, textprops={'fontsize': 10}
            )
            for t in autotexts:
                t.set_fontsize(9)
                t.set_color('#374151')
            # Donut hole
            centre = plt.Circle((0, 0), 0.50, fc='white')
            ax.add_artist(centre)
        else:
            ax.text(0.5, 0.5, 'No tickets yet', ha='center', va='center',
                    transform=ax.transAxes, color='#9ca3af', fontsize=12)
            ax.set_axis_off()

        ax.set_title('Ticket Status', fontsize=13, fontweight='600', color='#1f2937')
        fig.patch.set_facecolor('#ffffff')
        fig.tight_layout(pad=2.0)
        return fig
    except Exception as e:
        logger.error(f"Error creating ticket chart: {e}")
        fig, ax = plt.subplots(figsize=(4, 3.2))
        ax.text(0.5, 0.5, 'Chart unavailable', ha='center', va='center',
                transform=ax.transAxes, color='#9ca3af')
        ax.set_axis_off()
        return fig


def chart_user_languages():
    """Horizontal bar chart of user language distribution."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT UPPER(COALESCE(language, 'UNKNOWN')) as lang, COUNT(*) as count
            FROM users
            GROUP BY lang
            ORDER BY count DESC
        """)
        rows = cur.fetchall()
        db.close_db(conn)

        fig, ax = plt.subplots(figsize=(4, 3.2))

        if rows:
            labels = [r[0] for r in rows]
            counts = [r[1] for r in rows]
            colors = CHART_COLORS[:len(labels)]
            bars = ax.barh(labels, counts, color=colors, height=0.5, edgecolor='none')
            ax.invert_yaxis()
            for bar, count in zip(bars, counts):
                ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                        str(count), va='center', fontsize=9, color='#374151', fontweight='500')
        else:
            ax.text(0.5, 0.5, 'No user data yet', ha='center', va='center',
                    transform=ax.transAxes, color='#9ca3af', fontsize=12)

        ax.set_title('Users by Language')
        _style_chart(fig, ax)
        return fig
    except Exception as e:
        logger.error(f"Error creating language chart: {e}")
        fig, ax = plt.subplots(figsize=(4, 3.2))
        ax.text(0.5, 0.5, 'Chart unavailable', ha='center', va='center',
                transform=ax.transAxes, color='#9ca3af')
        ax.set_axis_off()
        return fig


def chart_user_demographics():
    """Bar chart of user age range distribution."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(age_range, 'Unknown') as age_group, COUNT(*) as count
            FROM users
            GROUP BY age_group
            ORDER BY age_group
        """)
        rows = cur.fetchall()
        db.close_db(conn)

        fig, ax = plt.subplots(figsize=(7, 3.2))

        if rows:
            labels = [r[0] for r in rows]
            counts = [r[1] for r in rows]
            bars = ax.bar(labels, counts, color=CHART_COLORS[3], width=0.5, edgecolor='none')
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        str(count), ha='center', fontsize=9, color='#374151', fontweight='500')
        else:
            ax.text(0.5, 0.5, 'No user data yet', ha='center', va='center',
                    transform=ax.transAxes, color='#9ca3af', fontsize=12)

        ax.set_title('Users by Age Range')
        ax.set_ylabel('Users', fontsize=10, color='#6b7280')
        _style_chart(fig, ax)
        return fig
    except Exception as e:
        logger.error(f"Error creating demographics chart: {e}")
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.text(0.5, 0.5, 'Chart unavailable', ha='center', va='center',
                transform=ax.transAxes, color='#9ca3af')
        ax.set_axis_off()
        return fig


# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

def refresh_overview():
    """Refresh overview statistics and return individual stat values."""
    stats = get_system_stats()
    recent_tickets = get_tickets_data().head(5)
    recent_messages = get_recent_messages(5)

    return (
        str(stats.get('total_users', 0)),
        str(stats.get('total_messages', 0)),
        str(stats.get('active_tickets', 0)),
        str(stats.get('total_counsellors', 0)),
        "ON" if stats.get('maintenance_mode') else "OFF",
        str(stats.get('ai_model', 'N/A')),
        recent_tickets,
        recent_messages
    )


def build_overview_tab():
    """Build the Overview tab with stat cards."""
    stats = get_system_stats()
    tickets_df = get_tickets_data().head(5)
    messages_df = get_recent_messages(5)

    with gr.Tab("Overview"):
        gr.Markdown('<div class="section-header">System Overview</div>')

        # Stat Cards Row
        with gr.Row(equal_height=True):
            with gr.Column(scale=1, min_width=160):
                gr.HTML(f"""<div class="stat-card primary">
                    <div class="stat-value" id="stat-users">{stats.get('total_users', 0)}</div>
                    <div class="stat-label">Total Users</div>
                </div>""")
                stat_users = gr.Textbox(visible=False, value=str(stats.get('total_users', 0)))

            with gr.Column(scale=1, min_width=160):
                gr.HTML(f"""<div class="stat-card success">
                    <div class="stat-value" id="stat-messages">{stats.get('total_messages', 0)}</div>
                    <div class="stat-label">Total Messages</div>
                </div>""")
                stat_messages = gr.Textbox(visible=False, value=str(stats.get('total_messages', 0)))

            with gr.Column(scale=1, min_width=160):
                gr.HTML(f"""<div class="stat-card warning">
                    <div class="stat-value" id="stat-tickets">{stats.get('active_tickets', 0)}</div>
                    <div class="stat-label">Active Tickets</div>
                </div>""")
                stat_tickets = gr.Textbox(visible=False, value=str(stats.get('active_tickets', 0)))

            with gr.Column(scale=1, min_width=160):
                gr.HTML(f"""<div class="stat-card info">
                    <div class="stat-value" id="stat-counsellors">{stats.get('total_counsellors', 0)}</div>
                    <div class="stat-label">Counsellors</div>
                </div>""")
                stat_counsellors = gr.Textbox(visible=False, value=str(stats.get('total_counsellors', 0)))

        # System Info Row
        with gr.Row(equal_height=True):
            with gr.Column(scale=1, min_width=160):
                maintenance_status = "ON" if stats.get('maintenance_mode') else "OFF"
                gr.HTML(f"""<div class="stat-card">
                    <div class="stat-value" style="font-size: 22px;">{maintenance_status}</div>
                    <div class="stat-label">Maintenance Mode</div>
                </div>""")
                stat_maintenance = gr.Textbox(visible=False, value=maintenance_status)

            with gr.Column(scale=1, min_width=160):
                model_name = str(stats.get('ai_model', 'N/A'))
                display_model = model_name.split('/')[-1][:25] if '/' in model_name else model_name[:25]
                gr.HTML(f"""<div class="stat-card">
                    <div class="stat-value" style="font-size: 16px;">{display_model}</div>
                    <div class="stat-label">AI Model</div>
                </div>""")
                stat_model = gr.Textbox(visible=False, value=model_name)

        with gr.Row():
            refresh_btn = gr.Button("Refresh Stats", variant="primary", size="sm")

        # Recent Activity
        gr.Markdown('<div class="section-header">Recent Activity</div>')

        with gr.Row():
            with gr.Column():
                gr.Markdown("**Latest Tickets**")
                recent_tickets = gr.Dataframe(
                    value=tickets_df,
                    headers=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'],
                    interactive=False,
                    wrap=True,
                    max_height=250
                )

            with gr.Column():
                gr.Markdown("**Latest Messages**")
                recent_messages = gr.Dataframe(
                    value=messages_df,
                    headers=['From', 'To', 'Type', 'Content', 'Timestamp'],
                    interactive=False,
                    wrap=True,
                    max_height=250
                )

        # Refresh handler
        refresh_btn.click(
            fn=refresh_overview,
            outputs=[
                stat_users, stat_messages, stat_tickets, stat_counsellors,
                stat_maintenance, stat_model,
                recent_tickets, recent_messages
            ]
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
            return "Error: Username and email are required fields.", refresh_counsellors()

        create_counsellor(
            username=username,
            password=password if password else "changeme123",
            email=email,
            name=name if name else username,
            whatsapp_number=whatsapp if whatsapp else None
        )

        return f"Counsellor '{username}' created successfully.", refresh_counsellors()

    except Exception as e:
        logger.error(f"Error creating counsellor: {e}")
        return f"Error: {str(e)}", refresh_counsellors()


def delete_counsellor_action(username):
    """Delete a counsellor."""
    try:
        if not username:
            return "Error: Please enter a username.", refresh_counsellors()

        if counsellors.remove_counsellor(username):
            return f"Counsellor '{username}' deleted.", refresh_counsellors()
        else:
            return f"Error: Failed to delete '{username}'.", refresh_counsellors()

    except Exception as e:
        logger.error(f"Error deleting counsellor: {e}")
        return f"Error: {str(e)}", refresh_counsellors()


def build_counsellors_tab():
    """Build the Counsellors tab."""
    initial_counsellors = refresh_counsellors()

    with gr.Tab("Counsellors"):
        gr.Markdown('<div class="section-header">Counsellor Management</div>')

        with gr.Row():
            refresh_counsellors_btn = gr.Button("Refresh List", variant="secondary", size="sm")

        counsellors_list = gr.Dataframe(
            value=initial_counsellors,
            headers=['ID', 'Username', 'Name', 'Email', 'Phone', 'Current Ticket'],
            interactive=False,
            wrap=True,
            max_height=350
        )

        # Create Counsellor Form
        gr.Markdown('<div class="section-header">Add New Counsellor</div>')

        with gr.Group():
            with gr.Row():
                with gr.Column():
                    new_username = gr.Textbox(
                        label="Username",
                        placeholder="e.g. alice",
                        info="Required. Must be unique."
                    )
                    new_name = gr.Textbox(
                        label="Full Name",
                        placeholder="e.g. Alice Smith"
                    )
                    new_email = gr.Textbox(
                        label="Email",
                        placeholder="e.g. alice@example.com",
                        info="Required."
                    )

                with gr.Column():
                    new_password = gr.Textbox(
                        label="Password",
                        placeholder="Leave empty for default",
                        type="password",
                        info="Default: changeme123"
                    )
                    new_phone = gr.Textbox(
                        label="Phone",
                        placeholder="e.g. 237612345678"
                    )
                    new_whatsapp = gr.Textbox(
                        label="WhatsApp Number",
                        placeholder="e.g. 237612345678"
                    )

            create_btn = gr.Button("Create Counsellor", variant="primary")
            create_result = gr.Textbox(label="Result", interactive=False, show_label=False)

        # Delete Counsellor
        gr.Markdown('<div class="section-header" style="color: #991b1b;">Remove Counsellor</div>')

        with gr.Group():
            gr.Markdown("*This action is irreversible. The counsellor will be permanently removed.*")
            with gr.Row():
                delete_username = gr.Textbox(
                    label="Username to Remove",
                    placeholder="Enter username",
                    scale=3
                )
                delete_btn = gr.Button("Delete", variant="stop", scale=1)

            delete_result = gr.Textbox(label="Result", interactive=False, show_label=False)

        # Button actions
        refresh_counsellors_btn.click(fn=refresh_counsellors, outputs=counsellors_list)

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

def refresh_tickets(status_filter='all'):
    """Refresh tickets list with optional filter."""
    return get_tickets_data(status_filter)


def get_ticket_details(ticket_id):
    """Get detailed information about a ticket."""
    try:
        if not ticket_id:
            return "Enter a ticket ID to view details."

        ticket_data = ticket.get_ticket(ticket_id)

        if not ticket_data:
            return f"Ticket '{ticket_id}' not found."

        status = ticket_data.get('status', 'N/A')
        transcript = ticket_data.get('transcript', 'No transcript available')

        details = f"""### Ticket: {ticket_data.get('id', 'N/A')}

| Field | Value |
|-------|-------|
| **Status** | {status} |
| **Handler** | {ticket_data.get('handler', 'Unassigned')} |
| **User** | {ticket_data.get('user', 'N/A')} |
| **Created** | {ticket_data.get('created_at', 'N/A')} |
| **Closed** | {ticket_data.get('closed_at', 'Still open')} |

---

**Transcript:**

{transcript}
"""
        return details

    except Exception as e:
        logger.error(f"Error getting ticket details: {e}")
        return f"Error: {str(e)}"


def build_tickets_tab():
    """Build the Tickets tab."""
    initial_tickets = refresh_tickets()

    with gr.Tab("Tickets"):
        gr.Markdown('<div class="section-header">Ticket Management</div>')

        with gr.Row():
            status_filter = gr.Dropdown(
                choices=['all', 'open', 'closed', 'escalated'],
                value='all',
                label="Filter by Status",
                scale=2
            )
            refresh_tickets_btn = gr.Button("Refresh", variant="secondary", size="sm", scale=1)

        tickets_list = gr.Dataframe(
            value=initial_tickets,
            headers=['Ticket ID', 'Status', 'Handler', 'User', 'Created', 'Closed'],
            interactive=False,
            wrap=True,
            max_height=400
        )

        gr.Markdown('<div class="section-header">Ticket Details</div>')

        with gr.Row():
            ticket_id_input = gr.Textbox(
                label="Ticket ID",
                placeholder="Enter ticket ID to view details",
                scale=3
            )
            view_ticket_btn = gr.Button("View Details", variant="primary", scale=1)

        ticket_details = gr.Markdown("*Select a ticket to view its details.*")

        # Button actions
        refresh_tickets_btn.click(
            fn=refresh_tickets,
            inputs=status_filter,
            outputs=tickets_list
        )

        status_filter.change(
            fn=refresh_tickets,
            inputs=status_filter,
            outputs=tickets_list
        )

        view_ticket_btn.click(
            fn=get_ticket_details,
            inputs=ticket_id_input,
            outputs=ticket_details
        )


# =============================================================================
# TAB 4: USERS
# =============================================================================

def build_users_tab():
    """Build the Users tab."""
    initial_users = get_users_data()

    with gr.Tab("Users"):
        gr.Markdown('<div class="section-header">User Management</div>')

        with gr.Row():
            refresh_users_btn = gr.Button("Refresh", variant="secondary", size="sm")

        users_list = gr.Dataframe(
            value=initial_users,
            headers=['Phone', 'Language', 'Handler', 'Onboarding', 'Age', 'Name'],
            interactive=False,
            wrap=True,
            max_height=500
        )

        refresh_users_btn.click(
            fn=get_users_data,
            outputs=users_list
        )


# =============================================================================
# TAB 5: MESSAGES
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
            content = m[3] if m[3] else ''
            data.append({
                'From': m[0],
                'To': m[1],
                'Type': m[2],
                'Content': content,
                'Timestamp': m[4]
            })

        return pd.DataFrame(data)

    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return pd.DataFrame(columns=['From', 'To', 'Type', 'Content', 'Timestamp'])


def build_messages_tab():
    """Build the Messages tab."""
    initial_messages = get_recent_messages(50)

    with gr.Tab("Messages"):
        gr.Markdown('<div class="section-header">Message Log</div>')

        with gr.Row():
            search_input = gr.Textbox(
                label="Search",
                placeholder="Search by user ID or message content",
                scale=4
            )
            msg_limit = gr.Dropdown(
                choices=['25', '50', '100', '200'],
                value='50',
                label="Show",
                scale=1
            )
            search_btn = gr.Button("Search", variant="primary", size="sm", scale=1)
            refresh_messages_btn = gr.Button("Refresh", variant="secondary", size="sm", scale=1)

        messages_list = gr.Dataframe(
            value=initial_messages,
            headers=['From', 'To', 'Type', 'Content', 'Timestamp'],
            interactive=False,
            wrap=True,
            max_height=500
        )

        # Button actions
        search_btn.click(
            fn=lambda term, limit: search_messages(term, int(limit)),
            inputs=[search_input, msg_limit],
            outputs=messages_list
        )

        refresh_messages_btn.click(
            fn=lambda limit: get_recent_messages(int(limit)),
            inputs=msg_limit,
            outputs=messages_list
        )


# =============================================================================
# TAB 6: SETTINGS
# =============================================================================

def get_system_configs():
    """Get all system configurations."""
    try:
        all_configs = db.get_all_system_configs()

        data = []
        for category, configs in all_configs.items():
            for key, info in configs.items():
                data.append({
                    'Category': category.capitalize(),
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
        if not key or value is None or value == '':
            return "Error: Key and value are required.", get_system_configs()

        if db.set_system_config(key, value, category):
            return f"Configuration '{key}' updated successfully.", get_system_configs()
        else:
            return f"Error: Failed to update '{key}'. It may not be editable.", get_system_configs()

    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return f"Error: {str(e)}", get_system_configs()


def build_settings_tab():
    """Build the Settings tab."""
    initial_configs = get_system_configs()

    with gr.Tab("Settings"):
        gr.Markdown('<div class="section-header">System Configuration</div>')

        with gr.Row():
            refresh_configs_btn = gr.Button("Refresh Configs", variant="secondary", size="sm")

        configs_list = gr.Dataframe(
            value=initial_configs,
            headers=['Category', 'Key', 'Value', 'Type', 'Description', 'Editable'],
            interactive=False,
            wrap=True,
            max_height=400
        )

        gr.Markdown('<div class="section-header">Update Configuration</div>')
        gr.Markdown("*Only editable configurations can be modified.*")

        with gr.Group():
            with gr.Row():
                config_category = gr.Dropdown(
                    choices=['config', 'stats', 'health'],
                    value='config',
                    label="Category",
                    scale=1
                )
                config_key = gr.Textbox(
                    label="Config Key",
                    placeholder="e.g. maintenance_mode",
                    scale=2
                )
                config_value = gr.Textbox(
                    label="New Value",
                    placeholder="e.g. true",
                    scale=2
                )

            update_btn = gr.Button("Save Configuration", variant="primary")
            update_result = gr.Textbox(label="Result", interactive=False, show_label=False)

        # Button actions
        refresh_configs_btn.click(fn=get_system_configs, outputs=configs_list)

        update_btn.click(
            fn=update_config,
            inputs=[config_key, config_value, config_category],
            outputs=[update_result, configs_list]
        )


# =============================================================================
# TAB 7: ANALYTICS
# =============================================================================

def refresh_all_charts():
    """Regenerate all charts."""
    return (
        chart_messages_over_time(),
        chart_ticket_status(),
        chart_user_languages(),
        chart_user_demographics()
    )


def build_analytics_tab():
    """Build the Analytics tab with charts."""
    with gr.Tab("Analytics"):
        gr.Markdown('<div class="section-header">Analytics & Insights</div>')

        with gr.Row():
            refresh_charts_btn = gr.Button("Refresh Charts", variant="primary", size="sm")

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                msg_chart = gr.Plot(value=chart_messages_over_time(), label="Message Volume")
            with gr.Column(scale=2):
                ticket_chart = gr.Plot(value=chart_ticket_status(), label="Ticket Status")

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                demo_chart = gr.Plot(value=chart_user_demographics(), label="Age Distribution")
            with gr.Column(scale=2):
                lang_chart = gr.Plot(value=chart_user_languages(), label="Languages")

        refresh_charts_btn.click(
            fn=refresh_all_charts,
            outputs=[msg_chart, ticket_chart, lang_chart, demo_chart]
        )


# =============================================================================
# MAIN DASHBOARD
# =============================================================================

def build_dashboard():
    """Build the complete dashboard."""
    with gr.Blocks(
        title="Aunty Queen Connect - Admin Dashboard",
        css=DASHBOARD_CSS,
        theme=gr.themes.Base(
            primary_hue="blue",
            secondary_hue="slate",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter"),
            font_mono=gr.themes.GoogleFont("JetBrains Mono"),
        )
    ) as dashboard:

        # Header
        gr.HTML("""
        <div class="dashboard-header">
            <h1>Aunty Queen Connect</h1>
            <p>Admin Dashboard &mdash; Manage counsellors, monitor conversations, and configure system settings</p>
        </div>
        """)

        # Build all tabs
        build_overview_tab()
        build_analytics_tab()
        build_counsellors_tab()
        build_tickets_tab()
        build_users_tab()
        build_messages_tab()
        build_settings_tab()

        # Footer
        gr.HTML("""
        <div class="dashboard-footer">
            Aunty Queen Connect Admin Dashboard v2.0 &nbsp;&bull;&nbsp; SQLite &nbsp;&bull;&nbsp; Gradio
        </div>
        """)

    return dashboard


if __name__ == "__main__":
    dashboard = build_dashboard()

    dashboard_port = int(os.getenv('DASHBOARD_PORT', 7860))

    print(f"\n{'='*70}")
    print(f"  Aunty Queen Connect - Admin Dashboard")
    print(f"  http://localhost:{dashboard_port}")
    print(f"{'='*70}\n")

    dashboard.launch(
        server_port=dashboard_port,
        server_name="0.0.0.0",
        share=False,
        show_error=True
    )
