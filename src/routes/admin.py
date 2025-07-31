"""
Admin routes for KanardiaCloud
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from src.app import db
from src.models import User, Device, Checklist, LogbookEntry, Pilot, Event
from src.forms import PilotMappingForm
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
    
    # Get events count
    events_count = Event.query.count()
    
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
                         events_count=events_count,
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


@admin_bp.route('/sync/clear-events', methods=['POST'])
@login_required
@admin_required
def clear_events():
    """Clear all device events."""
    try:
        # Find all events
        all_events = Event.query.all()
        count = len(all_events)
        
        if count == 0:
            flash('No events found to clear.', 'info')
            return redirect(url_for('admin.sync_management'))
        
        # Get some statistics for logging
        device_counts = {}
        event_type_counts = {}
        
        for event in all_events:
            device_name = event.device.name if event.device else f"Device ID {event.device_id}"
            device_counts[device_name] = device_counts.get(device_name, 0) + 1
            
            # Count active event types
            active_events = event.get_active_events()
            for event_type in active_events:
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Delete all events
        for event in all_events:
            db.session.delete(event)
        
        db.session.commit()
        
        # Create detailed log message
        devices_summary = ", ".join([f"{device}: {count} events" for device, count in device_counts.items()])
        event_types_summary = ", ".join([f"{event_type}: {count}" for event_type, count in event_type_counts.items()])
        
        current_app.logger.info(f"Admin {current_user.nickname} cleared {count} device events "
                              f"(Devices: {devices_summary}, Event types: {event_types_summary})")
        
        flash(f'Successfully cleared {count} device events from {len(device_counts)} devices.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error clearing events: {str(e)}")
        flash('Error clearing events. Please try again.', 'error')
    
    return redirect(url_for('admin.sync_management'))


@admin_bp.route('/pilots')
@login_required
@admin_required
def pilots():
    """Pilot mappings management page."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    device_filter = request.args.get('device_filter', '')
    
    # Create the form
    form = PilotMappingForm()
    
    # Populate form choices
    form.user_id.choices = [(user.id, f"{user.nickname or user.email} ({user.email})") 
                           for user in User.query.filter_by(is_active=True).order_by(User.email.asc()).all()]
    form.device_id.choices = [(device.id, f"{device.name} ({device.registration})") 
                             for device in Device.query.filter_by(is_active=True).order_by(Device.name.asc()).all()]
    
    # Base query
    query = Pilot.query
    
    # Apply search filter
    if search:
        query = query.join(User).filter(
            db.or_(
                Pilot.pilot_name.contains(search),
                User.email.contains(search),
                User.nickname.contains(search)
            )
        )
    
    # Apply device filter
    if device_filter:
        query = query.join(Device).filter(Device.id == device_filter)
    
    pilots = query.order_by(Pilot.pilot_name.asc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all devices for filter dropdown
    devices = Device.query.filter_by(is_active=True).order_by(Device.name.asc()).all()
    
    # Get all users for mapping dropdown
    users = User.query.filter_by(is_active=True).order_by(User.email.asc()).all()
    
    # Get unmapped pilots from logbook entries
    unmapped_pilots = db.session.query(LogbookEntry.pilot_name.distinct().label('pilot_name'))\
        .filter(LogbookEntry.pilot_name.isnot(None))\
        .filter(~LogbookEntry.pilot_name.in_(
            db.session.query(Pilot.pilot_name)
        )).all()
    
    return render_template('admin/pilots.html',
                         title='Pilot Mappings',
                         pilots=pilots,
                         devices=devices,
                         users=users,
                         form=form,
                         unmapped_pilots=[p.pilot_name for p in unmapped_pilots],
                         search=search,
                         device_filter=device_filter)


@admin_bp.route('/pilots/create', methods=['POST'])
@login_required
@admin_required
def create_pilot_mapping():
    """Create a new pilot mapping."""
    form = PilotMappingForm()
    
    # Populate form choices
    form.user_id.choices = [(user.id, f"{user.nickname or user.email} ({user.email})") 
                           for user in User.query.filter_by(is_active=True).order_by(User.email.asc()).all()]
    form.device_id.choices = [(device.id, f"{device.name} ({device.registration})") 
                             for device in Device.query.filter_by(is_active=True).order_by(Device.name.asc()).all()]
    
    if form.validate_on_submit():
        pilot_name = (form.pilot_name.data or '').strip()
        user_id = form.user_id.data
        device_id = form.device_id.data
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            flash('Selected user does not exist.', 'error')
            return redirect(url_for('admin.pilots'))
        
        # Check if device exists
        device = Device.query.get(device_id)
        if not device:
            flash('Selected device does not exist.', 'error')
            return redirect(url_for('admin.pilots'))
        
        # Check if mapping already exists
        existing = Pilot.query.filter_by(
            pilot_name=pilot_name,
            device_id=device_id
        ).first()
        
        if existing:
            flash(f'Mapping for pilot "{pilot_name}" on device "{device.name}" already exists.', 'error')
            return redirect(url_for('admin.pilots'))
        
        try:
            # Create new pilot mapping
            pilot = Pilot(
                pilot_name=pilot_name,
                user_id=user_id,
                device_id=device_id
            )
            db.session.add(pilot)
            db.session.commit()
            
            current_app.logger.info(f"Admin {current_user.nickname} created pilot mapping: "
                                  f"{pilot_name} -> {user.email} on {device.name}")
            flash(f'Successfully created pilot mapping: {pilot_name} -> {user.email} on {device.name}', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating pilot mapping: {str(e)}")
            flash('Error creating pilot mapping. Please try again.', 'error')
    else:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('admin.pilots'))


@admin_bp.route('/pilots/<int:pilot_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_pilot_mapping(pilot_id):
    """Delete a pilot mapping."""
    pilot = Pilot.query.get_or_404(pilot_id)
    
    try:
        pilot_info = f"{pilot.pilot_name} -> {pilot.user.email} on {pilot.device.name}"
        db.session.delete(pilot)
        db.session.commit()
        
        current_app.logger.info(f"Admin {current_user.nickname} deleted pilot mapping: {pilot_info}")
        flash(f'Successfully deleted pilot mapping: {pilot_info}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pilot mapping: {str(e)}")
        flash('Error deleting pilot mapping. Please try again.', 'error')
    
    return redirect(url_for('admin.pilots'))


@admin_bp.route('/api/pilots/suggestions')
@login_required
@admin_required
def pilot_suggestions():
    """Get pilot name suggestions from logbook entries."""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Get pilot names from logbook entries that match the query
    pilot_names = db.session.query(LogbookEntry.pilot_name.distinct().label('pilot_name'))\
        .filter(LogbookEntry.pilot_name.isnot(None))\
        .filter(LogbookEntry.pilot_name.contains(query))\
        .limit(10).all()
    
    return jsonify([p.pilot_name for p in pilot_names])


@admin_bp.route('/events')
@login_required
@admin_required
def events():
    """Admin view of all device events."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    device_id = request.args.get('device_id', type=int)
    event_type = request.args.get('event_type', 'all')  # all, takeoff, landing, etc.
    
    # Build query
    query = Event.query
    
    # Filter by device
    if device_id:
        query = query.filter(Event.device_id == device_id)
    
    # Filter by event type (bitfield)
    if event_type != 'all' and event_type in Event.EVENT_BITS:
        bit_position = Event.EVENT_BITS[event_type]
        bit_mask = 1 << bit_position
        query = query.filter(Event.bitfield.op('&')(bit_mask) != 0)
    
    # Order by date descending
    query = query.order_by(Event.date_time.desc().nullslast(), Event.created_at.desc())
    
    # Paginate
    events = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all devices for filter dropdown
    devices = Device.query.filter_by(is_active=True).all()
    
    # Get event type counts for statistics
    event_stats = {}
    for event_name, bit_position in Event.EVENT_BITS.items():
        bit_mask = 1 << bit_position
        count = Event.query.filter(Event.bitfield.op('&')(bit_mask) != 0).count()
        event_stats[event_name] = count
    
    return render_template('admin/events.html',
                         title='Device Events',
                         events=events,
                         devices=devices,
                         event_types=Event.EVENT_BITS,
                         event_stats=event_stats,
                         selected_device_id=device_id,
                         selected_event_type=event_type)


@admin_bp.route('/events/<int:event_id>')
@login_required
@admin_required
def event_detail(event_id):
    """View detailed information about a specific event."""
    event = Event.query.get_or_404(event_id)
    
    # Check if the current user has access to this event
    # Events are only accessible to device owners or admins
    if not current_user.is_admin and event.device.user_id != current_user.id:
        flash('Access denied. You can only view events from your own devices.', 'error')
        return redirect(url_for('admin.events'))
    
    return render_template('admin/event_detail.html',
                         title=f'Event {event_id}',
                         event=event)
