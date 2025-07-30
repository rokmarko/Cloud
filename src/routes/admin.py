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


@admin_bp.route('/logbook')
@login_required
@admin_required
def logbook():
    """Admin view of all logbook entries with device linking information."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    show_synced = request.args.get('synced', 'all')  # all, synced, manual
    device_id = request.args.get('device_id', type=int)
    
    # Build query
    query = LogbookEntry.query
    
    # Filter by sync status
    if show_synced == 'synced':
        query = query.filter(LogbookEntry.device_id.isnot(None))
    elif show_synced == 'manual':
        query = query.filter(LogbookEntry.device_id.is_(None))
    
    # Filter by device
    if device_id:
        query = query.filter(LogbookEntry.device_id == device_id)
    
    # Order by date descending
    query = query.order_by(LogbookEntry.date.desc(), LogbookEntry.created_at.desc())
    
    # Paginate
    entries = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get devices for filter dropdown
    devices = Device.query.filter_by(is_active=True).order_by(Device.registration).all()
    
    # Get statistics
    total_entries = LogbookEntry.query.count()
    synced_entries = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).count()
    manual_entries = total_entries - synced_entries
    
    return render_template('admin/logbook.html',
                         title='Logbook Management',
                         entries=entries,
                         devices=devices,
                         show_synced=show_synced,
                         selected_device_id=device_id,
                         total_entries=total_entries,
                         synced_entries=synced_entries,
                         manual_entries=manual_entries)


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
    """View all devices across all users, including unlinked ones."""
    page = request.args.get('page', 1, type=int)
    
    # Show all devices (both active and inactive/unlinked)
    devices = Device.query.join(User).order_by(
        Device.is_active.desc(),  # Show active devices first
        Device.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
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


@admin_bp.route('/devices/<int:device_id>/relink', methods=['POST'])
@login_required
@admin_required
def relink_device(device_id):
    """Relink an unlinked device."""
    device = Device.query.get_or_404(device_id)
    
    if device.is_active:
        flash('Device is already active.', 'info')
        return redirect(url_for('admin.devices'))
    
    device.is_active = True
    db.session.commit()
    flash(f'Device "{device.name}" has been relinked to user {device.owner.nickname}.', 'success')
    return redirect(url_for('admin.devices'))


@admin_bp.route('/devices/<int:device_id>/delete-permanently', methods=['POST'])
@login_required
@admin_required
def delete_device_permanently(device_id):
    """Permanently delete a device from the database."""
    device = Device.query.get_or_404(device_id)
    
    if device.is_active:
        flash('Cannot permanently delete an active device. Unlink it first.', 'error')
        return redirect(url_for('admin.devices'))
    
    device_name = device.name
    owner_name = device.owner.nickname
    
    # Permanently delete the device
    db.session.delete(device)
    db.session.commit()
    
    flash(f'Device "{device_name}" has been permanently deleted from user {owner_name}.', 'warning')
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
    
    # Get synced entries count
    synced_entries_count = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).count()
    
    # Get scheduler jobs
    jobs = task_scheduler.get_jobs()
    sync_job = next((job for job in jobs if job.id == 'thingsboard_sync'), None)
    
    # Get ThingsBoard authentication status
    auth_status = thingsboard_sync.get_authentication_status()
    
    return render_template('admin/sync.html',
                         title='ThingsBoard Sync Management',
                         total_devices=total_devices,
                         sync_enabled_devices=sync_enabled_devices,
                         recent_entries=recent_entries,
                         synced_entries_count=synced_entries_count,
                         sync_job=sync_job,
                         auth_status=auth_status)


@admin_bp.route('/sync/test-auth', methods=['POST'])
@login_required
@admin_required
def test_thingsboard_auth():
    """Test ThingsBoard authentication."""
    try:
        success = thingsboard_sync.test_authentication()
        if success:
            flash('ThingsBoard authentication successful!', 'success')
        else:
            flash('ThingsBoard authentication failed. Check credentials and server connectivity.', 'error')
    except Exception as e:
        flash(f'Error testing authentication: {str(e)}', 'error')
    
    return redirect(url_for('admin.sync_management'))


@admin_bp.route('/sync/devices')
@login_required
@admin_required
def sync_devices():
    """View devices with sync configuration, including unlinked ones."""
    page = request.args.get('page', 1, type=int)
    
    # Show all devices (both active and inactive) for sync configuration
    devices = Device.query.join(User).order_by(
        Device.is_active.desc(),  # Show active devices first
        Device.external_device_id.isnot(None).desc(),  # Then prioritize devices with sync configured
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
        
        # Run sync synchronously to avoid context issues
        results = thingsboard_sync.sync_all_devices()
        current_app.logger.info(f"Manual sync completed: {results}")
        
        # Show results in flash message
        if results.get('errors'):
            flash(f"Sync completed with errors: {results['new_entries']}/{results['total_entries']} entries synced. Check logs for details.", 'warning')
        else:
            flash(f"Sync completed successfully: {results['new_entries']}/{results['total_entries']} new entries synced from {results['synced_devices']}/{results['total_devices']} devices.", 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error during manual sync: {str(e)}")
        flash('Error during sync. Please check logs.', 'error')
    
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


@admin_bp.route('/sync/clear-entries', methods=['POST'])
@login_required
@admin_required
def clear_synced_entries():
    """Clear all synced logbook entries."""
    try:
        # Find all logbook entries that have a device_id (synced entries)
        synced_entries = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).all()
        count = len(synced_entries)
        
        if count == 0:
            flash('No synced entries found to clear.', 'info')
            return redirect(url_for('admin.sync_management'))
        
        # Get some statistics for logging
        device_counts = {}
        total_flight_time = 0
        for entry in synced_entries:
            device_name = entry.device.name if entry.device else f"Device ID {entry.device_id}"
            device_counts[device_name] = device_counts.get(device_name, 0) + 1
            total_flight_time += entry.flight_time or 0
        
        # Delete all synced entries
        for entry in synced_entries:
            db.session.delete(entry)
        
        db.session.commit()
        
        # Create detailed log message
        devices_summary = ", ".join([f"{device}: {count} entries" for device, count in device_counts.items()])
        current_app.logger.info(f"Admin {current_user.nickname} cleared {count} synced logbook entries "
                              f"(Total flight time: {total_flight_time:.2f}h, Devices: {devices_summary})")
        
        flash(f'Successfully cleared {count} synced logbook entries (Total: {total_flight_time:.2f} flight hours).', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error clearing synced entries: {str(e)}")
        flash('Error clearing synced entries. Please try again.', 'error')
    
    return redirect(url_for('admin.sync_management'))
