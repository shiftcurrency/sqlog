#!/usr/bin/env bash

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8

running=0
logfile_to_parse="lisk.log"
sqlog_dir=$(dirname "$log_file_to_parse");
sqlog_db="$sqlog_dir/sqlog.db";
sqlog_logfile="$sqlog_dir/sqlog.log"
sqlite=$(whereis sqlite3 |awk {'print $2'});


check_prereq() {

    if [[ -z "$sqlite" ]]; then
        echo "SQLite3 not installed. Run: sudo apt-get install sqlite3";
        exit 1;
    fi
}

create_db() {

    createdb='CREATE TABLE IF NOT EXISTS logs (datetime TIMESTAMP PRIMARY KEY NOT NULL, severity TEXT, log_string TEXT)';
    $sqlite $sqlog_db "$createdb" &> $sqlog_logfile || { echo "Could not create database. Check logfile $sqlog_logfile. Exiting." && exit 1; }
    echo "$(date): Created database $sqlog_db." >> $sqlog_logfile
}

running_status() {
    
    running=$(ps aux |grep 'sqlog_collector.bash start' |wc -l)
    if [[ "$running" -gt "1" ]]; then
        echo "OK";
        exit 0;
    else
        echo "KO";
        exit 1;
    fi
}

stop_collector() {

    ## It is safe to kill the process with "kill", it will do no harm to the SQLite database.
    for i in $(ps aux |grep sqlog_collector.bash |awk {'print $2'}); do kill $i &> $sqlog_logfile; done
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
    else
        echo "$logfile_to_parse could not be found in this directory. Exiting."
        exit 1
    fi
}


parse_option() {
    OPTIND=2
    while getopts ":f:" opt; do
    case $opt in
    f)
        if [[ -f "$OPTARG" ]] 2> /dev/null; then
            logfile_to_parse=$OPTARG
        fi
    ;;
    *) echo "Unknown option: -$OPTARG" >&2; exit 1
    ;;
    esac
  done
}

parse_option $@

case $1 in
    "status")
        running_status
    ;;
    "start")
        check_prereq
        create_db
        start_collector
    ;;
    "stop")
        stop_collector
    ;;

*)
    echo 'Available options: start, stop, status'
    echo 'Usage: ./sqlog_collector.bash start'
    exit 1
;;
esac
exit 0;
