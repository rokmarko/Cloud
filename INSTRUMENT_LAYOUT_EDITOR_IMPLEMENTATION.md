# Instrument Layout Editor Implementation

## Summary
Added a complete Instrument Layout Editor using the same structure as the checklist editor, including iframe-based editor, database model, API routes, and UI components.

## Database Changes

### 1. New InstrumentLayout Model (`src/models.py`)

```python
class InstrumentLayout(db.Model):
    """Instrument layout model for cockpit instrument configurations."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # primary, secondary, backup, custom
    layout_data = db.Column(db.Text, nullable=False)  # JSON string of layout configuration
    json_content = db.Column(db.Text, nullable=False)  # Full JSON content of the layout
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<InstrumentLayout {self.title}>'
```

### 2. User Model Relationship
- Added `instrument_layouts` relationship to User model
- Supports cascade delete when user is removed

## Forms (`src/forms/__init__.py`)

### 1. InstrumentLayoutForm
- Full form with title, description, category selection
- Categories: primary, secondary, backup, custom, other

### 2. InstrumentLayoutCreateForm  
- Simplified creation form (title only)
- Similar to ChecklistCreateForm pattern

## Backend Routes (`src/routes/dashboard.py`)

### 1. Main Routes
- `GET /dashboard/instrument-layouts` - List all layouts
- `GET /dashboard/instrument-layouts/add` - Create new layout form
- `GET /dashboard/instrument-layouts/<id>` - View layout details
- `GET /dashboard/instrument-layouts/<id>/export` - Download layout JSON
- `GET /dashboard/instrument-layouts/<id>/load_json` - Load layout for editor

### 2. API Routes
- `GET /api/instrument-layout/<id>` - Get layout data
- `PUT /api/instrument-layout/<id>` - Update layout data
- `POST /api/instrument-layout/<id>/duplicate` - Duplicate layout
- `DELETE /api/instrument-layout/<id>` - Delete layout (soft delete)
- `GET /api/instrument-layout/<id>/load_json` - Alternative load endpoint

### 3. Default Template Structure
```json
{
  "layout_type": "instrument_panel",
  "version": "1.0",
  "instruments": [],
  "layout": {
    "width": 1024,
    "height": 768,
    "background_color": "#000000",
    "grid_enabled": true,
    "grid_size": 10
  },
  "settings": {
    "units": "metric",
    "theme": "dark"
  }
}
```

## Frontend Templates

### 1. Main Layout Page (`templates/dashboard/instrument_layouts.html`)
- Grid layout displaying all instrument layouts
- Edit, Export, Duplicate, Delete actions per layout
- Modal-based iframe editor integration
- JavaScript functions for editor communication

### 2. Create Layout Page (`templates/dashboard/add_instrument_layout_simple.html`)
- Simple form for creating new layouts
- Minimal UI focused on title input
- Redirects to layouts list after creation

### 3. Dashboard Integration (`templates/dashboard/index.html`)
- Added instrument layouts stats card
- Shows count of active layouts
- Links to instrument layouts page

## JavaScript Functionality

### 1. Editor Integration
- `openInstrumentLayoutEditor(id, title)` - Opens modal with iframe
- `loadInstrumentLayoutData()` - Loads layout data into editor
- `saveInstrumentLayout()` - Manual save functionality
- `saveInstrumentLayoutData(data)` - Autosave functionality

### 2. Message Handling
- Listens for `init` and `autosave` events from iframe
- Sends `load` and `getData` messages to iframe
- Handles editor communication via postMessage API

### 3. CRUD Operations
- `duplicateInstrumentLayout(id)` - Duplicate existing layout
- `deleteInstrumentLayout(id)` - Delete layout with confirmation
- CSRF token handling for all requests

## Migration Requirements

### 1. Database Table Creation
```sql
CREATE TABLE instrument_layout (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    layout_data TEXT NOT NULL,
    json_content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);
```

### 2. Migration Script
- Created `migrate_instrument_layout.py` for table creation
- Requires app restart to apply changes
- Run: `python migrate_instrument_layout.py`

## Features

### 1. Complete CRUD Operations
- ✅ Create new instrument layouts
- ✅ Read/view existing layouts  
- ✅ Update layouts via editor
- ✅ Delete layouts (soft delete)

### 2. Editor Integration
- ✅ Iframe-based editor at `https://www.kanardia.eu/apps/instrument-layout`
- ✅ Load existing layout data into editor
- ✅ Save changes back to database
- ✅ Autosave functionality

### 3. Data Management
- ✅ JSON-based layout storage
- ✅ Export layouts as downloadable files
- ✅ Duplicate existing layouts
- ✅ Category-based organization

### 4. User Experience
- ✅ Dashboard integration with stats
- ✅ Responsive card-based layout
- ✅ Loading indicators during editor startup
- ✅ Error handling and user feedback

## File Structure

```
src/
├── models.py (+ InstrumentLayout model)
├── forms/__init__.py (+ InstrumentLayoutForm, InstrumentLayoutCreateForm)
└── routes/dashboard.py (+ instrument layout routes)

templates/dashboard/
├── instrument_layouts.html (main layouts page)
├── add_instrument_layout_simple.html (create form)
└── index.html (+ instrument layouts card)

migration/
└── migrate_instrument_layout.py (table creation)
```

## Usage Flow

1. **Access**: Navigate to Dashboard → Instrument Layouts card
2. **Create**: Click "Create Layout" → Enter title → Save
3. **Edit**: Click "Edit" button → Opens iframe editor → Make changes → Auto-saves
4. **Export**: Click "Export" button → Downloads JSON file
5. **Manage**: Use dropdown menu for duplicate/delete operations

## Technical Notes

### 1. Editor Communication
- Uses postMessage for iframe communication
- Supports both manual save and autosave
- Handles loading indicators and error states

### 2. Data Storage
- `layout_data`: Legacy field for basic JSON data
- `json_content`: Full layout structure for editor
- Both fields updated when saving from editor

### 3. Security
- CSRF token protection on all API calls
- User ownership validation on all operations
- Soft delete preserves data integrity

### 4. Performance
- Deferred iframe loading (no src until modal opens)
- Efficient database queries with user filtering
- Proper cleanup when modal closes

## Testing

To test the implementation:

1. **Setup**: Run migration script to create tables
2. **Access**: Navigate to `/dashboard/instrument-layouts`
3. **Create**: Add a new instrument layout
4. **Edit**: Open editor and verify data loading/saving
5. **Export**: Test download functionality
6. **CRUD**: Test duplicate and delete operations

## Future Enhancements

1. **Layout Templates**: Pre-defined instrument configurations
2. **Import Functionality**: Upload existing layout files
3. **Version Control**: Track layout changes over time
4. **Sharing**: Share layouts between users
5. **Validation**: Layout format validation
6. **Preview**: Thumbnail previews of layouts
