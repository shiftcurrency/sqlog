#!/usr/bin/env bash
# Joey, <shiftcurrency@gmail.com>

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8

logfile_to_parse=$1;

if [[ -z "$logfile_to_parse" ]] || [[ ! -f "$logfile_to_parse" ]]; then
    echo "Start with LISK/SHIFT log file as first argument. Specify full path.";
    echo "Example: $0 /home/lisk/lisk-main/logs/lisk.log";
fi

sqlog_dir=$(dirname "$log_file_to_parse");
sqlog_db="$sqlog_dir/sqlog.db";
sqlog_logfile="$sqlog_dir/sqlog.log"
sqlite=$(whereis sqlite3 |awk {'print $2'});

if [[ -z "$sqlite" ]]; then
    echo "SQLite3 not installed. Run: sudo apt-get install sqlite3";
    exit 1;
fi

create_db() {

    createdb='CREATE TABLE IF NOT EXISTS logs (datetime TIMESTAMP PRIMARY KEY NOT NULL, severity TEXT, log_string TEXT)';
    $sqlite $sqlog_db "$createdb" &> $sqlog_logfile || { echo "Could not create database. Check logfile $sqlog_logfile. Exiting." && exit 1; }
    echo "$(date): Created database $sqlog_db." >> $sqlog_logfile
}

start_collector() {

    counter=0

    if [[ -f "$logfile_to_parse" ]]; then
        echo "$(date): Started sqlog collector." >> $sqlog_logfile
        tail -F -n0 $logfile_to_parse | stdbuf -i0 -oL tr -d '|[]'| while read "severity" "date" "time" "logstring"; do
            $sqlite $sqlog_db "INSERT OR IGNORE INTO logs (datetime, severity, log_string) VALUES ('$date $time', '$severity', '$logstring')"
            ((counter++)) 
            if (( counter % 1000 == 0 )); then
                echo "$(date): Number of log lines parsed: $counter" >> $sqlog_logfile
            fi
        done
    fi
}

create_db
start_collector
