"""
Dashboard and application feature routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.app import db
from src.models import Device, Checklist, ApproachChart, LogbookEntry
from src.forms import DeviceForm, ChecklistForm, LogbookEntryForm
import json

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page."""
    # Get some statistics for the dashboard
    device_count = Device.query.filter_by(user_id=current_user.id, is_active=True).count()
    checklist_count = Checklist.query.filter_by(user_id=current_user.id, is_active=True).count()
    logbook_count = LogbookEntry.query.filter_by(user_id=current_user.id).count()
    
    # Get recent logbook entries
    recent_entries = LogbookEntry.query.filter_by(user_id=current_user.id)\
        .order_by(LogbookEntry.date.desc()).limit(5).all()
    
    # Calculate total flight time
    total_flight_time = db.session.query(db.func.sum(LogbookEntry.flight_time))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('dashboard/index.html', 
                         title='Dashboard',
                         device_count=device_count,
                         checklist_count=checklist_count,
                         logbook_count=logbook_count,
                         recent_entries=recent_entries,
                         total_flight_time=total_flight_time)


@dashboard_bp.route('/devices')
@login_required
def devices():
    """Device management page."""
    devices = Device.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('dashboard/devices.html', title='Devices', devices=devices)


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
    
    # Calculate totals
    totals = {
        'total_time': db.session.query(db.func.sum(LogbookEntry.flight_time)).filter_by(user_id=current_user.id).scalar() or 0,
        'pic_time': db.session.query(db.func.sum(LogbookEntry.pilot_in_command_time)).filter_by(user_id=current_user.id).scalar() or 0,
        'dual_time': db.session.query(db.func.sum(LogbookEntry.dual_time)).filter_by(user_id=current_user.id).scalar() or 0,
        'instrument_time': db.session.query(db.func.sum(LogbookEntry.instrument_time)).filter_by(user_id=current_user.id).scalar() or 0,
        'night_time': db.session.query(db.func.sum(LogbookEntry.night_time)).filter_by(user_id=current_user.id).scalar() or 0,
        'cross_country_time': db.session.query(db.func.sum(LogbookEntry.cross_country_time)).filter_by(user_id=current_user.id).scalar() or 0,
    }
    
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
