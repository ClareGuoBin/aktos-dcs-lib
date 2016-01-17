from gevent import monkey;monkey.patch_socket()
import datetime
from aktos_dcs import *

try:
    import MySQLdb
except ImportError:
    print """
    in order to install MySQLdb:

        apt-get install python-dev libmysqlclient-dev
        pip install MySQL-python
    """
    raise

class DatabaseActor(Actor):
    def __init__(self, host="localhost", port=3306, user="root", passwd='', db=''):
        Actor.__init__(self)
        self.conn_params = [host, port, user, passwd, db]
        self.conn_retry_count = 0
        self.cur = None

        self.try_to_connect()

    def connect(self, host="localhost", port=3306, user="root", passwd='', db='', conn_params = []):

        if conn_params:
            host, port, user, passwd, db = conn_params

        if port != 3306 and host == "localhost":
            host = '127.0.0.1'

        #print "connecting..."
        self.db = MySQLdb.connect(
                host=host,       # your host, usually localhost
                port=port,              # port
                user=user,       # your username
                passwd=passwd,     # your password
                db=db)         # name of the data base

        #print "getting cursor..."
        self.cur = self.db.cursor()

        #print "connection done..."

    def try_to_connect(self):
        for i in range(3):
            if not self.cur:
                print "INFO: CONNECTION MIGHT BE LOST, RETRYING..."
                self.connect(conn_params = self.conn_params)
                self.conn_retry_count += 1
            else:
                break

    def run_query(self, query):
        self.try_to_connect()

        max_retry_query = 10 
        for i in range(max_retry_query): 
            try:
                self.cur.execute(query)
                self.db.commit()

                output = []
                while True:
                    row = self.cur.fetchone()
                    if not row:
                        break
                    print "Output:\t\t", row
                    output.append(row)
                return output
            except Exception as e:
                print "problem, rolling back... msg: ", e
                try:
                    self.db.rollback()
                except: 
                    print "Exception while rolling back..."
                finally: 
                    self.try_to_connect()

    def cleanup(self):
        self.cur.close()


class Test(Actor):
    pass

if __name__ == "__main__":
    from aktos_parser import AktosConfig
    cfg = AktosConfig(config_file='mysql_driver_config.md')
    d = cfg.flat_dict()

    host = d['cici-meze.proxy-server.host']
    port = d['cici-meze.proxy-server.port']
    user = d['cici-meze.user']
    passwd = d['cici-meze.passwd']
    db = d['cici-meze.db']

    #print host, port, user, passwd, db

    DatabaseActor(host=host, port=port, user=user, passwd=passwd, db=db)
    t = Test()
    while True:
        print "send query message..."
        query = "select * from sensors"
        t.send({'RunSQL': {'query': query}})
        sleep(5)

    i = 0
    while True:
        i += 1
        print "send query message..."
        query = "insert into sensors (pin_name, type) values ('test-pin-name-%d', 'temp')" % (i)
        t.send({'RunSQL': {'query': query}})
        sleep(5)

    wait_all()
