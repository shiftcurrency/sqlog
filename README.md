# SQLOG
SQLOG is a log parser and monitoring system that reads SHIFT/LISK log files. 
The logs can then be worked with via a sql database doing all sorts of cool stuff.

# Run
nohup bash sqlog_collector.bash start -f /home/xxxx/shift/logs/shift.log &

# Check status (running or not)
bash sqlog_collector.bash status

# Stop
bash sqlog_collector.bash status
