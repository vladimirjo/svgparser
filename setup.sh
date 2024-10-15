#!/bin/bash

# Step 1: Install virtual environment
echo "Creating virtual environment..."
python -m venv .venv

# Step 2: Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 3: Install all development dependencies
echo "Installing development dependencies..."
pip install ".[dev]"

# Step 4: Install the package locally
echo "Installing the package locally..."
pip install -e .

echo "Setup complete."
