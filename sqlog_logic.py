import json
import requests
import subprocess
import sys
import os.path
import sqlite3
import ConfigParser
import re

class SQLog(object):

    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        try:
            self.config.read('config.ini')
        except Exception as e:
            print "Could read config.ini. Reason: %s" % e 
            sys.exit(1)

        try:
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_db")))
            self.c = self.conn_db.cursor()
        except Exception as e:
            print e
            sys.exit(1)

    def whos_forging(self):
        
        """ Return values:
            string: forging node (primary or secondary)
            False: Could not determine which node is forging.
            None. Exception thrown. Could not set forging node. """
        try:
            self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()

            if self.forging(self.config.get("failover", "primary_node")):
                self.c.execute('UPDATE status SET whos_forging = "primary"')
                self.conn_db.commit()
                self.conn_db.close()
                print "Primary node(%s) is forging." % self.config.get("failover", "primary_node")
                return "primary"
            elif self.forging(self.config.get("failover", "secondary_node")):
                self.c.execute('UPDATE status SET whos_forging = "secondary"')
                self.conn_db.commit()
                self.conn_db.close()
                print "Secondary node(%s) is forging." % self.config.get("failover", "secondary_node")
                return "secondary"
        except Exception as e:
            print "Could not set forging node. Reason: %s" % e
            return None
        return False

    def forging(self, ip):

        """ Argument: IP-address(string).
            Return values:
            True: IP-address with account is forging.
            False: IP-address with account is not forging.
            None: Exception thrown. """

        url = "http://" + ip + ":" + self.config.get("general", "api_port") + \
                "/api/accounts/getPublicKey?address=" + self.config.get("failover", "address")
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success'] == True:
                public_key = res['publicKey']
        except Exception as e:
            print "Could not get public key of account %s. Reason: %s" % \
                (self.config.get("failover", "address"), e)
            return None

        url = "http://" + ip + ":" + self.config.get("general", "api_port") + \
                "/api/delegates/forging/status?publicKey=" + public_key
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success'] == True:
                if res['enabled'] == True:
                    return True
        except Exception as e:
            print e
            print "Could not check if %s is forging with account %s" % \
                (ip, self.config.get("failover", "address"))
            return None
        return False

    def blockhain_loaded(self):

        """ 
        Return values: 
        True: The blockchain is loaded.
        False: The blockchain is not loaded.
        None: Exception, we can not determine if the blockchain is loaded.
        """
        
        url = "http://127.0.0.1:" + self.config.get("general", "api_port") + "/api/loader/status"
        try:
            http_req = requests.get(url)
            res = http_req.json()
        except Exception as e:
            print "Could not fetch node status. Reason: %s" % e
            return None

        if 'success' in res and res['success'] == True and 'loaded' in res and res['loaded'] == True:
            return True
        return False

    def get_rebuild_status(self):

        """ 
        Return values: 
        True: We have an on going blockchain rebuild.
        False: We do not have an on going blockchain rebuild.
        None: An exception as thrown. Can not determine a if we have an on going rebuild.
        """

        try:
            self.conn_db = self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()
            self.c.execute('SELECT rebuild FROM status')
            res = self.c.fetchall()
        except Exception as e:
            print "Could not fetch rebuild status. Reason: %s" % e 
            return None

        if len(res) > 0:
            if res[0][0] == "True":
                return True
        return False

    def set_rebuild_status(self, status):

        """ 
        Return values: 
        True: Successfully updated the database that we have an on going rebuild.
        False: Could not update the database that we have an on going rebuild.
        """

        try:
            self.conn_db = self.conn_db = sqlite3.connect((self.config.get("general", "sqlog_stats_db")))
            self.c = self.conn_db.cursor()
            sql = "UPDATE status SET rebuild = \'%s\'" % status
            self.c.execute(sql)
            self.conn_db.commit()
            self.conn_db.close()
        except Exception as e:
            print "Could not set rebuild status to True. Reason: %s" % e
            return False
        return True
 
    def consensus_height(self):

        """ 
        Return values: 
        Success: Blockheight as an integer
        False: No values could be fetched.
        """

        heights = []
        ips = self.config.get("general", "blockheight_nodes")

        for ip in ips.split():
            url = "http://" + str(ip) + ":" + self.config.get("general", "api_port") + "/api/blocks/getHeight"
            try:
                http_req = requests.get(url)
                res = http_req.json()
            except Exception as e:
                pass
            if 'success' in res and res['success'] and 'height' in res:
                heights.append(res['height'])

        if len(heights) > 0:
            heights.sort()
            return heights[-1]
            
        return False

    def height_low(self, consensus_height, own_height):

        """ 
        Return values: 
        True: Node is syncing blocks
        False: Node is not syncing blocks 
        """

        if consensus_height and own_height and \
            (int(own_height) <= int(consensus_height)-int(self.config.get("general", "block_offset"))):
            return True
        return True

    def syncing(self):

        """ Return values: 
            height: as integer on success
            None: if no result is returned
            False: Exception """

        url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/loader/status/sync'
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success']:
                if res['syncing'] == True:
                    return True
        except Exception as e:
            pass
        return False

    def own_height(self):

        """ Return values: 
            height: as integer on success
            False: if no result is returned
            None: Exception, could not fetch own blockheight. """

        url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/blocks/getHeight'
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success']:
                height = res['height']
                return height
        except Exception as e:
            return None
        return False

    def restart(self):
        try:
            p = subprocess.Popen(["/bin/bash", str(self.config.get("paths", "management_script")), "reload"],  stdout=subprocess.PIPE, shell=False)
            (output, err) = p.communicate()
            proc_status = p.wait()
            if proc_status == 0:
                return True
        except Exception as e:
            pass
        return False

    def rebuild(self):

        try:
            p = subprocess.Popen(["/bin/bash", str(self.config.get("paths", "management_script")), "rebuild"],  stdout=subprocess.PIPE, shell=False)
            (output, err) = p.communicate()
            proc_status = p.wait()
            if proc_status == 0:
                return True
        except Exception as e:
            print e
            return None
        return False

    def check_broadhash(self):

        """ Return values:
            False: broadhash consensus is bigger or equal to 51%
            True: Broadhash is lower than 51%
            None: Exception """
        try:
            sql = 'SELECT * FROM logs WHERE log_string like \'%Broadhash%\' AND log_string NOT LIKE \'%100%\'' + \
                'AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\', datetime(\'now\', \'-20 seconds\'))) < datetime ORDER BY datetime DESC LIMIT 1'
            self.c.execute(sql)
            res = self.c.fetchall()
            if len(res) >= 1 and len(res[0]) > 0:
                consensus = int(re.search(r'\d+', str(res[0][2])).group())
                if int(consensus) < 51:
                    return True
        except Exception as e:
            return None
        return False

    def bad_memory_table(self):

        """ Return values:
            False: We did not find a bad memory table rebuild within the last 30 seconds.
            True: We found a bad memory table. """

        """ If LISK/SHIFT finds e.g. an orphaned block, the database has to be rebuild from block 0. This takes too long.
            We should therefore initiate a rebuild and do a failover instead. """

        try:
            sql = 'SELECT * FROM logs WHERE log_string like \'%Recreating memory tables%\'' + \
                    'AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\', datetime(\'now\', \'-30 seconds\'))) < datetime ORDER BY datetime DESC LIMIT 1'
            self.c.execute(sql)
            res = self.c.fetchall()
            if len(res) == 0:
                return False
        except Exception as e:
            print "Could not do bad memory check. Reason: %s" % e
        return True

    def failover(self):

        """ Return values:
            True: Disabled forging on local node, enabled forging on remote node.
            False: Could not disable forging on local node or enable forging on remote node.
            None: Exception thrown. """

        if self.config.get("failover", "this_node") == 'primary':
            ip = self.config.get("failover", "secondary_node")
        elif self.config.get("failover", "this_node") == 'secondary':
            ip = self.config.get("failover", "primary_node")
            
        try:
            data = {"secret": str(self.config.get("failover", "secret"))}
            headers = {'Content-Type': 'application/json'}

            url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/delegates/forging/disable'
            r = requests.post(url, data=json.dumps(data), headers=headers)
            res = r.json()

            if 'success' in res and res['success'] == True:
                print "Forging disabled on the local node (127.0.0.1)."
                url = 'http://' + str(ip) + ':' + (self.config.get("general", "api_port")) + '/api/delegates/forging/enable'
                r = requests.post(url, data=json.dumps(data), headers=headers)
                res = r.json()
                if 'success' in res and res['success'] == True:
                    print "Forging enabled on remote node (%s)" % str(ip)
                    return True
        except Exception as e:
            print "Could not commit failover. Reason: %s" % e
            return None
        return False
        
    def check_fork3(self):

        """ Return values:
        False: No fork type 3 detected within the specific time frame. 
        True: There was a fork type 3 within the specific timeframe
        None: Exception, we can not determine if a fork type 3 occurred. """

        try:
            sql = 'SELECT * FROM logs WHERE log_string LIKE \'%Fork%\' AND log_string LIKE \'%"cause":3%\' AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\',' + \
                    'datetime(\'now\', \'-20 seconds\'))) < datetime'
            self.c.execute(sql)
            if len(self.c.fetchall()) >= 1:
                return True
        except Exception as e:
            return None
        return False

    def stats(self):

        try:
            sql = 'SELECT COUNT(severity) FROM logs'
            self.c.execute(sql)
            num_lines = self.c.fetchall()
            if len(num_lines) >= 1:
                self.whos_forging()
                own_height = self.own_height()
                con_height = self.consensus_height()
                if own_height and con_height:
                    print "Local blockchain height: %s; Consensus blockchain height: %s." % \
                        (own_height, con_height)
                print "Log lines parsed: %i" % num_lines[0]
        except Exception as e:
            pass

