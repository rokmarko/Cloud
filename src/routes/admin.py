"""
Admin routes for KanardiaCloud
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from src.app import db
from src.models import User, Device, Checklist, LogbookEntry
from src.services.thingsboard_sync import thingsboard_sync
from src.services.scheduler import task_scheduler

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard."""
    # Get statistics
    total_users = User.query.filter_by(is_active=True).count()
    total_devices = Device.query.filter_by(is_active=True).count()
    total_checklists = Checklist.query.filter_by(is_active=True).count()
    total_logbook_entries = LogbookEntry.query.count()
    
    recent_users = User.query.filter_by(is_active=True).order_by(User.created_at.desc()).limit(5).all()
    recent_devices = Device.query.filter_by(is_active=True).order_by(Device.created_at.desc()).limit(10).all()
    
    return render_template('admin/index.html', 
                         title='Admin Dashboard',
                         total_users=total_users,
                         total_devices=total_devices,
                         total_checklists=total_checklists,
                         total_logbook_entries=total_logbook_entries,
                         recent_users=recent_users,
                         recent_devices=recent_devices)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', title='Manage Users', users=users)


@admin_bp.route('/devices')
@login_required
@admin_required
def devices():
    """View all devices across all users."""
    page = request.args.get('page', 1, type=int)
    devices = Device.query.join(User).filter(Device.is_active == True).order_by(Device.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/devices.html', title='All Devices', devices=devices)


@admin_bp.route('/devices/<int:device_id>/unlink', methods=['POST'])
@login_required
@admin_required
def unlink_device(device_id):
    """Unlink (soft delete) a device from its user."""
    device = Device.query.filter_by(id=device_id, is_active=True).first_or_404()
    device.is_active = False
    db.session.commit()
    flash(f'Device "{device.name}" has been unlinked from user {device.owner.nickname}.', 'success')
    return redirect(url_for('admin.devices'))


@admin_bp.route('/api/devices/<int:device_id>', methods=['DELETE'])
@login_required
@admin_required
def api_unlink_device(device_id):
    """Unlink a device via API (soft delete)."""
    device = Device.query.filter_by(id=device_id, is_active=True).first_or_404()
    
    device_name = device.name
    user_nickname = device.owner.nickname
    
    # Soft delete by setting is_active to False
    device.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Device "{device_name}" unlinked from user {user_nickname}'
    })


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user."""
    if current_user.id == user_id:
        flash('You cannot change your own admin status.', 'error')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.nickname}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    """Toggle active status for a user."""
    if current_user.id == user_id:
        flash('You cannot change your own active status.', 'error')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.nickname} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/sync')
@login_required
@admin_required
def sync_management():
    """ThingsBoard sync management page."""
    # Get sync statistics
    total_devices = Device.query.filter_by(is_active=True).count()
    sync_enabled_devices = Device.query.filter(
        Device.is_active == True,
        Device.external_device_id.isnot(None),
        Device.external_device_id != ''
    ).count()
    
    # Get recent logbook entries (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_entries = LogbookEntry.query.filter(
        LogbookEntry.created_at >= yesterday
    ).order_by(LogbookEntry.created_at.desc()).limit(10).all()
    
    # Get scheduler jobs
    jobs = task_scheduler.get_jobs()
    sync_job = next((job for job in jobs if job.id == 'thingsboard_sync'), None)
    
    return render_template('admin/sync.html',
                         title='ThingsBoard Sync Management',
                         total_devices=total_devices,
                         sync_enabled_devices=sync_enabled_devices,
                         recent_entries=recent_entries,
                         sync_job=sync_job)


@admin_bp.route('/sync/devices')
@login_required
@admin_required
def sync_devices():
    """View devices with sync configuration."""
    page = request.args.get('page', 1, type=int)
    devices = Device.query.join(User).filter(Device.is_active == True).order_by(
        Device.external_device_id.isnot(None).desc(),
        Device.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/sync_devices.html',
                         title='Sync Device Configuration',
                         devices=devices)


@admin_bp.route('/sync/run', methods=['POST'])
@login_required
@admin_required
def run_sync_manually():
    """Manually trigger ThingsBoard sync."""
    try:
        current_app.logger.info(f"Manual sync triggered by admin user {current_user.nickname}")
        
        # Run sync in background to avoid timeout
        import threading
        
        def run_sync():
            with current_app.app_context():
                results = thingsboard_sync.sync_all_devices()
                current_app.logger.info(f"Manual sync completed: {results}")
        
        sync_thread = threading.Thread(target=run_sync)
        sync_thread.daemon = True
        sync_thread.start()
        
        flash('ThingsBoard sync started manually. Check logs for results.', 'info')
        
    except Exception as e:
        current_app.logger.error(f"Error starting manual sync: {str(e)}")
        flash('Error starting sync. Please check logs.', 'error')
    
    return redirect(url_for('admin.sync_management'))


@admin_bp.route('/sync/device/<int:device_id>/configure', methods=['POST'])
@login_required
@admin_required
def configure_device_sync(device_id):
    """Configure ThingsBoard sync for a specific device."""
    device = Device.query.get_or_404(device_id)
    
    external_device_id = request.form.get('external_device_id', '').strip()
    
    if external_device_id:
        # Check if external_device_id is already used by another device
        existing = Device.query.filter(
            Device.external_device_id == external_device_id,
            Device.id != device_id
        ).first()
        
        if existing:
            flash(f'External device ID "{external_device_id}" is already used by device "{existing.name}".', 'error')
            return redirect(url_for('admin.sync_devices'))
    
    device.external_device_id = external_device_id if external_device_id else None
    db.session.commit()
    
    if external_device_id:
        flash(f'Device "{device.name}" configured for ThingsBoard sync with ID: {external_device_id}', 'success')
    else:
        flash(f'ThingsBoard sync disabled for device "{device.name}"', 'info')
    
    return redirect(url_for('admin.sync_devices'))


@admin_bp.route('/api/sync/status')
@login_required
@admin_required
def sync_status_api():
    """API endpoint for sync status information."""
    # Get scheduler job status
    jobs = task_scheduler.get_jobs()
    sync_job = next((job for job in jobs if job.id == 'thingsboard_sync'), None)
    
    # Get sync statistics
    total_devices = Device.query.filter_by(is_active=True).count()
    sync_enabled_devices = Device.query.filter(
        Device.is_active == True,
        Device.external_device_id.isnot(None),
        Device.external_device_id != ''
    ).count()
    
    # Get recent sync activity (logbook entries from last hour)
    last_hour = datetime.utcnow() - timedelta(hours=1)
    recent_sync_entries = LogbookEntry.query.filter(
        LogbookEntry.created_at >= last_hour,
        LogbookEntry.remarks.like('%Synced from ThingsBoard%')
    ).count()
    
    return jsonify({
        'scheduler_running': sync_job is not None,
        'next_run': sync_job.next_run_time.isoformat() if sync_job and sync_job.next_run_time else None,
        'total_devices': total_devices,
        'sync_enabled_devices': sync_enabled_devices,
        'recent_sync_entries': recent_sync_entries,
        'last_check': datetime.utcnow().isoformat()
    })
