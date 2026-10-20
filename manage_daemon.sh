#!/usr/bin/env bash
# ==============================================================================
# Autonomous Cold Outreach Service Manager for Rajat Murhe
# Manage the background outreach daemon without Antigravity
# ==============================================================================

PLIST_NAME="com.rajatmurhe.outreach.plist"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

case "$1" in
    install)
        echo "=================================================="
        echo "🚀 Installing Automated Outreach Daemon (launchd)"
        echo "=================================================="
        mkdir -p "$HOME/Library/LaunchAgents"
        mkdir -p "$SCRIPT_DIR/logs"

        # Copy plist to user LaunchAgents directory
        cp "$SCRIPT_DIR/$PLIST_NAME" "$TARGET_PLIST"

        # Unload any previous version and load new
        launchctl unload "$TARGET_PLIST" 2>/dev/null
        launchctl load "$TARGET_PLIST"

        echo "✅ Daemon installed successfully!"
        echo "📅 Schedule: Monday to Friday at 9:30 AM"
        echo "📂 Target plist: $TARGET_PLIST"
        echo "💡 To check status anytime: ./manage_daemon.sh status"
        echo "=================================================="
        ;;

    uninstall)
        echo "Stopping and uninstalling Outreach Daemon..."
        launchctl unload "$TARGET_PLIST" 2>/dev/null
        rm -f "$TARGET_PLIST"
        echo "✅ Outreach Daemon uninstalled. Scheduled runs are disabled."
        ;;

    status)
        echo "=================================================="
        echo "📊 Outreach Daemon Status"
        echo "=================================================="
        if launchctl list | grep -q "com.rajatmurhe.outreach"; then
            echo "🟢 Service: ACTIVE & SCHEDULED in macOS launchd"
        else
            echo "⚪ Service: NOT currently scheduled (run './manage_daemon.sh install' to enable)"
        fi
        echo ""
        echo "📈 Today's Statistics:"
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c "
import csv, datetime
today = datetime.date.today().strftime('%Y-%m-%d')
today_sent = 0
all_sent = set()
by_acc = {}
try:
    with open('$SCRIPT_DIR/emails_sent.csv', 'r') as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) > 4 and row[4] == 'Success':
                all_sent.add(row[1].lower().strip())
                if row[0].startswith(today):
                    today_sent += 1
                    acc = row[6].strip() if len(row) > 6 else 'unknown'
                    by_acc[acc] = by_acc.get(acc, 0) + 1
    print(f'  • Sent today ({today}): {today_sent} applications')
    print(f'  • Breakdown today: {by_acc}')
    print(f'  • All-time unique recruiters reached: {len(all_sent)}')
except Exception as e:
    print('  • Tracking file not found or empty:', e)
"
        echo ""
        echo "📁 Recent Logs:"
        LATEST_LOG="$SCRIPT_DIR/logs/outreach_$(date +%Y-%m-%d).log"
        if [ -f "$LATEST_LOG" ]; then
            tail -n 5 "$LATEST_LOG"
        else
            echo "  (No log entries recorded yet today)"
        fi
        echo "=================================================="
        ;;

    run-now)
        echo "▶️ Triggering outreach run immediately..."
        cd "$SCRIPT_DIR"
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 "$SCRIPT_DIR/daily_outreach_daemon.py"
        ;;

    logs)
        LATEST_LOG="$SCRIPT_DIR/logs/outreach_$(date +%Y-%m-%d).log"
        if [ -f "$LATEST_LOG" ]; then
            echo "Displaying live logs for today ($LATEST_LOG):"
            tail -f "$LATEST_LOG"
        else
            echo "No log file found for today. Showing daemon stdout log:"
            tail -f "$SCRIPT_DIR/logs/launchd_stdout.log" 2>/dev/null || echo "No logs yet."
        fi
        ;;

    *)
        echo "Usage: ./manage_daemon.sh {install | uninstall | status | run-now | logs}"
        echo ""
        echo "Commands:"
        echo "  install    - Schedule the daemon to run automatically at 9:30 AM every weekday"
        echo "  uninstall  - Remove the scheduled service"
        echo "  status     - Show daemon status, today's email count, and account breakdown"
        echo "  run-now    - Manually run today's outreach immediately right now"
        echo "  logs       - View live outreach logs"
        exit 1
        ;;
esac
