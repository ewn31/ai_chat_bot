"""
Dashboard REST API Blueprint

Provides JSON endpoints for the React admin dashboard.
All endpoints require X-API-Key header authentication.
"""

from flask import Blueprint, request, jsonify
import database.db as db
import counsellors
import ticket
import logging
from counsellor_handler import create_counsellor
from api.auth import require_api_key

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


# =============================================================================
# STATS
# =============================================================================

@dashboard_bp.route('/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get overview statistics."""
    try:
        db.update_system_stats()

        stats_data = db.get_all_system_configs(category='stats')
        config_data = db.get_all_system_configs(category='config')
        health_data = db.get_all_system_configs(category='health')

        stats = {
            'total_users': int(stats_data['stats']['total_users']['value']) if stats_data else 0,
            'total_messages': int(stats_data['stats']['total_messages']['value']) if stats_data else 0,
            'active_tickets': int(stats_data['stats']['active_tickets']['value']) if stats_data else 0,
            'total_counsellors': len(db.get_counsellors()),
            'maintenance_mode': config_data['config']['maintenance_mode']['value'] if config_data else False,
            'ai_model': config_data['config']['ai_model_version']['value'] if config_data else 'N/A',
            'db_version': int(health_data['health']['db_version']['value']) if health_data else 0,
        }

        return jsonify({'success': True, 'stats': stats}), 200

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ANALYTICS
# =============================================================================

@dashboard_bp.route('/analytics/messages-per-day', methods=['GET'])
@require_api_key
def analytics_messages_per_day():
    """Daily message counts for the last N days."""
    try:
        days = request.args.get('days', 30, type=int)

        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT DATE(timestamp) as day, COUNT(*) as count
            FROM messages
            WHERE timestamp >= DATE('now', ?)
            GROUP BY DATE(timestamp)
            ORDER BY day
        """, (f'-{days} days',))
        rows = cur.fetchall()
        db.close_db(conn)

        data = [{'date': row[0], 'count': row[1]} for row in rows]
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logger.error(f"Error getting messages-per-day: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/analytics/ticket-status', methods=['GET'])
@require_api_key
def analytics_ticket_status():
    """Ticket count by status."""
    try:
        conn = db.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) FROM tickets GROUP BY status")
        rows = cur.fetchall()
        db.close_db(conn)

        data = [{'status': (row[0] or 'unknown').capitalize(), 'count': row[1]} for row in rows]
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logger.error(f"Error getting ticket-status analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/analytics/user-languages', methods=['GET'])
@require_api_key
def analytics_user_languages():
    """User count by language."""
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

        data = [{'language': row[0], 'count': row[1]} for row in rows]
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logger.error(f"Error getting user-languages analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/analytics/user-demographics', methods=['GET'])
@require_api_key
def analytics_user_demographics():
    """User count by age range."""
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

        data = [{'age_range': row[0], 'count': row[1]} for row in rows]
        return jsonify({'success': True, 'data': data}), 200

    except Exception as e:
        logger.error(f"Error getting user-demographics analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# TICKETS
# =============================================================================

@dashboard_bp.route('/tickets', methods=['GET'])
@require_api_key
def get_tickets():
    """List tickets with optional status filter and pagination."""
    try:
        status_filter = request.args.get('status', 'all')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        conn = db.connect_db()
        cur = conn.cursor()

        if status_filter and status_filter != 'all':
            cur.execute("""
                SELECT id, status, handler, user, created_at, closed_at
                FROM tickets
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (status_filter, limit, offset))
        else:
            cur.execute("""
                SELECT id, status, handler, user, created_at, closed_at
                FROM tickets
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = cur.fetchall()
        db.close_db(conn)

        tickets_list = []
        for t in rows:
            tickets_list.append({
                'id': t[0],
                'status': (t[1] or 'unknown').capitalize(),
                'handler': t[2] if t[2] else 'Unassigned',
                'user': t[3],
                'created_at': t[4],
                'closed_at': t[5]
            })

        return jsonify({'success': True, 'count': len(tickets_list), 'tickets': tickets_list}), 200

    except Exception as e:
        logger.error(f"Error getting tickets: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/tickets/<ticket_id>', methods=['GET'])
@require_api_key
def get_ticket_details(ticket_id):
    """Get full ticket details including transcript."""
    try:
        ticket_data = ticket.get_ticket(ticket_id)

        if not ticket_data:
            return jsonify({'success': False, 'error': f'Ticket "{ticket_id}" not found'}), 404

        result = {
            'id': ticket_data.get('id'),
            'status': ticket_data.get('status'),
            'handler': ticket_data.get('handler'),
            'user': ticket_data.get('user'),
            'transcript': ticket_data.get('transcript'),
            'created_at': ticket_data.get('created_at'),
            'closed_at': ticket_data.get('closed_at'),
        }

        return jsonify({'success': True, 'ticket': result}), 200

    except Exception as e:
        logger.error(f"Error getting ticket {ticket_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/tickets/<ticket_id>/status', methods=['PATCH'])
@require_api_key
def update_ticket_status(ticket_id):
    """Update a ticket's status."""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Missing "status" field'}), 400

        new_status = data['status']
        if new_status not in ('open', 'in_progress', 'closed'):
            return jsonify({'success': False, 'error': 'Invalid status. Must be: open, in_progress, closed'}), 400

        if db.update_ticket_status(ticket_id, new_status):
            return jsonify({'success': True, 'message': f'Ticket status updated to {new_status}'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to update ticket status'}), 500

    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id} status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# USERS
# =============================================================================

@dashboard_bp.route('/users', methods=['GET'])
@require_api_key
def get_users():
    """List users with pagination and optional search."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '')

        conn = db.connect_db()
        cur = conn.cursor()

        if search:
            cur.execute("""
                SELECT id, language, handler, onboarding_level, age, gender
                FROM users
                WHERE id LIKE ?
                ORDER BY rowid DESC
                LIMIT ? OFFSET ?
            """, (f'%{search}%', limit, offset))
        else:
            cur.execute("""
                SELECT id, language, handler, onboarding_level, age, gender
                FROM users
                ORDER BY rowid DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = cur.fetchall()
        db.close_db(conn)

        users_list = []
        for u in rows:
            users_list.append({
                'id': u[0],
                'language': (u[1] or '').upper() if u[1] else None,
                'handler': u[2],
                'onboarding_level': u[3],
                'age': u[4],
                'gender': u[5],
            })

        return jsonify({'success': True, 'count': len(users_list), 'users': users_list}), 200

    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# MESSAGES
# =============================================================================

@dashboard_bp.route('/messages', methods=['GET'])
@require_api_key
def get_messages():
    """List messages with pagination and optional search."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '')

        conn = db.connect_db()
        cur = conn.cursor()

        if search:
            cur.execute("""
                SELECT id, _from, _to, _type, content, timestamp
                FROM messages
                WHERE _from LIKE ? OR _to LIKE ? OR content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (f'%{search}%', f'%{search}%', f'%{search}%', limit, offset))
        else:
            cur.execute("""
                SELECT id, _from, _to, _type, content, timestamp
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        rows = cur.fetchall()
        db.close_db(conn)

        messages_list = []
        for m in rows:
            messages_list.append({
                'id': m[0],
                'from': m[1],
                'to': m[2],
                'type': m[3],
                'content': m[4],
                'timestamp': m[5],
            })

        return jsonify({'success': True, 'count': len(messages_list), 'messages': messages_list}), 200

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# SETTINGS
# =============================================================================

@dashboard_bp.route('/settings', methods=['GET'])
@require_api_key
def get_settings():
    """Get system configurations."""
    try:
        category = request.args.get('category', None)
        configs = db.get_all_system_configs(category=category)
        return jsonify({'success': True, 'configs': configs}), 200

    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/settings/<category>/<key>', methods=['PUT'])
@require_api_key
def update_setting(category, key):
    """Update a system configuration value."""
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({'success': False, 'error': 'Missing "value" field'}), 400

        if db.set_system_config(key, data['value'], category):
            return jsonify({'success': True, 'message': f"Configuration '{key}' updated successfully"}), 200
        else:
            return jsonify({'success': False, 'error': f"Failed to update '{key}'. It may not be editable."}), 400

    except Exception as e:
        logger.error(f"Error updating setting {category}/{key}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# COUNSELLORS
# =============================================================================

@dashboard_bp.route('/counsellors', methods=['GET'])
@require_api_key
def get_all_counsellors():
    """Get all counsellors (password excluded)."""
    try:
        counsellors_data = db.get_counsellors_details()

        counsellors_list = []
        for c in counsellors_data:
            counsellors_list.append({
                'id': c[0],
                'name': c[1],
                'username': c[2],
                'email': c[4],
                'phone': c[5],
                'channels': c[6],
                'current_ticket': c[7]
            })

        return jsonify({'success': True, 'count': len(counsellors_list), 'counsellors': counsellors_list}), 200

    except Exception as e:
        logger.error(f"Error retrieving counsellors: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/counsellors/<username>', methods=['GET'])
@require_api_key
def get_counsellor(username):
    """Get a specific counsellor by username (password excluded)."""
    try:
        counsellor = db.get_counsellor(username)

        if not counsellor:
            return jsonify({'success': False, 'error': f'Counsellor "{username}" not found'}), 404

        result = {
            'id': counsellor[0],
            'name': counsellor[1],
            'username': counsellor[2],
            'email': counsellor[4],
            'phone': counsellor[5],
            'channels': counsellor[6],
            'current_ticket': counsellor[7]
        }

        return jsonify({'success': True, 'counsellor': result}), 200

    except Exception as e:
        logger.error(f"Error retrieving counsellor {username}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/counsellors', methods=['POST'])
@require_api_key
def create_counsellor_endpoint():
    """Create a new counsellor."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        required_fields = ['username', 'email']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 400

        username = data['username']
        email = data['email']
        name = data.get('name', username)
        password = data.get('password', '')
        whatsapp = data.get('whatsapp')

        if whatsapp:
            whatsapp = whatsapp.strip().replace('@s.whatsapp.net', '')

        create_counsellor(username, password, email, name=name, whatsapp_number=whatsapp)

        return jsonify({
            'success': True,
            'message': f'Counsellor "{username}" created successfully',
            'counsellor': {'username': username, 'email': email, 'name': name}
        }), 201

    except Exception as e:
        logger.error(f"Error creating counsellor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/counsellors/<username>', methods=['PUT', 'PATCH'])
@require_api_key
def update_counsellor(username):
    """Update a counsellor's information."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({'success': False, 'error': f'Counsellor "{username}" not found'}), 404

        allowed_fields = ['name', 'email', 'phone', 'password']
        updated_fields = []

        for field in allowed_fields:
            if field in data:
                if db.update_counsellor(username, field, data[field]):
                    updated_fields.append(field)

        if updated_fields:
            return jsonify({
                'success': True,
                'message': f'Counsellor "{username}" updated',
                'updated_fields': updated_fields
            }), 200
        else:
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400

    except Exception as e:
        logger.error(f"Error updating counsellor {username}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/counsellors/<username>', methods=['DELETE'])
@require_api_key
def delete_counsellor(username):
    """Delete a counsellor."""
    try:
        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({'success': False, 'error': f'Counsellor "{username}" not found'}), 404

        if counsellors.remove_counsellor(username):
            return jsonify({'success': True, 'message': f'Counsellor "{username}" deleted'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to delete counsellor'}), 500

    except Exception as e:
        logger.error(f"Error deleting counsellor {username}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@dashboard_bp.route('/counsellors/<username>/channels', methods=['POST'])
@require_api_key
def add_counsellor_channel(username):
    """Add a channel to a counsellor."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        required_fields = ['channel', 'channel_id']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 400

        counsellor = db.get_counsellor(username)
        if not counsellor:
            return jsonify({'success': False, 'error': f'Counsellor "{username}" not found'}), 404

        if counsellors.add_channel(username, data['channel'], data['channel_id'], data.get('auth_key'), data.get('order')):
            return jsonify({'success': True, 'message': f'Channel "{data["channel"]}" added to "{username}"'}), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to add channel'}), 500

    except Exception as e:
        logger.error(f"Error adding channel to {username}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
