import mysql.connector
import time

import mysql.connector

class DBManager:
    def __init__(self, tunnel=False):
        self.host = "allegrotradedb.proxy-cj4ujco21i0x.eu-central-1.rds.amazonaws.com"
        self.user = "admin"
        self.password = "xCNxyM9nf8pHyyCY"
        self.database = "sales-data"

        self.ssh_host = "ec2-3-120-12-175.eu-central-1.compute.amazonaws.com"
        self.ssh_username = "ec2-user"
        self.ssh_phkey = "pairpem.pem"
        self.ssh_port = 22

        self.tunnel = tunnel


    def openConnection(self):
        if self.tunnel:
            with sshtunnel.SSHTunnelForwarder(
                    (self.ssh_host, self.ssh_port),
                    ssh_username=self.ssh_username,
                    ssh_pkey=self.ssh_phkey,
                    remote_bind_address=(self.host, 3306),
            ) as tunnel:
                return mysql.connector.connect(
                        host=self.host,
                        user=self.user,
                        port=tunnel.local_bind_port,
                        password=self.password,
                        database=self.database,
                        allow_local_infile=True,
                        connect_timeout=20)
        else:
            return mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                allow_local_infile=True,
                connect_timeout=200)


    def saveProxies(self):
        database = self.openConnection()
        with open("proxies.txt") as f:
            content = f.readlines()
        mycursor = database.cursor()
        for i in content:
            i = i.replace("\n", "")
            sql = "INSERT INTO proxy (proxy_string,active) VALUES (%s, %s)"
            val = (i, 1)
            mycursor.execute(sql, val)
            database.commit()
        mycursor.close()
        database.close()

    def getActiveProxies(self):
        database = self.openConnection()
        mycursor = database.cursor()
        sql = "SELECT proxy_string FROM proxy WHERE active = 1;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mycursor.close()
        database.close()

        proxy_string = []
        for x in myresult:
            proxy_string.append(x[0])
        return proxy_string

    def randomProxy(self, Retries=0, Cursor=None):
        database = self.openConnection()
        if (Cursor is None):
            mycursor = database.cursor()
        else:
            mycursor = Cursor
        sql = "SELECT randomProxy();"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        database.commit()
        mycursor.close()
        database.close()

        if len(myresult) == 0 or myresult[0][0] == "":
            time.sleep(1)
            print(f"Couldn't get proxy. Retrying. ({Retries + 1})")
            return self.randomProxy(Retries=Retries + 1, Cursor=mycursor)
        else:
            return myresult[0][0]

    def getProxyFromFIFO(self):
        database = self.openConnection()
        mycursor = database.cursor()
        sql = 'SELECT getProxy()'
        mycursor.execute(sql)
        result = mycursor.fetchone()
        database.commit()
        mycursor.close()
        database.close()

        if (len(result) > 0):
            return result[0]
        else:
            return None

    def saveCategoryTo(self,filename):
        database = self.openConnection()
        mycursor = database.cursor()
        sql = f"LOAD DATA LOCAL INFILE '{filename}' INTO TABLE `category-tmp`;"
        mycursor.execute(sql)
        mycursor.execute('SET FOREIGN_KEY_CHECKS=0')
        sql = "INSERT INTO `category` (`id`,`name`,`estimated-amount`,`parent-id`) " \
              "SELECT `category-tmp`.`id`,`category-tmp`.`name`,`category-tmp`.`estimated-amount`,`category-tmp`.`parent-id` " \
              "FROM `category-tmp` " \
              "ON DUPLICATE KEY UPDATE `category`.`name` = `category-tmp`.`name`, `category`.`estimated-amount`=`category-tmp`.`estimated-amount` ,`category`.`parent-id` = `category-tmp`.`parent-id`;"
        mycursor.execute(sql)
        sql = "DELETE FROM `category-tmp` WHERE 1=1;"
        mycursor.execute(sql)
        mycursor.execute('SET FOREIGN_KEY_CHECKS=1')
        database.commit()
        mycursor.close()

    def saveOffers(self, file):
        database = self.openConnection()
        mycursor = database.cursor()
        mycursor.execute('SET FOREIGN_KEY_CHECKS=0')
        sql = f"LOAD DATA LOCAL INFILE '{file}' INTO TABLE `offer`;"
        mycursor.execute(sql)
        mycursor.execute('SET FOREIGN_KEY_CHECKS=1')
        database.commit()
        mycursor.close()
        database.close()

    def getCategories(self):
        database = self.openConnection()
        mycursor = database.cursor()
        sql = "SELECT id from category WHERE id NOT IN (SELECT `parent-id` FROM category)"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mycursor.close()
        database.close()
        ids = []
        for i in myresult:
            ids.append(i[0])
        return ids

    def getAPICredentials(self):
        database = self.openConnection()
        mycursor = database.cursor()
        mycursor.execute("SELECT getAPICredentials();")
        result = mycursor.fetchone()
        database.commit()
        mycursor.close()
        database.close()
        if len(result) > 0:
            return result[0]
        else:
            return None
