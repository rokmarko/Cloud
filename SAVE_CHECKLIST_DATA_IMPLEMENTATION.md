# SaveChecklistData Implementation

## Summary
Implemented the `saveChecklistData()` method in the checklist editor to handle autosave functionality by writing JSON data to the `json_content` field.

## Backend Changes

### 1. Enhanced API Update Route (`src/routes/dashboard.py`)

**Modified:** `api_update_checklist()` function to handle `json_content` updates

```python
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
    # NEW: Handle json_content updates (for checklist editor)
    if 'json_content' in request_data:
        checklist.json_content = json.dumps(request_data['json_content'])
    # NEW: If data is provided without explicit json_content, also update json_content
    elif 'data' in request_data:
        checklist.json_content = json.dumps(request_data['data'])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Checklist updated successfully'
    })
```

## Frontend Changes

### 2. New JavaScript Function (`templates/dashboard/checklists.html`)

**Added:** `saveChecklistData()` function for autosave functionality

```javascript
/**
 * Save checklist data directly (for autosave functionality)
 * @param {Object} data - The checklist data to save
 */
function saveChecklistData(data) {
    if (!currentChecklistId) {
        console.error('No checklist ID available for saving');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Save to backend API
    fetch(`/dashboard/api/checklist/${currentChecklistId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            json_content: data
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        console.log('Checklist autosaved successfully:', result);
        // Optional: Show a subtle notification that data was saved
    })
    .catch(error => {
        console.error('Error autosaving checklist:', error);
        // Don't show alert for autosave failures as they can be disruptive
    });
}
```

## Integration Flow

### 1. Autosave Trigger
- Editor iframe sends 'autosave' event with payload data
- Event handler calls `saveChecklistData(payload.data)`

### 2. Data Flow
```
Checklist Editor (iframe) 
    ↓ postMessage with autosave event
JavaScript handleEditorMessage() 
    ↓ calls saveChecklistData(data)
Frontend saveChecklistData() 
    ↓ PUT request with json_content
Backend api_update_checklist() 
    ↓ saves to database
Database json_content field updated
```

### 3. API Request Format
```javascript
PUT /dashboard/api/checklist/{id}
Content-Type: application/json
X-CSRFToken: {token}

{
  "json_content": {
    "Language": "en-us",
    "Voice": "Linda",
    "Root": {
      "Type": 0,
      "Name": "Root",
      "Children": [...]
    }
  }
}
```

### 4. Database Storage
- Data is stored as JSON string in `checklist.json_content` field
- Backend automatically serializes object to JSON string using `json.dumps()`
- Load operations parse JSON string back to object using `json.loads()`

## Key Features

### 1. Autosave Functionality
- **Trigger**: Editor sends autosave events automatically
- **Silent Operation**: No user alerts on autosave failures (only console logging)
- **Background Saving**: Non-blocking operation that doesn't interrupt editing

### 2. Error Handling
- **Missing Checklist ID**: Logs error and returns early
- **Network Failures**: Catches and logs errors without user disruption
- **Authentication Issues**: Handled by CSRF token validation

### 3. CSRF Protection
- Uses meta tag CSRF token for security
- Protects against cross-site request forgery attacks
- Token extracted from `<meta name="csrf-token">` element

### 4. Data Consistency
- **Dual Update**: Updates both `items` and `json_content` when data provided
- **Flexible Input**: Accepts either `json_content` or `data` in request
- **Automatic Serialization**: Backend handles JSON string conversion

## Testing

### Manual Testing Steps
1. Open checklist editor modal
2. Make changes to checklist structure
3. Wait for autosave event from editor
4. Check browser console for "Checklist autosaved successfully" message
5. Verify data persistence by reloading the checklist

### Expected Console Output
```
Checklist autosaved successfully: {success: true, message: "Checklist updated successfully"}
```

### Error Scenarios
- **No Checklist ID**: "No checklist ID available for saving"
- **Network Error**: "Error autosaving checklist: [error details]"
- **Authentication Error**: HTTP 403 response

## Implementation Benefits

### 1. User Experience
- **Automatic Saving**: Users don't lose work if they forget to save
- **Silent Operation**: No disruptive popup messages during editing
- **Real-time Persistence**: Changes saved as user works

### 2. Data Integrity
- **Consistent Storage**: Both legacy `items` and new `json_content` fields updated
- **Error Recovery**: Graceful handling of save failures
- **Security**: CSRF protection prevents unauthorized updates

### 3. Developer Experience
- **Clean API**: Single endpoint handles multiple update scenarios
- **Extensible**: Easy to add additional autosave triggers
- **Debuggable**: Console logging helps with troubleshooting

## Future Enhancements

### 1. Visual Feedback
- Add subtle "Saved" indicator when autosave succeeds
- Show temporary notification for save confirmations
- Display offline/connection status

### 2. Conflict Resolution
- Handle concurrent editing scenarios
- Add version checking to prevent overwrites
- Implement optimistic locking

### 3. Performance Optimization
- Debounce autosave requests to reduce server load
- Implement local caching for offline editing
- Add compression for large checklist data
