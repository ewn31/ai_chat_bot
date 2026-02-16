import functools
from flask import request, jsonify
import database.db as db
import logging

logger = logging.getLogger(__name__)


def require_api_key(f):
    """Decorator that checks for a valid X-API-Key header."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'success': False, 'error': 'Missing API key'}), 401

        stored_key = db.get_system_config('dashboard_api_key', category='config')
        if not stored_key or api_key != stored_key:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 403

        return f(*args, **kwargs)
    return decorated
