## DO NOT USE YET, UNDER DEVELOPMENT.

## LISK/SHIFT monitoring software (Only LISK right now).

SQLog works as a monitoring software for LISK/SHIFT with a failover system. It also parse logs and inserts them into a SQLite3 database, hence the name SQLog. Since it uses a SQL-database as backend, it is very easy to create new events and actions.

## Supported events

SQLog enables high availability for LISK/SHIFT nodes. It can handle the following events.

| Event       | Action          |
| ------------- |:-------------:|
| Local node software is not running. | Try to start the local node software.|
| The node blockheight is low compared to network consensus | Failover and rebuild. Sends email if enabled.|
| The node experienced a fork of type 3 | Failover and rebuild. Sends email if enabled.|
|Broadhash consensus is either higher or lower than primary/secondary node|Failover|
|The blockchain database is corrupted|Failover and rebuild. Sends email if enabled.|

## Installation

1. `git clone https://github.com/shiftcurrency/sqlog.git`

2. Install python requests by using either python pip or apt (on debian based systems such as ubuntu).
   `apt-get install python-requests` or `pip install requests`

3. `Configure config.ini` in the sqlog directory. The configuration file is documented. OBSERVE, make sure you choose one server to be primary and one server to be secondary.

4. Start the software (in screen or similar) by executing sqlog.py, such as: ./sqlog.py

5. Make sure you white list the primary/secondary node IP-address in config.json for LISK/SHIFT as well as 127.0.0.1 on BOTH nodes.

## The End

If you like my work you can give my delegate a vote (joey on LISK) or give me a small contribution at 3791057246258751384L.

## License

    <SQLog, SHIFT/LISK monitoring system>
    Copyright (C) <2016>  <Joey (shiftcurrency@gmail.com)>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
