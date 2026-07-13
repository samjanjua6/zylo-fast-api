#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies and building React frontend..."
cd frontend-src
npm install
npm run build
cd ..
