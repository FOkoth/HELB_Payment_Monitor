#!/bin/bash

echo "🚀 DEPLOYING HELB SYSTEM"
echo "========================="

# Set production mode
export PRODUCTION_MODE=true

# Check if database exists
if [ -f "helb_data.db" ]; then
    echo "✅ Database exists. Checking data integrity..."
    
    # Run data check
    python check_data.py
    
    echo ""
    echo "⚠️  WARNING: You are running in PRODUCTION MODE"
    echo "⚠️  Data will NOT be reinitialized on restart"
    echo "⚠️  Auto-recovery is DISABLED"
    echo ""
    
    read -p "Continue with deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the application
echo "Starting HELB System..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
