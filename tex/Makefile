# KanardiaCloud User Manual Makefile

# Variables
MAIN_TEX = user_manual.tex
OUTPUT_PDF = user_manual.pdf
BUILD_DIR = build
CHAPTERS_DIR = chapters
IMAGES_DIR = images

# Default target
all: $(OUTPUT_PDF)

# Build the PDF
$(OUTPUT_PDF): $(MAIN_TEX) $(wildcard $(CHAPTERS_DIR)/*.tex) $(wildcard $(IMAGES_DIR)/*)
	@echo "Building KanardiaCloud User Manual..."
	@mkdir -p $(BUILD_DIR)
	pdflatex -output-directory=$(BUILD_DIR) $(MAIN_TEX)
	pdflatex -output-directory=$(BUILD_DIR) $(MAIN_TEX)  # Second pass for references
	@cp $(BUILD_DIR)/$(OUTPUT_PDF) $(OUTPUT_PDF)
	@echo "PDF generated successfully: $(OUTPUT_PDF)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@rm -f $(OUTPUT_PDF)
	@echo "Clean completed"

# Generate placeholder images
images:
	@echo "Generating placeholder images..."
	@mkdir -p $(IMAGES_DIR)
	@# Create placeholder images using ImageMagick (if available)
	@if command -v convert >/dev/null 2>&1; then \
		convert -size 800x600 xc:white -fill black -gravity center -pointsize 24 \
			-annotate +0+0 "KanardiaCloud\\nDashboard\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/dashboard_overview.png; \
		convert -size 600x400 xc:white -fill black -gravity center -pointsize 20 \
			-annotate +0+0 "Checklist Dashboard\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/checklist_dashboard.png; \
		convert -size 500x350 xc:white -fill black -gravity center -pointsize 16 \
			-annotate +0+0 "Registration Form\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/registration_form.png; \
		convert -size 800x600 xc:white -fill black -gravity center -pointsize 20 \
			-annotate +0+0 "Main Dashboard\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/main_dashboard.png; \
		convert -size 600x400 xc:white -fill black -gravity center -pointsize 18 \
			-annotate +0+0 "Create Checklist\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/create_checklist_form.png; \
		convert -size 800x600 xc:white -fill black -gravity center -pointsize 20 \
			-annotate +0+0 "Checklist Editor\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/checklist_editor.png; \
		convert -size 600x400 xc:white -fill black -gravity center -pointsize 18 \
			-annotate +0+0 "Checklist Import\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/checklist_import.png; \
		convert -size 400x600 xc:white -fill black -gravity center -pointsize 14 \
			-annotate +0+0 "Standard Print\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/checklist_print_standard.png; \
		convert -size 400x600 xc:white -fill black -gravity center -pointsize 14 \
			-annotate +0+0 "Minimal Print\\n(Screenshot Placeholder)" \
			$(IMAGES_DIR)/checklist_print_minimal.png; \
		convert -size 200x100 xc:white -fill orange -gravity center -pointsize 16 \
			-annotate +0+0 "KANARDIA" \
			$(IMAGES_DIR)/kanardia_logo.png; \
		echo "Placeholder images generated"; \
	else \
		echo "ImageMagick not found. Please install it or add images manually."; \
		touch $(IMAGES_DIR)/dashboard_overview.png; \
		touch $(IMAGES_DIR)/checklist_dashboard.png; \
		touch $(IMAGES_DIR)/registration_form.png; \
		touch $(IMAGES_DIR)/main_dashboard.png; \
		touch $(IMAGES_DIR)/create_checklist_form.png; \
		touch $(IMAGES_DIR)/checklist_editor.png; \
		touch $(IMAGES_DIR)/checklist_import.png; \
		touch $(IMAGES_DIR)/checklist_print_standard.png; \
		touch $(IMAGES_DIR)/checklist_print_minimal.png; \
		touch $(IMAGES_DIR)/kanardia_logo.png; \
		echo "Placeholder files created"; \
	fi

# Build with images
full: images $(OUTPUT_PDF)

# Watch for changes and rebuild (requires entr or inotify-tools)
watch:
	@if command -v entr >/dev/null 2>&1; then \
		find . -name "*.tex" | entr -c make $(OUTPUT_PDF); \
	elif command -v inotifywait >/dev/null 2>&1; then \
		while inotifywait -e modify -r .; do make $(OUTPUT_PDF); done; \
	else \
		echo "Neither entr nor inotifywait found. Install one for watch functionality."; \
	fi

# Open the PDF (Linux)
open: $(OUTPUT_PDF)
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open $(OUTPUT_PDF); \
	elif command -v evince >/dev/null 2>&1; then \
		evince $(OUTPUT_PDF) &; \
	else \
		echo "No suitable PDF viewer found"; \
	fi

# Check LaTeX installation
check:
	@echo "Checking LaTeX installation..."
	@command -v pdflatex >/dev/null 2>&1 || { echo "pdflatex not found. Please install LaTeX."; exit 1; }
	@echo "LaTeX installation OK"

# Help
help:
	@echo "KanardiaCloud User Manual Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  all      - Build the PDF (default)"
	@echo "  clean    - Remove build artifacts"
	@echo "  images   - Generate placeholder images"
	@echo "  full     - Generate images and build PDF"
	@echo "  watch    - Watch for changes and rebuild"
	@echo "  open     - Open the generated PDF"
	@echo "  check    - Check LaTeX installation"
	@echo "  help     - Show this help message"

.PHONY: all clean images full watch open check help
