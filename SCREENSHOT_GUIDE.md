# KanardiaCloud Screenshot Capture Guide

## Demo Account Created
- **Email**: demo@kanardia.com
- **Password**: demo123
- **Admin access**: Yes

## Application URL
http://localhost:5000

## Screenshots Needed for Manual

### 1. Authentication Screenshots
- [ ] **login_form.png** - Login page (http://localhost:5000/login)
- [ ] **registration_form.png** - Registration page (http://localhost:5000/register)

### 2. Dashboard Screenshots  
- [ ] **main_dashboard.png** - Main dashboard after login (http://localhost:5000/dashboard)
- [ ] **dashboard_overview.png** - Dashboard overview with navigation

### 3. Checklist Management Screenshots
- [ ] **checklist_dashboard.png** - Checklist management page (http://localhost:5000/checklists)
- [ ] **create_checklist_form.png** - Create new checklist form
- [ ] **checklist_editor.png** - Checklist editing interface
- [ ] **checklist_import.png** - Checklist import functionality
- [ ] **checklist_print_standard.png** - Standard print preview of checklist
- [ ] **checklist_print_minimal.png** - Minimal print preview of checklist

### 4. Device Management Screenshots
- [ ] **device_management.png** - Device management interface (http://localhost:5000/devices)
- [ ] **device_details.png** - Device details/configuration

### 5. Logbook Screenshots
- [ ] **logbook_overview.png** - Logbook main page (http://localhost:5000/logbook)
- [ ] **logbook_entry.png** - Individual logbook entry view

### 6. Settings Screenshots
- [ ] **user_settings.png** - User settings/preferences page
- [ ] **admin_panel.png** - Admin panel (if accessible)

## Manual Screenshot Process

1. **Open Browser**: The application should already be open in the Simple Browser
2. **Navigate**: Go to http://localhost:5000
3. **Login**: Use demo@kanardia.com / demo123
4. **Capture**: Take screenshots of each page/feature
5. **Save**: Save screenshots to `/home/rok/src/Cloud-1/tex/screenshots/`
6. **Copy to Manual**: Copy relevant screenshots to `/home/rok/src/Cloud-1/tex/images/`

## After Screenshots Are Captured

Run this command to copy screenshots to the manual:
```bash
cd /home/rok/src/Cloud-1/tex
cp screenshots/*.png images/
make clean && make
```

## Screenshot Tips

- **Window Size**: Use consistent browser window size (ideally 1920x1080 or similar)
- **Content**: Make sure pages are fully loaded before capturing
- **Quality**: Save as PNG format for best quality
- **Naming**: Use the exact filenames listed above for easy integration

## Alternative: Replace Placeholders Later

If manual screenshots are not possible right now, the PDF manual already works with placeholder images. You can:

1. Generate the current PDF: `cd tex && make`
2. Add real screenshots later by replacing files in `tex/images/`
3. Regenerate PDF when ready

The manual structure is complete and ready for use with either placeholder or real images.
