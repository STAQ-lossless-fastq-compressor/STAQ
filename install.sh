#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print start message
echo "Installing STAQ project..."

# Navigate to the STAQ directory
if [ -d "STAQ" ]; then
    cd STAQ
else
    echo "Error: STAQ directory not found!"
    exit 1
fi

# Navigate to the Spring directory
if [ -d "Spring" ]; then
    cd Spring
else
    echo "Error: Spring directory not found!"
    exit 1
fi

# Check if the build directory exists, and remove it if it does
if [ -d "build" ]; then
    echo "Removing existing build directory..."
    rm -rf build
fi

# Create the build directory and navigate into it
mkdir -p build
cd build

# Run CMake to generate build files
echo "Running CMake..."
cmake ..

# Run Make to compile the source code
echo "Building project..."
make

# Print completion message
echo "Installation complete!"
