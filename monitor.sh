#!/bin/bash

echo "🔍 MONITORING HELB DATABASE"
echo "=========================="

while true; do
    clear
    echo "🕒 $(date)"
    echo "--------------------------"
    
    # Check database size
    if [ -f "helb_data.db" ]; then
        SIZE=$(du -h helb_data.db | cut -f1)
        echo "📦 Database Size: $SIZE"
        
        # Check user count
        USER_COUNT=$(sqlite3 helb_data.db "SELECT COUNT(*) FROM users;" 2>/dev/null)
        if [ -n "$USER_COUNT" ]; then
            echo "👥 Users: $USER_COUNT"
        fi
        
        # Check request count
        REQ_COUNT=$(sqlite3 helb_data.db "SELECT COUNT(*) FROM requests;" 2>/dev/null)
        if [ -n "$REQ_COUNT" ]; then
            echo "📋 Requests: $REQ_COUNT"
        fi
    else
        echo "❌ Database file not found!"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 10
done
