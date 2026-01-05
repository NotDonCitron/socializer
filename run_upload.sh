#!/bin/bash

# Ensure we are in the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found! Please run the installation step first."
    exit 1
fi

# Check argument
if [ "$1" == "stealth" ]; then
    echo "Running Stealth Uploader (Undetected ChromeDriver)..."
    if [ -n "$2" ]; then
        ./venv/bin/python3 upload_instagram_stealth.py "$2"
    else
        ./venv/bin/python3 upload_instagram_stealth.py
    fi
elif [ "$1" == "explore" ]; then
    echo "Running Instagram Button Explorer..."
    ./venv/bin/python3 instagram_button_explorer.py
elif [ "$1" == "test" ]; then
    echo "Running Instagram Automation Test Suite..."
    ./venv/bin/python3 instagram_test_suite.py
else
    echo "Running Standard Uploader (Instagrapi)..."
    ./venv/bin/python3 upload_instagram.py
fi

echo ""
echo "Usage: ./run_upload.sh [stealth|explore|test] [file_path]"
echo "  stealth [file] - Upload using stealth browser"
echo "  explore        - Find Instagram button positions"
echo "  test           - Run full automation test suite"
echo "  (no args)      - Use instagrapi library"
