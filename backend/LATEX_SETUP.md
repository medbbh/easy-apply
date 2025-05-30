# LaTeX Setup for PDF Generation

This application generates professional PDF documents using LaTeX. To enable LaTeX-based PDF generation, you need to install a TeX distribution on your system.

## Installation Instructions

### Windows
1. Download and install MiKTeX from https://miktex.org/download
2. During installation, choose "Install for all users" and enable automatic package installation
3. After installation, MiKTeX will automatically download required packages when needed

### macOS
1. Install MacTeX using Homebrew:
   ```bash
   brew install --cask mactex
   ```
   OR download the installer from https://www.tug.org/mactex/

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install texlive-full
```

### Linux (Fedora/RHEL)
```bash
sudo dnf install texlive-scheme-full
```

## Minimal Installation (if full installation is too large)

For a minimal installation that includes only the necessary packages:

### Ubuntu/Debian:
```bash
sudo apt-get install texlive-base texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra
```

### Required LaTeX Packages
The application uses the following LaTeX packages:
- fontawesome5
- charter
- enumitem
- hyperref
- geometry
- titlesec

## Fallback Option

If LaTeX is not available on your system, the application will automatically fall back to using WeasyPrint for PDF generation. While the output won't match the exact LaTeX styling, it will still produce professional-looking PDFs.

## Verifying Installation

To verify that LaTeX is installed correctly, run:
```bash
pdflatex --version
```

You should see version information for pdfTeX.

## Troubleshooting

1. **"LaTeX compiler not found" error**: Ensure that pdflatex or xelatex is in your system's PATH
2. **Missing packages**: If you get errors about missing packages, install the full TeX distribution or use your distribution's package manager to install missing packages
3. **Font issues**: The template uses the Charter font. If it's not available, the system will fall back to a default font

## Docker Installation

If you're using Docker, add this to your Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    texlive-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*
``` 