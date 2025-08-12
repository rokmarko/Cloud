"""
Dashboard and application feature routes
"""

import logging
import os
import base64
import uuid
from io import BytesIO
from datetime import datetime
from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from src.app import db
from src.models import Device, Checklist, InstrumentLayout, ApproachChart, LogbookEntry, InitialLogbookTime, Pilot, Event
from src.forms import DeviceForm, ChecklistForm, ChecklistCreateForm, ChecklistImportForm, InstrumentLayoutForm, InstrumentLayoutCreateForm, InstrumentLayoutImportForm, LogbookEntryForm, InitialLogbookTimeForm, DevicePilotMappingForm
from src.services.thingsboard_sync import ThingsBoardSyncService
import json

dashboard_bp = Blueprint('dashboard', __name__)


def process_thumbnail_base64(base64_data, thumbnail_size=(300, 200)):
    """
    Process base64 image data and return optimized base64 for database storage.
    
    Args:
        base64_data: Base64 encoded image data (may include data URI prefix)
        thumbnail_size: Tuple of (width, height) for thumbnail size
    
    Returns:
        str: Optimized base64 encoded PNG data for database storage, or None if failed
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/png;base64,")
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Open image with PIL
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Resize to thumbnail size while maintaining aspect ratio
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        # Create thumbnail with white background if needed
        if image.size != thumbnail_size:
            thumbnail = Image.new('RGB', thumbnail_size, (255, 255, 255))
            # Center the image
            x = (thumbnail_size[0] - image.size[0]) // 2
            y = (thumbnail_size[1] - image.size[1]) // 2
            thumbnail.paste(image, (x, y))
            image = thumbnail
        
        # Convert back to base64 for database storage
        buffer = BytesIO()
        image.save(buffer, format='PNG', quality=95, optimize=True)
        optimized_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return optimized_base64
        
    except Exception as e:
        logging.error(f"Error processing thumbnail base64: {e}")
        return None


def generate_thumbnail_from_base64(base64_data, layout_id, thumbnail_size=(300, 200)):
    """
    Generate a PNG thumbnail from base64 image data (legacy file-based storage).
    
    Args:
        base64_data: Base64 encoded image data (may include data URI prefix)
        layout_id: ID of the instrument layout for filename
        thumbnail_size: Tuple of (width, height) for thumbnail size
    
    Returns:
        str: Filename of saved thumbnail, or None if failed
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/png;base64,")
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Open image with PIL
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        # Resize to thumbnail size while maintaining aspect ratio
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        # Create thumbnail with white background if needed
        if image.size != thumbnail_size:
            thumbnail = Image.new('RGB', thumbnail_size, (255, 255, 255))
            # Center the image
            x = (thumbnail_size[0] - image.size[0]) // 2
            y = (thumbnail_size[1] - image.size[1]) // 2
            thumbnail.paste(image, (x, y))
            image = thumbnail
        
        # Generate unique filename
        filename = f"layout_{layout_id}_{uuid.uuid4().hex[:8]}.png"
        
        # Ensure thumbnails directory exists
        thumbnails_dir = os.path.join(current_app.static_folder, 'thumbnails', 'instrument_layouts')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Save thumbnail as PNG
        filepath = os.path.join(thumbnails_dir, filename)
        image.save(filepath, 'PNG', quality=95)
        
        return filename
        
    except Exception as e:
        logging.error(f"Error generating thumbnail for layout {layout_id}: {e}")
        return None


def delete_thumbnail(filename):
    """
    Delete a thumbnail file.
    
    Args:
        filename: Name of the thumbnail file to delete
    """
    if filename:
        try:
            filepath = os.path.join(current_app.static_folder, 'thumbnails', 'instrument_layouts', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f"Deleted thumbnail: {filename}")
        except Exception as e:
            logging.error(f"Error deleting thumbnail {filename}: {e}")


def calculate_logbook_totals(user_id):
    """Calculate logbook totals including initial times and filtering by effective date."""
    # Get initial logbook time if it exists
    initial_time = InitialLogbookTime.query.filter_by(user_id=user_id).first()
    
    # Get pilot mappings for this user to include mapped pilot flights
    from src.models import Pilot
    user_pilot_mappings = Pilot.query.filter_by(user_id=user_id, is_active=True).all()
    user_pilot_names = [mapping.pilot_name for mapping in user_pilot_mappings]
    
    # Build base query for logbook entries
    if user_pilot_names:
        base_filter = db.or_(
            LogbookEntry.user_id == user_id,
            LogbookEntry.pilot_name.in_(user_pilot_names)
        )
    else:
        base_filter = LogbookEntry.user_id == user_id
    
    # Calculate sums from logbook entries
    if initial_time:
        # Only count entries after the effective date
        entry_totals = {
            'total_time': db.session.query(db.func.sum(LogbookEntry.flight_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'pic_time': db.session.query(db.func.sum(LogbookEntry.pilot_in_command_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'dual_time': db.session.query(db.func.sum(LogbookEntry.dual_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'instrument_time': db.session.query(db.func.sum(LogbookEntry.instrument_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'night_time': db.session.query(db.func.sum(LogbookEntry.night_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'cross_country_time': db.session.query(db.func.sum(LogbookEntry.cross_country_time)).filter(
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).scalar() or 0,
            'total_landings': (
                db.session.query(
                    db.func.sum(LogbookEntry.landings_day + LogbookEntry.landings_night)
                ).filter(
                    base_filter,
                    db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
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
                base_filter,
                db.func.date(LogbookEntry.takeoff_datetime) >= initial_time.effective_date
            ).count()
        }
    else:
        # No initial time, just sum all entries
        totals = {
            'total_time': db.session.query(db.func.sum(LogbookEntry.flight_time)).filter(base_filter).scalar() or 0,
            'pic_time': db.session.query(db.func.sum(LogbookEntry.pilot_in_command_time)).filter(base_filter).scalar() or 0,
            'dual_time': db.session.query(db.func.sum(LogbookEntry.dual_time)).filter(base_filter).scalar() or 0,
            'instrument_time': db.session.query(db.func.sum(LogbookEntry.instrument_time)).filter(base_filter).scalar() or 0,
            'night_time': db.session.query(db.func.sum(LogbookEntry.night_time)).filter(base_filter).scalar() or 0,
            'cross_country_time': db.session.query(db.func.sum(LogbookEntry.cross_country_time)).filter(base_filter).scalar() or 0,
            'total_landings': (
                db.session.query(
                    db.func.sum(LogbookEntry.landings_day + LogbookEntry.landings_night)
                ).filter(base_filter).scalar() or 0
            ),
            'has_initial_time': False,
            'initial_time': None,
            'entries_count': LogbookEntry.query.filter(base_filter).count()
        }
    
    return totals


@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page."""
    # Get some statistics for the dashboard
    device_count = Device.query.filter_by(user_id=current_user.id, is_active=True).count()
    checklist_count = Checklist.query.filter_by(user_id=current_user.id, is_active=True).count()
    instrument_layout_count = InstrumentLayout.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    # Get pilot mappings for current user to find their pilot names
    from src.models import Pilot
    user_pilot_mappings = Pilot.query.filter_by(user_id=current_user.id, is_active=True).all()
    user_pilot_names = [mapping.pilot_name for mapping in user_pilot_mappings]
    
    # Build query for logbook entries (including pilot mappings)
    if user_pilot_names:
        logbook_filter = db.or_(
            LogbookEntry.user_id == current_user.id,
            LogbookEntry.pilot_name.in_(user_pilot_names)
        )
    else:
        logbook_filter = LogbookEntry.user_id == current_user.id
    
    logbook_count = LogbookEntry.query.filter(logbook_filter).count()
    
    # Get pilot mapping count (aircraft the user has access to)
    pilot_mapping_count = Pilot.query.filter_by(user_id=current_user.id, is_active=True)\
        .join(Device).filter(Device.is_active == True).count()
    
    # Get recent logbook entries (including pilot mappings)
    recent_entries = LogbookEntry.query.filter(logbook_filter)\
        .order_by(LogbookEntry.takeoff_datetime.desc()).limit(5).all()
    
    # Calculate total flight time using new function
    totals = calculate_logbook_totals(current_user.id)
    total_flight_time = totals['total_time']
    
    return render_template('dashboard/index.html', 
                         title='Dashboard',
                         device_count=device_count,
                         checklist_count=checklist_count,
                         instrument_layout_count=instrument_layout_count,
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
    """View all logbook entries linked to a specific device (for device owner and pilots)."""
    # First check if user owns the device
    device = Device.query.filter_by(id=device_id, user_id=current_user.id, is_active=True).first()
    
    # If not the owner, check if user is mapped as a pilot for this device
    if not device:
        from src.models import Pilot
        pilot_mapping = Pilot.query.filter_by(
            user_id=current_user.id, 
            device_id=device_id, 
            is_active=True
        ).first()
        
        if pilot_mapping:
            device = Device.query.filter_by(id=device_id, is_active=True).first()
        
        if not device:
            # User has no access to this device
            flash('You do not have access to view this device logbook.', 'error')
            return redirect(url_for('dashboard.devices'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get ALL logbook entries linked to this device (regardless of user_id)
    # This includes entries from device events (user_id=None) and pilot mappings
    entries = LogbookEntry.query.filter_by(device_id=device_id)\
        .order_by(LogbookEntry.takeoff_datetime.desc(), LogbookEntry.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate totals for this device from ALL entries
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
        else:
            unique_pilots.add('Unknown Pilot')  # For event-generated entries without pilot info
    
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


@dashboard_bp.route('/api/device/<int:device_id>/sync-telemetry', methods=['POST'])
@login_required
def api_sync_device_telemetry(device_id):
    """Manually sync telemetry data for a specific device."""
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    if not device.external_device_id:
        return jsonify({
            'success': False,
            'error': 'Device has no external device ID configured for telemetry sync'
        }), 400
    
    try:
        # Initialize ThingsBoard service
        tb_service = ThingsBoardSyncService()
        
        # Sync telemetry for this device
        success = tb_service._sync_device_telemetry(device)
        
        if success:
            # Return updated telemetry data
            return jsonify({
                'success': True,
                'message': 'Telemetry synced successfully',
                'telemetry': {
                    'status': device.status,
                    'status_description': device.status_description,
                    'fuel_quantity': device.fuel_quantity,
                    'altitude': device.altitude,
                    'latitude': device.latitude,
                    'longitude': device.longitude,
                    'speed': device.speed,
                    'location_description': device.location_description,
                    'last_update': device.last_telemetry_update.isoformat() if device.last_telemetry_update else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to sync telemetry data from ThingsBoard'
            }), 500
            
    except Exception as e:
        logging.error(f"Error syncing telemetry for device {device.name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error syncing telemetry: {str(e)}'
        }), 500


# Checklist routes


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
    form = ChecklistCreateForm()
    if form.validate_on_submit():
        # Default checklist template
        default_template = {
            "Language": "en-us",
            "Voice": "Linda",
            "Root": {
                "Type": 0,
                "Name": "Root",
                "Children": [
                    {
                        "Type": 0,
                        "Name": "Pre-flight",
                        "Children": []
                    },
                    {
                        "Type": 0,
                        "Name": "In-flight",
                        "Children": []
                    },
                    {
                        "Type": 0,
                        "Name": "Post-flight",
                        "Children": []
                    },
                    {
                        "Type": 0,
                        "Name": "Emergency",
                        "Children": []
                    },
                    {
                        "Type": 0,
                        "Name": "Reference",
                        "Children": []
                    }
                ]
            }
        }
        
        checklist = Checklist(
            title=form.title.data,
            description="",
            items=json.dumps([]),  # Empty items for now
            json_content=json.dumps(default_template),
            user_id=current_user.id
        )
        db.session.add(checklist)
        db.session.commit()
        flash('Checklist created successfully!', 'success')
        return redirect(url_for('dashboard.checklists'))
    
    return render_template('dashboard/add_checklist_simple.html', title='Add Checklist', form=form)


@dashboard_bp.route('/checklists/import', methods=['GET', 'POST'])
@login_required
def import_checklist():
    """Import checklist from .ckl file."""
    form = ChecklistImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        try:
            # Read file content directly
            file_content = file.read().decode('utf-8')
            
            # Extract filename without extension for title
            filename = file.filename
            if filename.lower().endswith('.ckl'):
                title = filename[:-4]  # Remove .ckl extension
            else:
                title = filename
            
            # Create checklist with file content directly in json_content
            checklist = Checklist(
                title=title,
                description=f"Imported from {filename}",
                items=json.dumps([]),  # Keep empty as we use json_content
                json_content=file_content,  # Load content directly
                user_id=current_user.id
            )
            
            db.session.add(checklist)
            db.session.commit()
            
            flash(f'Checklist "{title}" imported successfully from {filename}!', 'success')
            return redirect(url_for('dashboard.checklists'))
            
        except UnicodeDecodeError:
            flash('Could not read the file. Please ensure it is a text-based file with UTF-8 encoding.', 'danger')
        except Exception as e:
            flash(f'Error importing checklist: {str(e)}', 'danger')
            logging.error(f"Error importing checklist: {e}")
    
    return render_template('dashboard/import_checklist.html', title='Import Checklist', form=form)


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


@dashboard_bp.route('/checklists/<int:checklist_id>/export')
@login_required
def export_checklist(checklist_id):
    """Export checklist json_content as downloadable file."""
    from flask import Response
    import re
  
    checklist = Checklist.query.filter_by(id=checklist_id, user_id=current_user.id).first_or_404()
    
    # Clean the filename - remove special characters and spaces
    safe_filename = re.sub(r'[^\w\s-]', '', checklist.title)
    safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
    filename = f"checklist_{safe_filename}.ckl"
    
    # Create response with JSON content
    response = Response(
        checklist.json_content,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/json; charset=utf-8'
        }
    )
    
    return response

@dashboard_bp.route('/api/checklist/<int:checklist_id>/load_json')
@login_required
def load_checklist(checklist_id):
    """Load checklist json_content for editing."""
    checklist = Checklist.query.filter_by(id=checklist_id, user_id=current_user.id).first_or_404()
    
    # Parse the JSON content from the database and return as object
    # try:
    #     json_data = json.loads(checklist.json_content) if checklist.json_content else {}
    # except (json.JSONDecodeError, TypeError):
    #     # If parsing fails, return empty default structure
    #     json_data = {
    #         "Language": "en-us",
    #         "Voice": "Linda",
    #         "Root": {
    #             "Type": 0,
    #             "Name": "Root",
    #             "Children": []
    #         }
    #     }

    reply = { 
        "data": checklist.json_content,
        "title": checklist.title
    }

    return reply


@dashboard_bp.route('/instrument-layouts')
@login_required
def instrument_layouts():
    """Instrument layout management page."""
    layouts = InstrumentLayout.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('dashboard/instrument_layouts.html', title='Instrument Layouts', layouts=layouts)


@dashboard_bp.route('/instrument-layouts/add', methods=['GET', 'POST'])
@login_required
def add_instrument_layout():
    """Add new instrument layout."""
    form = InstrumentLayoutCreateForm()
    if form.validate_on_submit():
        # Default instrument layout template
        default_template = {
            "panel": []
        }
        import dicttoxml

        # Convert default_template to XML with attributes using dicttoxml
        # To add attributes, use a structure like {'@attr': value, ...} for attributes in dicttoxml
        # Example: {'panel': [], '@version': '1.0'} will add version="1.0" to the root

        # Add attributes to the root element
        xml_template = {
            # '@instrument': 'Digi',
            # '@model': 'I',
            'panel': [],
            'engine-type': "Generic Engine"
        }
        xml_content = dicttoxml.dicttoxml(
            xml_template,
            custom_root='indu',
            attr_type=False
        ).decode('utf-8')

        xml_content = xml_content.replace('<indu>', '<indu instrument="Digi" model="I">', 1)
        # import xml.dom.minidom
        # Pretty-print the XML for logging/debugging
        # pretty_xml = xml.dom.minidom.parseString(xml_content).toprettyxml(indent="  ")
        # logging.debug("Instrument layout XML:\n%s", pretty_xml)

        layout = InstrumentLayout(
            title=form.title.data,
            description="",
            instrument_type=form.instrument_type.data,
            layout_data=json.dumps([]),  # Empty data for now
            xml_content=xml_content,
            user_id=current_user.id
        )
        db.session.add(layout)
        db.session.commit()
        flash('Instrument layout created successfully!', 'success')
        return redirect(url_for('dashboard.instrument_layouts'))
    
    return render_template('dashboard/add_instrument_layout_simple.html', title='Add Instrument Layout', form=form)


@dashboard_bp.route('/instrument-layouts/import', methods=['GET', 'POST'])
@login_required
def import_instrument_layout():
    """Import instrument layout from file."""
    form = InstrumentLayoutImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        try:
            # Read file content
            file_content = file.read().decode('utf-8')
            
            # Extract filename without extension for title
            filename = file.filename
            title = filename
            for ext in ['.xml', '.iml']:
                if filename.lower().endswith(ext):
                    title = filename[:-len(ext)]
                    break
            
            # Determine instrument type from filename or content
            instrument_type = 'digi'  # Default
            filename_lower = filename.lower()
            if 'indu' in filename_lower:
                if '57' in filename_lower:
                    instrument_type = 'indu_57mm'
                elif '80' in filename_lower:
                    instrument_type = 'indu_80mm'
                else:
                    instrument_type = 'indu_57mm'
            elif 'altimeter' in filename_lower:
                instrument_type = 'altimeter_80mm'
            
            # Create instrument layout with file content
            layout = InstrumentLayout(
                title=title,
                description=f"Imported from {filename}",
                instrument_type=instrument_type,
                layout_data=json.dumps({}),  # Keep empty as we use xml_content
                xml_content=file_content,  # Load content directly
                user_id=current_user.id
            )
            
            db.session.add(layout)
            db.session.commit()
            
            flash(f'Instrument layout "{title}" imported successfully from {filename}!', 'success')
            return redirect(url_for('dashboard.instrument_layouts'))
            
        except UnicodeDecodeError:
            flash('Could not read the file. Please ensure it is a text-based file with UTF-8 encoding.', 'danger')
        except Exception as e:
            flash(f'Error importing instrument layout: {str(e)}', 'danger')
            logging.error(f"Error importing instrument layout: {e}")
    
    return render_template('dashboard/import_instrument_layout.html', title='Import Instrument Layout', form=form)


@dashboard_bp.route('/instrument-layouts/<int:layout_id>')
@login_required
def view_instrument_layout(layout_id):
    """View instrument layout details."""
    layout = InstrumentLayout.query.filter_by(id=layout_id, user_id=current_user.id).first_or_404()
    return render_template('dashboard/view_instrument_layout.html', 
                         title=layout.title, 
                         layout=layout)


@dashboard_bp.route('/instrument-layouts/<int:layout_id>/export')
@login_required
def export_instrument_layout(layout_id):
    """Export instrument layout xml_content as downloadable file."""
    from flask import Response
    import re
    
    layout = InstrumentLayout.query.filter_by(id=layout_id, user_id=current_user.id).first_or_404()
    
    # Clean the filename - remove special characters and spaces
    safe_filename = re.sub(r'[^\w\s-]', '', layout.title)
    safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
    filename = f"instrument_layout_{safe_filename}.xml"
    
    # Create response with XML content
    response = Response(
        layout.xml_content,
        mimetype='application/xml',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/xml; charset=utf-8'
        }
    )
    
    return response


@dashboard_bp.route('/instrument-layouts/<int:layout_id>/load_json')
@dashboard_bp.route('/api/instrument-layout/<int:layout_id>/load_json')
@login_required
def load_instrument_layout(layout_id):
    """Load instrument layout xml_content for editing."""
    layout = InstrumentLayout.query.filter_by(id=layout_id, user_id=current_user.id).first_or_404()

    reply = { 
        "content": layout.xml_content,
        "title": layout.title
    }

    return reply


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
    
    # Get entries where user is directly assigned OR where user is mapped as pilot
    from src.models import Pilot
    
    # Get pilot mappings for current user to find their pilot names
    user_pilot_mappings = Pilot.query.filter_by(user_id=current_user.id, is_active=True).all()
    user_pilot_names = [mapping.pilot_name for mapping in user_pilot_mappings]
    
    # Build query for entries
    query = LogbookEntry.query
    
    if user_pilot_names:
        # Include entries directly assigned to user OR entries with user's pilot name
        query = query.filter(
            db.or_(
                LogbookEntry.user_id == current_user.id,
                LogbookEntry.pilot_name.in_(user_pilot_names)
            )
        )
    else:
        # No pilot mappings, just show directly assigned entries
        query = query.filter_by(user_id=current_user.id)
    
    entries = query.order_by(LogbookEntry.takeoff_datetime.desc())\
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
        # Calculate flight time if not provided
        flight_time = form.flight_time.data
        if not flight_time and form.takeoff_datetime.data and form.landing_datetime.data:
            duration = form.landing_datetime.data - form.takeoff_datetime.data
            flight_time = round(duration.total_seconds() / 3600, 2)
        
        entry = LogbookEntry(
            takeoff_datetime=form.takeoff_datetime.data,
            landing_datetime=form.landing_datetime.data,
            aircraft_type=form.aircraft_type.data,
            aircraft_registration=form.aircraft_registration.data,
            departure_airport=form.departure_airport.data,
            arrival_airport=form.arrival_airport.data,
            flight_time=flight_time or 0,
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
        ).order_by(LogbookEntry.takeoff_datetime.desc()).limit(5).all()
    
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
        'description': checklist.description,
        'data': data
    })


@dashboard_bp.route('/api/checklist/<int:checklist_id>', methods=['PUT'])
@login_required
def api_update_checklist(checklist_id):
    import logging
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
    # if 'data' in request_data:
        # checklist.items = json.dumps(request_data['data'])
    # Handle json_content updates (for checklist editor)
    if 'json_content' in request_data:
        logging.info(f"Updating checklist {checklist_id} with new json_content")
        checklist.json_content = request_data['json_content']
    # If data is provided without explicit json_content, also update json_content
    elif 'data' in request_data:
        checklist.json_content = request_data['data']
    
    checklist.updated_at = db.func.now()
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


@dashboard_bp.route('/api/checklist/<int:checklist_id>/rename', methods=['POST'])
@login_required
def api_rename_checklist(checklist_id):
    """Rename a checklist."""
    checklist = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    new_title = request_data.get('title', '').strip()
    
    if not new_title:
        return jsonify({
            'success': False,
            'message': 'Title cannot be empty'
        }), 400
    
    if len(new_title) > 200:
        return jsonify({
            'success': False,
            'message': 'Title cannot exceed 200 characters'
        }), 400
    
    checklist.title = new_title
    checklist.updated_at = db.func.now()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Checklist renamed successfully',
        'new_title': new_title
    })


@dashboard_bp.route('/api/available-devices', methods=['GET'])
@login_required
def api_get_available_devices():
    """Get devices that the user can send checklists to."""
    devices = []
    
    # Get user's own devices
    user_devices = Device.query.filter_by(user_id=current_user.id, is_active=True).all()
    for device in user_devices:
        devices.append({
            'id': device.id,
            'name': device.name,
            'type': device.device_type.title(),
            'registration': device.registration,
            'ownership': '(Your Device)'
        })
    
    # Get devices where user is mapped as pilot
    pilot_mappings = Pilot.query.filter_by(user_id=current_user.id, is_active=True).all()
    for pilot in pilot_mappings:
        # Avoid duplicates (user's own devices)
        if pilot.device.user_id != current_user.id and pilot.device.is_active:
            devices.append({
                'id': pilot.device.id,
                'name': pilot.device.name,
                'type': pilot.device.device_type.title(),
                'registration': pilot.device.registration,
                'ownership': f'(As pilot: {pilot.pilot_name})'
            })
    
    return jsonify({
        'success': True,
        'devices': devices
    })


@dashboard_bp.route('/api/checklist/<int:checklist_id>/send', methods=['POST'])
@login_required
def api_send_checklist(checklist_id):
    """Send checklist to a device."""
    checklist = Checklist.query.filter_by(
        id=checklist_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    device_id = request_data.get('device_id')
    
    if not device_id:
        return jsonify({
            'success': False,
            'message': 'Device ID is required'
        }), 400
    
    # Check if user has access to this device
    device = None
    
    # Check if it's user's own device
    user_device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    if user_device:
        device = user_device
    else:
        # Check if user is mapped as pilot on this device
        pilot_mapping = Pilot.query.filter_by(
            user_id=current_user.id,
            device_id=device_id,
            is_active=True
        ).first()
        
        if pilot_mapping and pilot_mapping.device.is_active:
            device = pilot_mapping.device
    
    if not device:
        return jsonify({
            'success': False,
            'message': 'You do not have access to this device'
        }), 403
    
    try:
        # Initialize ThingsBoard service
        tb_service = ThingsBoardSyncService()
        
        # Prepare checklist data for sending
        checklist_data = {
            'id': checklist.id,
            'title': checklist.title,
            'description': checklist.description or '',
            'json_content': checklist.json_content or '',
            'created_at': checklist.created_at.isoformat() if checklist.created_at else None,
            'updated_at': checklist.updated_at.isoformat() if checklist.updated_at else None
        }
        
        # Send checklist via ThingsBoard RPC v2 API
        success = tb_service.send_checklist_to_device(device.external_device_id, checklist_data)
        
        if success:
            logging.info(f"Checklist '{checklist.title}' (ID: {checklist.id}) sent to device '{device.name}' (ID: {device.id}) via ThingsBoard RPC by user {current_user.email}")
            
            return jsonify({
                'success': True,
                'message': f'Checklist "{checklist.title}" sent to {device.name} successfully!'
            })
        else:
            logging.error(f"Failed to send checklist '{checklist.title}' to device '{device.name}' via ThingsBoard RPC")
            return jsonify({
                'success': False,
                'message': f'Failed to send checklist to {device.name}. Device may be offline or unreachable.'
            }), 500
        
    except Exception as e:
        logging.error(f"Error sending checklist {checklist_id} to device {device_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to send checklist'
        }), 500


# API Endpoints for Instrument Layout Editor Integration

@dashboard_bp.route('/api/instrument-layout/<int:layout_id>', methods=['GET'])
@login_required
def api_get_instrument_layout(layout_id):
    """Get instrument layout data for the editor."""
    layout = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Parse layout data if it's stored as JSON
    try:
        data = json.loads(layout.layout_data) if layout.layout_data else {}
    except (json.JSONDecodeError, TypeError):
        data = {}
    
    return jsonify({
        'id': layout.id,
        'title': layout.title,
        'description': layout.description,
        'data': data
    })


@dashboard_bp.route('/api/instrument-layout/<int:layout_id>', methods=['PUT'])
@login_required
def api_update_instrument_layout(layout_id):
    """Update instrument layout data from the editor."""
    layout = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    
    # Update layout fields
    if 'title' in request_data:
        layout.title = request_data['title']
    if 'description' in request_data:
        layout.description = request_data['description']
    if 'data' in request_data:
        layout.layout_data = json.dumps(request_data['data'])
    # Handle xml_content updates (for instrument layout editor)
    if 'xml_content' in request_data:
        layout.xml_content = request_data['xml_content']
    # If data is provided without explicit xml_content, also update xml_content
    elif 'data' in request_data:
        layout.xml_content = request_data['data']
    
    # Handle thumbnail generation if provided
    if 'thumbnail' in request_data and request_data['thumbnail']:
        # Process thumbnail data for database storage
        processed_base64 = process_thumbnail_base64(request_data['thumbnail'])
        
        if processed_base64:
            # Delete old thumbnail file if it exists (backward compatibility)
            if layout.thumbnail_filename:
                delete_thumbnail(layout.thumbnail_filename)
                layout.thumbnail_filename = None
            
            # Store base64 in database
            layout.thumbnail_base64 = processed_base64
            logging.info(f"Updated thumbnail base64 for layout {layout_id}")
        else:
            logging.warning(f"Failed to process thumbnail for layout {layout_id}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Instrument layout updated successfully'
    })


@dashboard_bp.route('/api/instrument-layout/<int:layout_id>/duplicate', methods=['POST'])
@login_required
def api_duplicate_instrument_layout(layout_id):
    """Duplicate an instrument layout."""
    original = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Create a copy
    duplicate = InstrumentLayout(
        title=f"{original.title} (Copy)",
        instrument_type=original.instrument_type,
        description=original.description,
        layout_data=original.layout_data,
        xml_content=original.xml_content,
        user_id=current_user.id
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Instrument layout duplicated successfully',
        'new_id': duplicate.id
    })


@dashboard_bp.route('/api/instrument-layout/<int:layout_id>', methods=['DELETE'])
@login_required
def api_delete_instrument_layout(layout_id):
    """Delete an instrument layout (soft delete)."""
    layout = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    # Delete thumbnail file if it exists (backward compatibility)
    if layout.thumbnail_filename:
        delete_thumbnail(layout.thumbnail_filename)
        layout.thumbnail_filename = None
    
    # Clear base64 thumbnail data
    layout.thumbnail_base64 = None
    
    # Soft delete by setting is_active to False
    layout.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Instrument layout deleted successfully'
    })


@dashboard_bp.route('/api/instrument-layout/<int:layout_id>/rename', methods=['POST'])
@login_required
def api_rename_instrument_layout(layout_id):
    """Rename an instrument layout."""
    layout = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    new_title = request_data.get('title', '').strip()
    
    if not new_title:
        return jsonify({
            'success': False,
            'message': 'Title cannot be empty'
        }), 400
    
    if len(new_title) > 200:
        return jsonify({
            'success': False,
            'message': 'Title cannot exceed 200 characters'
        }), 400
    
    layout.title = new_title
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Instrument layout renamed successfully',
        'new_title': new_title
    })


@dashboard_bp.route('/api/instrument-layout/<int:layout_id>/thumbnail', methods=['PUT'])
@login_required
def api_update_instrument_layout_thumbnail(layout_id):
    """Update instrument layout thumbnail from editor export."""
    layout = InstrumentLayout.query.filter_by(
        id=layout_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    request_data = request.get_json()
    thumbnail_data = request_data.get('thumbnail')
    
    if not thumbnail_data:
        return jsonify({
            'success': False,
            'message': 'No thumbnail data provided'
        }), 400
    
    try:
        # Process thumbnail data for database storage
        processed_base64 = process_thumbnail_base64(thumbnail_data)
        
        if processed_base64:
            # Delete old thumbnail file if it exists (backward compatibility)
            if layout.thumbnail_filename:
                delete_thumbnail(layout.thumbnail_filename)
                layout.thumbnail_filename = None
            
            # Store base64 in database
            layout.thumbnail_base64 = processed_base64
            db.session.commit()
            
            logging.info(f"Updated thumbnail base64 for layout {layout_id}")
            return jsonify({
                'success': True,
                'message': 'Thumbnail updated successfully',
                'has_thumbnail': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to process thumbnail data'
            }), 500
            
    except Exception as e:
        logging.error(f"Error updating thumbnail for layout {layout_id}: {e}")
        return jsonify({
            'success': False,
            'message': 'Error updating thumbnail'
        }), 500


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


@dashboard_bp.route('/devices/<int:device_id>/pilots')
@login_required
def device_pilots(device_id):
    """Manage pilot mappings for a device (device owners only)."""
    # Verify device ownership
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Get pilot mappings for this device
    query = Pilot.query.filter_by(device_id=device_id, is_active=True)
    
    # Apply search filter
    if search:
        from src.models import User
        query = query.join(User).filter(
            db.or_(
                Pilot.pilot_name.contains(search),
                User.email.contains(search),
                User.nickname.contains(search)
            )
        )
    
    pilot_mappings = query.order_by(Pilot.pilot_name.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get unmapped pilots from logbook entries for this device
    unmapped_pilots = db.session.query(LogbookEntry.pilot_name.distinct().label('pilot_name'))\
        .filter(LogbookEntry.device_id == device_id)\
        .filter(LogbookEntry.pilot_name.isnot(None))\
        .filter(~LogbookEntry.pilot_name.in_(
            db.session.query(Pilot.pilot_name).filter_by(device_id=device_id)
        )).all()
    
    # Create form for new mappings
    form = DevicePilotMappingForm()
    
    return render_template('dashboard/device_pilots.html',
                         title=f'Pilot Mappings - {device.name}',
                         device=device,
                         pilot_mappings=pilot_mappings,
                         unmapped_pilots=[p.pilot_name for p in unmapped_pilots],
                         form=form,
                         search=search)


@dashboard_bp.route('/devices/<int:device_id>/pilots/create', methods=['POST'])
@login_required
def create_device_pilot_mapping(device_id):
    """Create a pilot mapping for a device (device owners only)."""
    # Verify device ownership
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    form = DevicePilotMappingForm()
    
    if form.validate_on_submit():
        pilot_name = form.pilot_name.data.strip()
        user_email = form.user_email.data.strip().lower()
        
        # Find user by email
        from src.models import User
        user = User.query.filter_by(email=user_email, is_active=True).first()
        if not user:
            flash(f'No active user found with email: {user_email}', 'error')
            return redirect(url_for('dashboard.device_pilots', device_id=device_id))
        
        # Check if mapping already exists
        existing = Pilot.query.filter_by(
            pilot_name=pilot_name,
            device_id=device_id
        ).first()
        
        if existing:
            if existing.is_active:
                flash(f'Pilot mapping already exists: "{pilot_name}" is mapped to {existing.user.email}', 'error')
            else:
                # Reactivate existing mapping with new user
                existing.user_id = user.id
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                flash(f'Reactivated pilot mapping: "{pilot_name}" -> {user.email}', 'success')
            return redirect(url_for('dashboard.device_pilots', device_id=device_id))
        
        try:
            # Create new pilot mapping
            pilot_mapping = Pilot(
                pilot_name=pilot_name,
                user_id=user.id,
                device_id=device_id
            )
            db.session.add(pilot_mapping)
            db.session.commit()
            
            current_app.logger.info(f"Device owner {current_user.nickname} created pilot mapping: "
                                   f"{pilot_name} -> {user.email} on {device.name}")
            
            flash(f'Successfully created pilot mapping: "{pilot_name}" -> {user.email}', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating pilot mapping: {str(e)}")
            flash('Error creating pilot mapping. Please try again.', 'error')
    else:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{form[field].label.text}: {error}', 'error')
    
    return redirect(url_for('dashboard.device_pilots', device_id=device_id))


@dashboard_bp.route('/devices/<int:device_id>/pilots/<int:pilot_id>/delete', methods=['POST'])
@login_required
def delete_device_pilot_mapping(device_id, pilot_id):
    """Delete a pilot mapping for a device (device owners only)."""
    # Verify device ownership
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    pilot = Pilot.query.filter_by(id=pilot_id, device_id=device_id).first_or_404()
    
    try:
        pilot_info = f"{pilot.pilot_name} -> {pilot.user.email}"
        db.session.delete(pilot)
        db.session.commit()
        
        current_app.logger.info(f"Device owner {current_user.nickname} deleted pilot mapping: {pilot_info} on {device.name}")
        flash(f'Successfully deleted pilot mapping: {pilot_info}', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pilot mapping: {str(e)}")
        flash('Error deleting pilot mapping. Please try again.', 'error')
    
    return redirect(url_for('dashboard.device_pilots', device_id=device_id))


@dashboard_bp.route('/api/devices/<int:device_id>/pilots/suggestions')
@login_required
def device_pilot_suggestions(device_id):
    """Get pilot name suggestions for a specific device (device owners only)."""
    # Verify device ownership
    device = Device.query.filter_by(
        id=device_id, 
        user_id=current_user.id, 
        is_active=True
    ).first_or_404()
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Get pilot names from logbook entries for this device that match the query
    pilot_names = db.session.query(LogbookEntry.pilot_name.distinct().label('pilot_name'))\
        .filter(LogbookEntry.device_id == device_id)\
        .filter(LogbookEntry.pilot_name.isnot(None))\
        .filter(LogbookEntry.pilot_name.contains(query))\
        .limit(10).all()
    
    return jsonify([p.pilot_name for p in pilot_names])


@dashboard_bp.route('/thumbnails/instrument_layouts/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images for instrument layouts."""
    from flask import send_from_directory
    thumbnails_dir = os.path.join(current_app.static_folder, 'thumbnails', 'instrument_layouts')
    return send_from_directory(thumbnails_dir, filename)
