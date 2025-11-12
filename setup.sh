#!/bin/bash
# Quick setup script for LinkedIn Scraper

echo "================================"
echo "LinkedIn Scraper - Setup Script"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.7+"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✓ Dependencies installed"
echo ""

# Test installation
echo "Testing installation..."
python3 -c "import selenium; import requests; import lxml; from linkedin_scraper import actions; print('✓ All packages working')"

if [ $? -ne 0 ]; then
    echo "❌ Installation test failed"
    exit 1
fi

echo ""
echo "================================"
echo "✨ Setup Complete!"
echo "================================"
echo ""
echo "To use the scraper:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run job scraper: python3 scrape_search_results.py"
echo "  3. Run connection sender: python3 scripts/run_connection_sender.py"
echo ""
echo "Read SETUP.md for detailed instructions"
echo "Read README_CONNECTIONS.md for connection automation safety"
echo ""
