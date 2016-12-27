#!/usr/bin/env python

import time
import sys
import ConfigParser
from sqlog_logic import SQLog
from multiprocessing import Process
from sqlog_collector import SQLogCollector 
from sqlog_notifications import Email

def start_collector():

    collector = SQLogCollector()
    try:
        thd = Process(target=collector.parser)
        res = thd.start()
        if thd.is_alive():
            return thd 
        return False
    except Exception as e:
        print "Could not start collector daemon. Reason: %s" % e

def stop_collector(thd):

    try:
        """ Always return None, but lets check it anyway. """
        if thd.terminate() == None:
            while thd.is_alive():
                continue
            return True
    except Exception as e:
        print "Could not stop collector daemon. Reason: %s" % e

def node_running(node):

    if node == "primary" and not logic.node_running(config.get("failover", "primary_node")):
        if config.get("notifications", "enable_email"):
            res = mail.send_email("Primary node is down.")
        return False
    elif node == "secondary" and not logic.node_running(config.get("failover", "secondary_node")):
       if config.get("notifications", "enable_email"):
            res = mail.send_email("Secondary node is down.")
            return False
    return True

def low_broadhash():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """

    if logic.check_broadhash() and config.get("failover", "this_node") == "primary" \
            and logic.forging(config.get("failover", "primary_node")) and node_running("secondary") \
            and not logic.syncing(config.get("failover", "secondary_node")):
        logic.logger("Broadhash consensus on secondary node is higher than on primary node. Commit failover.")
        if logic.failover("secondary"):
            return True
    return False

def force_forge():
    if config.get("failover", "this_node") == "secondary" and not node_running("primary") \
            and not logic.ping(config.get("failover", "primary_node")) \
            and not logic.forging(config.get("failover", "secondary_node")):
        log = "Primary node is DOWN (both API and ICMP), forcing forging on secondary node."
        logic.logger(log)
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
        logic.failover("secondary")
        return True
    elif config.get("failover", "this_node") == "primary" and not node_running("secondary") \
            and not logic.ping(config.get("failover", "secondary_node")) \
            and not logic.forging(config.get("failover", "primary_node")):
        log = "Secondary node is DOWN (both API and ICMP), forcing forging on primary node."
        logic.logger(log)
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
        logic.failover("primary")
        return True
    else:
        """ Check that we do not have both primary and secondary node forging at the same time. """
        if logic.forging(config.get("failover", "secondary_node")) \
            and logic.forging(config.get("failover", "primary_node")):
            logic.failover("primary")
    return False

def primary_takeover():

    """ Always make sure that the primary node is active if everything is OK. """
    if not logic.check_broadhash() and not logic.syncing("127.0.0.1") \
        and not logic.get_rebuild_status() and logic.blockchain_loaded() \
        and not logic.check_fork3() and not logic.forging(config.get("failover", "primary_node")):
        """ Everything is OK at primary node. """
        if config.get("failover", "this_node") == "primary":
            logic.logger("Primary node OK, taking over.")
            if logic.failover("primary"):
                return True
    return False

def bad_db_rebuild():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.bad_memory_table() and not logic.syncing("127.0.0.1") and not logic.get_rebuild_status() \
        and logic.set_rebuild_status("True"):
        log = "Faulty database detected, rebuilding blockchain."
        logic.logger(log)
        if config.get("failover", "this_node") == "primary" and node_running("secondary") \
            and not logic.forging(config.get("failover", "secondary_node")):
            logic.failover("secondary")
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
        if logic.run_script("rebuild"):
            logic.logger("Blockchain rebuild finished.")
            if logic.syncing("127.0.0.1"):
                logic.logger("Syncing blockchain.")
            return True
    return False


def check_fork():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.check_fork3() and not logic.syncing("127.0.0.1") and not logic.get_rebuild_status() \
        and logic.set_rebuild_status("True"):
        if config.get("failover", "this_node") == "primary" and node_running("secondary") \
            and not logic.forging(config.get("failover", "secondary_node")):
            logic.failover("secondary")
        log = "Fork type 3 detected, rebuilding blockchain."
        logic.logger(log)
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
        if logic.run_script("rebuild"):
            logic.logger("Blockchain rebuild finished.")
            if logic.syncing("127.0.0.1"):
                logic.logger("Syncing blockchain.")
            return True
    return False

def check_height():

    """ 1. Check if we have detected a fork within the time offset in config.ini.
        2. Check that the blockchain is not syncing from a recent rebuild.
        3. Check that the blockchain is loaded completely. """
    if logic.height_low() and not logic.syncing("127.0.0.1") and not logic.get_rebuild_status() and logic.blockchain_loaded() \
        and logic.set_rebuild_status("True"):
        """ 1. Set rebuild status to True
            2. Commit a fail over. """
        if config.get("failover", "this_node") == "primary" and node_running("secondary") \
            and not logic.forging(config.get("failover", "secondary_node")):
            logic.failover("secondary")
        log = "Own blockheight is %s blocks low compared to consensus, rebuilding blockchain." \
                % (str(config.get("general", "block_offset")))
        if config.get("notifications", "enable_email"):
            res = mail.send_email(log)
        logic.logger(log)
        if logic.run_script("rebuild"):
            logic.logger("Blockchain rebuild finished.")
            if logic.syncing("127.0.0.1"):
                logic.logger("Syncing blockchain.")
            return True
    return False

def main():
    try:
        counter=0
        collector_thread = start_collector()
        if collector_thread:
            logic.logger("SQLog collector started.")
            while True:
                counter+=1
                if (counter % 300) == 0 or counter == 1:
                    if not logic.syncing("127.0.0.1"): logic.stats()
                    else: logic.logger("Blockchain is syncing...")
                if not logic.syncing("127.0.0.1") and not node_running(config.get("failover", "this_node")):
                    logic.logger("Node software on localhost is not running, trying to start it...")
                    if config.get("failover", "this_node") == "primary" and node_running("secondary"):
                        logic.failover("secondary")
                    if logic.run_script("start"):
                        logic.logger("Node started on localhost.")
                        time.sleep(2)
                        continue
                else:
                    if not force_forge():
                        if low_broadhash():
                            continue
                        if primary_takeover():
                            continue
                    if check_height():
                        logic.set_rebuild_status("False")
                    if check_fork():
                        logic.set_rebuild_status("False")
                    if bad_db_rebuild():
                        logic.set_rebuild_status("False")
                time.sleep(6)
    except (KeyboardInterrupt, SystemExit):
        if stop_collector(collector_thread):
            logic.logger("SQLog collector stopped.")

if __name__ == "__main__":
    config = ConfigParser.RawConfigParser()
    logic = SQLog()
    mail = Email()
    try:
        config.read('config.ini')
    except Exception as e:
        log = "Could read config.ini. Reason: %s" % e
        logic.logger(log)
        sys.exit(1)
    main()
