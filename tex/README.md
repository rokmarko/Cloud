# KanardiaCloud User Manual

This directory contains the LaTeX source files for the KanardiaCloud User Manual.

## Prerequisites

### Required Software
- **LaTeX Distribution**: TeX Live (Linux), MikTeX (Windows), or MacTeX (macOS)
- **PDF Viewer**: Any standard PDF viewer
- **Optional**: ImageMagick for generating placeholder images

### Ubuntu/Debian Installation
```bash
sudo apt-get update
sudo apt-get install texlive-full imagemagick
```

### Fedora/RHEL Installation
```bash
sudo dnf install texlive-scheme-full ImageMagick
```

### macOS Installation
```bash
# Install MacTeX
brew install --cask mactex
# Install ImageMagick
brew install imagemagick
```

## Building the Manual

### Quick Build
```bash
make
```

### Generate Placeholder Images and Build
```bash
make full
```

### Watch for Changes (Auto-rebuild)
```bash
make watch
```

### Open Generated PDF
```bash
make open
```

## Project Structure

```
tex/
├── user_manual.tex          # Main LaTeX document
├── Makefile                 # Build automation
├── README.md               # This file
├── chapters/               # Individual chapters
│   ├── introduction.tex
│   ├── getting_started.tex
│   ├── checklist_management.tex
│   ├── dashboard.tex
│   ├── device_management.tex
│   ├── instrument_layouts.tex
│   ├── logbook.tex
│   ├── approach_charts.tex
│   ├── user_settings.tex
│   ├── troubleshooting.tex
│   ├── api_reference.tex
│   ├── appendix_a.tex      # Glossary
│   └── appendix_b.tex      # File formats
└── images/                 # Screenshots and diagrams
    ├── kanardia_logo.png
    ├── dashboard_overview.png
    ├── checklist_dashboard.png
    └── [other screenshots]
```

## Screenshots and Images

### Placeholder Images
The Makefile can generate placeholder images automatically:
```bash
make images
```

### Adding Real Screenshots
1. Take screenshots of the KanardiaCloud interface
2. Save them in the `images/` directory with appropriate names
3. Ensure images are in PNG or JPG format
4. Optimal resolution: 800x600 or 1024x768 for full-screen shots

### Required Screenshots
- `dashboard_overview.png` - Main dashboard
- `registration_form.png` - Account registration
- `checklist_dashboard.png` - Checklist management page
- `create_checklist_form.png` - New checklist form
- `checklist_editor.png` - Checklist editor interface
- `checklist_import.png` - Import interface
- `checklist_print_standard.png` - Standard print format
- `checklist_print_minimal.png` - Minimal print format
- `main_dashboard.png` - Dashboard with data
- `kanardia_logo.png` - Company logo

## Customization

### Adding New Chapters
1. Create a new `.tex` file in the `chapters/` directory
2. Add the chapter to `user_manual.tex`:
   ```latex
   \input{chapters/your_new_chapter}
   ```

### Modifying Styles
- Colors are defined in `user_manual.tex`
- Kanardia orange: `\definecolor{kanardiaOrange}{RGB}{255,87,34}`
- Custom styles can be added to the document preamble

### Updating Content
- Edit the appropriate chapter file
- Run `make` to rebuild the PDF
- Use `make watch` for continuous building during editing

## Available Make Targets

| Target | Description |
|--------|-------------|
| `all` | Build the PDF (default) |
| `clean` | Remove build artifacts |
| `images` | Generate placeholder images |
| `full` | Generate images and build PDF |
| `watch` | Watch for changes and rebuild |
| `open` | Open the generated PDF |
| `check` | Check LaTeX installation |
| `help` | Show help message |

## Troubleshooting

### Common Issues

**LaTeX not found**
```bash
make check  # Verify installation
```

**Missing packages**
- Install full LaTeX distribution: `texlive-full`
- Update package database: `sudo tlmgr update --all`

**Image generation fails**
- Install ImageMagick: `sudo apt-get install imagemagick`
- Or manually place images in the `images/` directory

**PDF not opening**
- Install a PDF viewer: `sudo apt-get install evince`
- Or open manually from file manager

### Build Errors
- Check LaTeX log files in the `build/` directory
- Ensure all referenced images exist
- Verify chapter files are properly formatted

## Contributing

### Guidelines
1. Use consistent formatting and style
2. Include proper LaTeX comments
3. Test builds before committing changes
4. Update this README if adding new features
5. Take high-quality screenshots for documentation

### Chapter Writing Standards
- Use clear, concise language
- Include step-by-step instructions
- Add screenshots for complex procedures
- Follow the existing chapter structure
- Include relevant tables and examples

## Version History

- **v1.0** - Initial complete manual with all major sections
- **v0.9** - Added API reference and troubleshooting
- **v0.8** - Completed core feature documentation
- **v0.7** - Added checklist management chapter
- **v0.6** - Initial structure and basic chapters

## License

This documentation is proprietary to Kanardia d.o.o. and subject to the company's copyright and distribution policies.
