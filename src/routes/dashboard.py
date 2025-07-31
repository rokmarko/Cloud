"""
Dashboard and application feature routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.app import db
from src.models import Device, Checklist, ApproachChart, LogbookEntry, InitialLogbookTime, Pilot, Event
from src.forms import DeviceForm, ChecklistForm, LogbookEntryForm, InitialLogbookTimeForm
import json

dashboard_bp = Blueprint('dashboard', __name__)


def calculate_logbook_totals(user_id):
    """Calculate logbook totals including initial times and filtering by effective date."""
    # Get initial logbook time if it exists
    initial_time = InitialLogbookTime.query.filter_by(user_id=user_id).first()
    
    # Calculate sums from logbook entries
    if initial_time:
        # Only count entries after the effective date
        entry_totals = {
            'total_time': db.session.query(db.func.sum(LogbookEntry.flight_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'pic_time': db.session.query(db.func.sum(LogbookEntry.pilot_in_command_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'dual_time': db.session.query(db.func.sum(LogbookEntry.dual_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'instrument_time': db.session.query(db.func.sum(LogbookEntry.instrument_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'night_time': db.session.query(db.func.sum(LogbookEntry.night_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'cross_country_time': db.session.query(db.func.sum(LogbookEntry.cross_country_time)).filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).scalar() or 0,
            'total_landings': (
                db.session.query(
                    db.func.sum(LogbookEntry.landings_day + LogbookEntry.landings_night)
                ).filter(
                    LogbookEntry.user_id == user_id,
                    LogbookEntry.date >= initial_time.effective_date
                ).scalar() or 0
            )
        }
        
        # Add initial times to entry totals
        totals = {
            'total_time': entry_totals['total_time'] + initial_time.total_time,
            'pic_time': entry_totals['pic_time'] + initial_time.pilot_in_command_time,
            'dual_time': entry_totals['dual_time'] + initial_time.dual_time,
            'instrument_time': entry_totals['instrument_time'] + initial_time.instrument_time,
            'night_time': entry_totals['night_time'] + initial_time.night_time,
            'cross_country_time': entry_totals['cross_country_time'] + initial_time.cross_country_time,
            'total_landings': entry_totals['total_landings'] + initial_time.total_landings,
            'has_initial_time': True,
            'initial_time': initial_time,
            'entries_count': LogbookEntry.query.filter(
                LogbookEntry.user_id == user_id,
                LogbookEntry.date >= initial_time.effective_date
            ).count()
        }
    else:
        # No initial time, just sum all entries
        totals = {
            'total_time': db.session.query(db.func.sum(LogbookEntry.flight_time)).filter_by(user_id=user_id).scalar() or 0,
            'pic_time': db.session.query(db.func.sum(LogbookEntry.pilot_in_command_time)).filter_by(user_id=user_id).scalar() or 0,
            'dual_time': db.session.query(db.func.sum(LogbookEntry.dual_time)).filter_by(user_id=user_id).scalar() or 0,
            'instrument_time': db.session.query(db.func.sum(LogbookEntry.instrument_time)).filter_by(user_id=user_id).scalar() or 0,
            'night_time': db.session.query(db.func.sum(LogbookEntry.night_time)).filter_by(user_id=user_id).scalar() or 0,
            'cross_country_time': db.session.query(db.func.sum(LogbookEntry.cross_country_time)).filter_by(user_id=user_id).scalar() or 0,
            'total_landings': (
                db.session.query(
                    db.func.sum(LogbookEntry.landings_day + LogbookEntry.landings_night)
                ).filter_by(user_id=user_id).scalar() or 0
            ),
            'has_initial_time': False,
            'initial_time': None,
            'entries_count': LogbookEntry.query.filter_by(user_id=user_id).count()
        }
    
    return totals


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page."""
    # Get some statistics for the dashboard
    device_count = Device.query.filter_by(user_id=current_user.id, is_active=True).count()
    checklist_count = Checklist.query.filter_by(user_id=current_user.id, is_active=True).count()
    logbook_count = LogbookEntry.query.filter_by(user_id=current_user.id).count()
    
    # Get pilot mapping count (aircraft the user has access to)
    pilot_mapping_count = Pilot.query.filter_by(user_id=current_user.id, is_active=True)\
        .join(Device).filter(Device.is_active == True).count()
    
    # Get recent logbook entries
    recent_entries = LogbookEntry.query.filter_by(user_id=current_user.id)\
        .order_by(LogbookEntry.date.desc()).limit(5).all()
    
    # Calculate total flight time using new function
    totals = calculate_logbook_totals(current_user.id)
    total_flight_time = totals['total_time']
    
    return render_template('dashboard/index.html', 
                         title='Dashboard',
                         device_count=device_count,
                         checklist_count=checklist_count,
                         logbook_count=logbook_count,
                         pilot_mapping_count=pilot_mapping_count,
                         recent_entries=recent_entries,
                         total_flight_time=total_flight_time,
                         totals=totals)


@dashboard_bp.route('/devices')
@login_required
def devices():
    """Device management page."""
    devices = Device.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Add logbook entry count for each device
    for device in devices:
        device.logbook_entry_count = LogbookEntry.query.filter_by(device_id=device.id).count()
        # Calculate total flight time for this device
        entries = LogbookEntry.query.filter_by(device_id=device.id).all()
        device.total_flight_time = sum(entry.flight_time or 0 for entry in entries)
    
    return render_template('dashboard/devices.html', title='My Devices', devices=devices)


@dashboard_bp.route('/devices/add', methods=['GET', 'POST'])
@login_required
def add_device():
    """Add new device."""
    form = DeviceForm()
    if form.validate_on_submit():
        device = Device(
            name=form.name.data,
            device_type=form.device_type.data,
            model=form.model.data,
            serial_number=form.serial_number.data,
            registration=form.registration.data,
            user_id=current_user.id
        )
        db.session.add(device)
        db.session.commit()
        flash('Device added successfully!', 'success')
        return redirect(url_for('dashboard.devices'))
    
    return render_template('dashboard/add_device.html', title='Add Device', form=form)


@dashboard_bp.route('/devices/<int:device_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_device(device_id):
    """Edit device."""
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first_or_404()
    
    form = DeviceForm(obj=device)
    if form.validate_on_submit():
        form.populate_obj(device)
        db.session.commit()
        flash('Device updated successfully!', 'success')
        return redirect(url_for('dashboard.devices'))
    
    return render_template('dashboard/edit_device.html', title='Edit Device', form=form, device=device)


@dashboard_bp.route('/devices/<int:device_id>/delete', methods=['POST'])
@login_required
def delete_device(device_id):
    """Delete device."""
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first_or_404()
    device.is_active = False
    db.session.commit()
    flash('Device deleted successfully!', 'success')
    return redirect(url_for('dashboard.devices'))


@dashboard_bp.route('/devices/<int:device_id>/logbook')
@login_required
def device_logbook(device_id):
    """View all logbook entries linked to a specific device (for device owner)."""
    device = Device.query.filter_by(id=device_id, user_id=current_user.id, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get all logbook entries linked to this device
    entries = LogbookEntry.query.filter_by(device_id=device_id)\
        .order_by(LogbookEntry.date.desc(), LogbookEntry.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate totals for this device
    device_entries = LogbookEntry.query.filter_by(device_id=device_id).all()
    total_flight_time = sum(entry.flight_time or 0 for entry in device_entries)
    total_entries = len(device_entries)
    
    # Count unique pilots who have flown this device
    unique_pilots = set()
    for entry in device_entries:
        if entry.pilot_name:
            unique_pilots.add(entry.pilot_name)
        elif entry.user:
            unique_pilots.add(entry.user.full_name)
    
    return render_template('dashboard/device_logbook.html',
                         title=f'Logbook - {device.name}',
                         device=device,
                         entries=entries,
                         total_flight_time=total_flight_time,
                         total_entries=total_entries,
                         unique_pilots_count=len(unique_pilots))


@dashboard_bp.route('/api/device/<int:device_id>', methods=['DELETE'])
@login_required
def api_delete_device(device_id):
    """Delete a device via API (soft delete)."""
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Soft delete by setting is_active to False
    device.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Device deleted successfully'
    })


@dashboard_bp.route('/api/device/<int:device_id>/duplicate', methods=['POST'])
@login_required
def api_duplicate_device(device_id):
    """Duplicate a device."""
    original = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Create a copy
    duplicate = Device(
        name=f"{original.name} (Copy)",
        device_type=original.device_type,
        model=original.model,
        serial_number=f"{original.serial_number}_copy_{device_id}",  # Ensure unique serial
        registration=f"{original.registration}_copy" if original.registration else None,
        user_id=current_user.id
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Device duplicated successfully',
        'new_id': duplicate.id
    })


@dashboard_bp.route('/checklists')
@login_required
def checklists():
    """Checklist management page."""
    checklists = Checklist.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('dashboard/checklists.html', title='Checklists', checklists=checklists)


@dashboard_bp.route('/checklists/add', methods=['GET', 'POST'])
@login_required
def add_checklist():
    """Add new checklist."""
    form = ChecklistForm()
    if form.validate_on_submit():
        # Convert items to JSON format
        items = [item.strip() for item in form.items.data.split('\n') if item.strip()]
        
        checklist = Checklist(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            items=json.dumps(items),
            user_id=current_user.id
        )
        db.session.add(checklist)
        db.session.commit()
        flash('Checklist added successfully!', 'success')
        return redirect(url_for('dashboard.checklists'))
    
    return render_template('dashboard/add_checklist.html', title='Add Checklist', form=form)


@dashboard_bp.route('/checklists/<int:checklist_id>')
@login_required
def view_checklist(checklist_id):
    """View checklist details."""
    checklist = Checklist.query.filter_by(id=checklist_id, user_id=current_user.id).first_or_404()
    items = json.loads(checklist.items)
    return render_template('dashboard/view_checklist.html', 
                         title=checklist.title, 
                         checklist=checklist, 
                         items=items)


@dashboard_bp.route('/approach-charts')
@login_required
def approach_charts():
    """Approach charts page."""
    charts = ApproachChart.query.filter_by(is_active=True).all()
    return render_template('dashboard/approach_charts.html', title='Approach Charts', charts=charts)


@dashboard_bp.route('/logbook')
@login_required
def logbook():
    """Logbook page."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    entries = LogbookEntry.query.filter_by(user_id=current_user.id)\
        .order_by(LogbookEntry.date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate totals using new function
    totals = calculate_logbook_totals(current_user.id)
    
    return render_template('dashboard/logbook.html', 
                         title='Logbook', 
                         entries=entries, 
                         totals=totals)


@dashboard_bp.route('/logbook/add', methods=['GET', 'POST'])
@login_required
def add_logbook_entry():
    """Add new logbook entry."""
    form = LogbookEntryForm()
    if form.validate_on_submit():
        entry = LogbookEntry(
            date=form.date.data,
            aircraft_type=form.aircraft_type.data,
            aircraft_registration=form.aircraft_registration.data,
            departure_airport=form.departure_airport.data,
            arrival_airport=form.arrival_airport.data,
            flight_time=form.flight_time.data,
            pilot_in_command_time=form.pilot_in_command_time.data or 0,
            dual_time=form.dual_time.data or 0,
            instrument_time=form.instrument_time.data or 0,
            night_time=form.night_time.data or 0,
            cross_country_time=form.cross_country_time.data or 0,
            landings_day=form.landings_day.data or 0,
            landings_night=form.landings_night.data or 0,
            remarks=form.remarks.data,
            user_id=current_user.id
        )
        db.session.add(entry)
        db.session.commit()
        flash('Logbook entry added successfully!', 'success')
        return redirect(url_for('dashboard.logbook'))
    
    return render_template('dashboard/add_logbook_entry.html', title='Add Logbook Entry', form=form)


@dashboard_bp.route('/my-aircraft-access')
@login_required
def my_aircraft_access():
    """Show devices/aircraft that the current user is mapped to as a pilot."""
    # Get all pilot mappings for the current user
    pilot_mappings = Pilot.query.filter_by(user_id=current_user.id, is_active=True)\
        .join(Device)\
        .filter(Device.is_active == True)\
        .order_by(Device.name.asc()).all()
    
    # Calculate statistics for each mapping
    for mapping in pilot_mappings:
        # Get logbook entries for this pilot on this device
        entries = LogbookEntry.query.filter_by(
            pilot_name=mapping.pilot_name,
            device_id=mapping.device_id
        ).all()
        
        mapping.logbook_entry_count = len(entries)
        mapping.total_flight_time = sum(entry.flight_time or 0 for entry in entries)
        
        # Get recent entries (last 5)
        mapping.recent_entries = LogbookEntry.query.filter_by(
            pilot_name=mapping.pilot_name,
            device_id=mapping.device_id
        ).order_by(LogbookEntry.date.desc()).limit(5).all()
    
    return render_template('dashboard/my_aircraft_access.html',
                         title='My Aircraft',
                         pilot_mappings=pilot_mappings)


@dashboard_bp.route('/logbook/initial-time', methods=['GET', 'POST'])
@login_required
def initial_logbook_time():
    """Set or edit initial logbook time."""
    form = InitialLogbookTimeForm()
    
    # Check if user already has initial time set
    existing_initial = InitialLogbookTime.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'GET' and existing_initial:
        # Pre-populate form with existing data
        form.effective_date.data = existing_initial.effective_date
        form.total_time.data = existing_initial.total_time
        form.pilot_in_command_time.data = existing_initial.pilot_in_command_time
        form.dual_time.data = existing_initial.dual_time
        form.instrument_time.data = existing_initial.instrument_time
        form.night_time.data = existing_initial.night_time
        form.cross_country_time.data = existing_initial.cross_country_time
        form.total_landings.data = existing_initial.total_landings
        form.notes.data = existing_initial.notes
    
    if form.validate_on_submit():
        if existing_initial:
            # Update existing record
            existing_initial.effective_date = form.effective_date.data
            existing_initial.total_time = form.total_time.data
            existing_initial.pilot_in_command_time = form.pilot_in_command_time.data or 0
            existing_initial.dual_time = form.dual_time.data or 0
            existing_initial.instrument_time = form.instrument_time.data or 0
            existing_initial.night_time = form.night_time.data or 0
            existing_initial.cross_country_time = form.cross_country_time.data or 0
            existing_initial.total_landings = form.total_landings.data or 0
            existing_initial.notes = form.notes.data
            flash('Initial logbook time updated successfully!', 'success')
        else:
            # Create new record
            initial_time = InitialLogbookTime(
                effective_date=form.effective_date.data,
                total_time=form.total_time.data,
                pilot_in_command_time=form.pilot_in_command_time.data or 0,
                dual_time=form.dual_time.data or 0,
                instrument_time=form.instrument_time.data or 0,
                night_time=form.night_time.data or 0,
                cross_country_time=form.cross_country_time.data or 0,
                total_landings=form.total_landings.data or 0,
                notes=form.notes.data,
                user_id=current_user.id
            )
            db.session.add(initial_time)
            flash('Initial logbook time set successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('dashboard.logbook'))
    
    return render_template('dashboard/initial_logbook_time.html', 
                         title='Set Initial Logbook Time', 
                         form=form, 
                         existing_initial=existing_initial)


@dashboard_bp.route('/logbook/initial-time/delete', methods=['POST'])
@login_required
def delete_initial_logbook_time():
    """Delete initial logbook time."""
    initial_time = InitialLogbookTime.query.filter_by(user_id=current_user.id).first()
    if initial_time:
        db.session.delete(initial_time)
        db.session.commit()
        flash('Initial logbook time removed successfully!', 'success')
    else:
        flash('No initial logbook time found to delete.', 'error')
    
    return redirect(url_for('dashboard.logbook'))


# API Endpoints for Checklist Editor Integration

@dashboard_bp.route('/api/checklist/<int:checklist_id>', methods=['GET'])
@login_required
def api_get_checklist(checklist_id):
    """Get checklist data for the editor."""
    checklist = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Parse checklist data if it's stored as JSON
    try:
        data = json.loads(checklist.items) if checklist.items else {}
    except (json.JSONDecodeError, TypeError):
        data = {}
    
    return jsonify({
        'id': checklist.id,
        'title': checklist.title,
        'category': checklist.category,
        'description': checklist.description,
        'data': data
    })


@dashboard_bp.route('/api/checklist/<int:checklist_id>', methods=['PUT'])
@login_required
def api_update_checklist(checklist_id):
    """Update checklist data from the editor."""
    checklist = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    
    # Update checklist fields
    if 'title' in request_data:
        checklist.title = request_data['title']
    if 'description' in request_data:
        checklist.description = request_data['description']
    if 'category' in request_data:
        checklist.category = request_data['category']
    if 'data' in request_data:
        checklist.items = json.dumps(request_data['data'])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Checklist updated successfully'
    })


@dashboard_bp.route('/api/checklist/<int:checklist_id>/duplicate', methods=['POST'])
@login_required
def api_duplicate_checklist(checklist_id):
    """Duplicate a checklist."""
    original = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Create a copy
    duplicate = Checklist(
        title=f"{original.title} (Copy)",
        category=original.category,
        description=original.description,
        items=original.items,
        user_id=current_user.id
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Checklist duplicated successfully',
        'new_id': duplicate.id
    })


@dashboard_bp.route('/api/checklist/<int:checklist_id>', methods=['DELETE'])
@login_required
def api_delete_checklist(checklist_id):
    """Delete a checklist (soft delete)."""
    checklist = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Soft delete by setting is_active to False
    checklist.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Checklist deleted successfully'
    })


@dashboard_bp.route('/events')
@login_required
def events():
    """Display events for user's devices."""
    page = request.args.get('page', 1, type=int)
    device_filter = request.args.get('device', type=int)
    event_type_filter = request.args.get('event_type', '')
    
    # Get user's devices
    user_devices = Device.query.filter_by(user_id=current_user.id, is_active=True).all()
    device_ids = [device.id for device in user_devices]
    
    if not device_ids:
        # User has no devices
        events = []
        pagination = None
        device_filter_obj = None
    else:
        # Build query for events from user's devices
        query = Event.query.filter(Event.device_id.in_(device_ids))
        
        # Apply device filter
        device_filter_obj = None
        if device_filter:
            device_filter_obj = Device.query.filter_by(id=device_filter, user_id=current_user.id).first()
            if device_filter_obj:
                query = query.filter(Event.device_id == device_filter)
        
        # Apply event type filter
        if event_type_filter and event_type_filter in Event.EVENT_BITS:
            bit_position = Event.EVENT_BITS[event_type_filter]
            bit_mask = 1 << bit_position
            query = query.filter(Event.bitfield.op('&')(bit_mask) != 0)
        
        # Order by newest first (highest page_address)
        query = query.order_by(Event.page_address.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=50, error_out=False
        )
        events = pagination.items
    
    # Calculate statistics
    stats = {}
    if device_ids:
        stats['total_events'] = Event.query.filter(Event.device_id.in_(device_ids)).count()
        
        # Count events by type
        for event_name, bit_position in Event.EVENT_BITS.items():
            bit_mask = 1 << bit_position
            count = Event.query.filter(
                Event.device_id.in_(device_ids),
                Event.bitfield.op('&')(bit_mask) != 0
            ).count()
            stats[f'{event_name.lower()}_count'] = count
    else:
        stats = {'total_events': 0}
        for event_name in Event.EVENT_BITS.keys():
            stats[f'{event_name.lower()}_count'] = 0
    
    return render_template(
        'dashboard/events.html',
        events=events,
        pagination=pagination,
        user_devices=user_devices,
        device_filter=device_filter,
        device_filter_obj=device_filter_obj,
        event_type_filter=event_type_filter,
        event_types=Event.EVENT_BITS,
        stats=stats
    )
