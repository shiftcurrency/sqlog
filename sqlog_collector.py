#!/usr/bin/env python

import sys
import os
import sqlite3
import ConfigParser
import time

class SQLogCollector(object):

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.read('config.ini')
        except Exception as e:
            print "Could read config.ini. Reason: %s" % e
            sys.exit(1)
        if not self.create_database():
            sys.exit(1)

    def parser(self):
        
        self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
        self.c = self.conn_db.cursor()

        file = open(self.config.get("paths", "log_file"),'r')
        st_results = os.stat(self.config.get("paths", "log_file"))
        st_size = st_results[6]
        file.seek(st_size)

        while True:
            where = file.tell()
            line = file.readline()
            if not line:
                time.sleep(0.2)
                file.seek(where)
            else:
                log_dict = self.get_log_dict(line)
                res = self.populate_db(log_dict)
                if res:
                    self.conn_db.commit()

    def populate_db(self, logs_dict):

        if not logs_dict == None:
            for date_time in logs_dict:
                d = date_time
                sev = logs_dict[date_time]['severity']
                log = logs_dict[date_time]['log']
                try:
                    sql = "INSERT OR IGNORE INTO logs (datetime, severity, log_string) VALUES (\'%s\', \'%s\', \'%s\')" % (d, sev, log)
                    self.c.execute(sql)
                except Exception as e:
                    print "Could not insert the entry below. Reason: %s" % e
            return True

    def create_database(self):

        try:
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
            self.c = self.conn_db.cursor()
            self.c.execute('CREATE TABLE IF NOT EXISTS logs (datetime TIMESTAMP, severity TEXT, log_string TEXT)')
            self.conn_db.commit()
            self.conn_db.close()
        except Exception as e:
            print "Could not create database table. Reason: %s" % e
            return False
        return True


    def get_log_dict(self, infile):

        log_dict = {}
        log_line = infile.split(" ")
        """ Assume that the log entries always follows the same syntax, which it does."""
        if len(log_line) >= 3:
            """ Get log level """
            severity = log_line[0]
            """ Get datetime when the log was produced """
            date_time = str(log_line[1] + ' ' + log_line[2])
            """ Get the actual log string """
            log_string = " ".join(str(elm) for elm in log_line[3:])
            """ Append result to dictionary """
            log_dict[date_time] = {'severity':severity, 'log':log_string.strip('|\n') }

        if len(log_dict) == 0:
            return None
        return log_dict
