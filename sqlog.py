import requests
import subprocess
import sys
import os.path
import sqlite3
import ConfigParser
import re
import time

class SQLog(object):
 
   def consensus_height(self):

        heights = []
        ips = (self.config.get("general", "blockheight_nodes"))

        for ip in ips:
            url = 'http://' + str(ip) + ':' (self.config.get("general", "api_port")) + '/api/blocks/getHeight'
            try:
                http_req = requests.get(url)
                res = http_req.json()
            except Exception as e:
                pass
            if 'success' in res and res['success']:
                heights.append(res['height'])

        if len(heights) > 0:
            heights.sort()
            return heights[-1]
        return None

    def blockheight_low(self, consensus_height, own_height):

        """ Return values: 
            True: Node is syncing blocks
            False: Node is not syncing blocks """

        if consensus_height and own_height and \
            (int(own_height) <= int(consensus_height)-int(self.config.get("general", "block_offset"))):
            return True
        return False

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
            return None
        return False

    def own_blockheight(self):

        """ Return values: 
            height: as integer on success
            None: if no result is returned
            False: Exception """

        url = 'http://127.0.0.1:' + (self.config.get("general", "api_port")) + '/api/blocks/getHeight'
        try:
            http_req = requests.get(url)
            res = http_req.json()
            if 'success' in res and res['success']:
                height = res['height']
                return height
        except Exception as e:
            return False
        return None


    def restart(self):
        try:
            p = subprocess.Popen("/bin/bash", (self.config.get("paths", "management_script")), "reload",  stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            proc_status = p.wait()
            if proc_status == 0:
                return True
        except Exception as e:
            pass
        return False

    def rebuild(self):

        try:
            p = subprocess.Popen("/bin/bash", (self.config.get("paths", "management_script")), "rebuild",  stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()
            proc_status = p.wait()    
            if proc_status == 0:
                return True
        except Exception as e:
            pass
        return False

    def check_broadhash(self):

        """ Return values:
            False: broadhash consensus is bigger or equal to 51%
            True: Broadhash is lower than 51%
            None: Exception """
        try:
            sql = 'select * from logs where log_string like \'%Broadhash%\' and log_string not like \'%100%\'' + \
                'AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\', datetime(\'now\', \'-20 seconds\'))) < datetime order by datetime DESC LIMIT 1'
            self.c.execute(sql)
            res = self.c.fetchall()
            if len(res) >= 1 and len(res[0]) > 0:
                consensus = int(re.search(r'\d+', str(res[0][2])).group())
                if int(consensus) < 51:
                    return True
        except Exception as e:
            return None
        return False
        
    def check_fork3(self):

        """ Return values:
        False: No fork type 3 detected within the specific time frame. 
        True: There was a fork type 3 within the specific timeframe
        None: Exception """

        try:
            sql = 'SELECT * FROM logs WHERE log_string LIKE \'%Fork%\' AND log_string LIKE \'%"cause":3%\' AND (SELECT strftime(\'%Y-%m-%d %H:%M:%S\',' + \
                    'datetime(\'now\', \'-20 seconds\'))) < datetime'
            self.c.execute(sql)
            if len(self.c.fetchall()) >= 1:
                return True
        except Exception as e:
            return None
        return False
