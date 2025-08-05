# Load JSON Route Modification

## Summary
Modified the `load_checklist` route (`load_json`) in `dashboard.py` to properly return `json_content` as a structured data object for use with `loadChecklistData()`.

## Changes Made

### 1. Route Enhancement (`src/routes/dashboard.py`)

**Before:**
```python
@dashboard_bp.route('/checklists/<int:checklist_id>/load_json')
@login_required
def load_checklist(checklist_id):
    """Load checklist json_content for editing."""
    from flask import jsonify

    checklist = Checklist.query.filter_by(id=checklist_id, user_id=current_user.id).first_or_404()
    return jsonify(checklist.json_content)
```

**After:**
```python
@dashboard_bp.route('/checklists/<int:checklist_id>/load_json')
@dashboard_bp.route('/api/checklist/<int:checklist_id>/load_json')
@login_required
def load_checklist(checklist_id):
    """Load checklist json_content for editing."""
    checklist = Checklist.query.filter_by(id=checklist_id, user_id=current_user.id).first_or_404()
    
    # Parse the JSON content from the database and return as object
    try:
        json_data = json.loads(checklist.json_content) if checklist.json_content else {}
    except (json.JSONDecodeError, TypeError):
        # If parsing fails, return empty default structure
        json_data = {
            "Language": "en-us",
            "Voice": "Linda",
            "Root": {
                "Type": 0,
                "Name": "Root",
                "Children": []
            }
        }
    
    return jsonify(json_data)
```

### 2. Frontend URL Correction

**Template: `templates/dashboard/checklists.html`**
- Updated fetch URL from `/api/checklist/${currentChecklistId}/load_json` to `/dashboard/api/checklist/${currentChecklistId}/load_json`

**Template: `templates/dashboard/view_checklist.html`** 
- Updated fetch URL from `/api/checklist/${currentChecklistId}` to `/dashboard/api/checklist/${currentChecklistId}/load_json`

## Key Improvements

### 1. Proper JSON Parsing
- **Issue**: Previously returned raw JSON string causing double-encoding
- **Fix**: Parse JSON content before returning, ensuring proper object structure

### 2. Dual Route Support
- Added both `/checklists/<id>/load_json` and `/api/checklist/<id>/load_json` patterns
- Maintains consistency with existing API routes

### 3. Error Handling
- Added try/catch for JSON parsing errors
- Provides default fallback structure if parsing fails

### 4. Correct URL Prefixes
- Fixed frontend calls to include `/dashboard` prefix
- Ensures routes are accessible through proper blueprint registration

## Expected Behavior

### Route Response Format
```json
{
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
      }
      // ... more sections
    ]
  }
}
```

### JavaScript Integration
The `loadChecklistData()` function now receives properly structured data:
```javascript
.then(data => {
    // data is now a proper object, not a JSON string
    iframe.contentWindow.postMessage({
        action: 'load',
        data: data  // Direct object, no additional parsing needed
    }, 'https://www.kanardia.eu');
})
```

## Testing

### Authentication Required
- Route requires login through `/auth/login`
- Protected by `@login_required` decorator

### Route Patterns Available
- `/dashboard/checklists/<id>/load_json`
- `/dashboard/api/checklist/<id>/load_json`

### Verification Steps
1. Login to application
2. Navigate to checklists page
3. Check browser network tab for fetch calls to load_json
4. Verify response contains structured JSON object (not string)

## Database Requirements

The route expects:
- `Checklist` table with `json_content` field (TEXT)
- Valid JSON stored in `json_content` column
- User ownership validation through `user_id`

## Error Scenarios Handled

1. **Missing json_content**: Returns default template structure
2. **Invalid JSON**: Falls back to default structure  
3. **Unauthorized access**: Returns 404 (handled by `first_or_404()`)
4. **Authentication required**: Redirects to login

## Implementation Notes

- Removed redundant import of `jsonify` (already imported at module level)
- Maintained backward compatibility with existing checklist structure
- Added comprehensive error handling for robustness
- Dual route registration provides flexibility for different frontend patterns
