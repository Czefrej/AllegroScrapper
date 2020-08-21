import mysql.connector
import time
class DBManager:
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host="scrapper-data.cj4ujco21i0x.eu-central-1.rds.amazonaws.com",
            user="admin",
            password="GedoMazo123",
            database="sales-data",
            allow_local_infile=True
        )

    def saveProxies(self):
        with open("proxies.txt") as f:
            content = f.readlines()
        mycursor = self.mydb.cursor()
        for i in content:
            i = i.replace("\n","")
            sql = "INSERT INTO proxy (proxy_string,active) VALUES (%s, %s)"
            val = (i, 1)
            mycursor.execute(sql, val)
            self.mydb.commit()
        mycursor.close()

    def getActiveProxies(self):
        mycursor = self.mydb.cursor()
        sql = "SELECT proxy_string FROM proxy WHERE active = 1;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mycursor.close()

        proxy_string = []
        for x in myresult:
            proxy_string.append(x[0])
        return proxy_string


    def randomProxy(self,Retries = 0, Cursor = None):
        if(Cursor is None):
            mycursor = self.mydb.cursor()
        else:
            mycursor = Cursor
        sql = "SELECT randomProxy();"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        if len(myresult) == 0 or myresult[0][0] == "":
            time.sleep(1)
            print(f"Couldn't get proxy. Retrying. ({Retries+1})")
            return self.randomProxy(Retries=Retries+1, Cursor=mycursor)
        else:
            mycursor.close()
            return myresult[0][0]


    def saveCategoryTo(self):
        mycursor = self.mydb.cursor()
        sql = "LOAD DATA LOCAL INFILE 'categories.csv' INTO TABLE `category-tmp`;"
        mycursor.execute(sql)
        mycursor.execute('SET FOREIGN_KEY_CHECKS=0')
        sql = "INSERT INTO `category` (`id`,`name`,`parent-id`) " \
              "SELECT `category-tmp`.`id`,`category-tmp`.`name`,`category-tmp`.`parent-id` " \
              "FROM `category-tmp` " \
              "ON DUPLICATE KEY UPDATE `category`.`name` = `category-tmp`.`name`, `category`.`parent-id` = `category-tmp`.`parent-id`;"
        mycursor.execute(sql)
        sql = "DELETE FROM `category-tmp` WHERE 1=1;"
        mycursor.execute(sql)
        mycursor.execute('SET FOREIGN_KEY_CHECKS=1')
        self.mydb.commit()
        self.mydb.close()

    def getCategories(self):
        mycursor = self.mydb.cursor()
        sql = "SELECT id from category WHERE id NOT IN (SELECT `parent-id` FROM category GROUP BY `parent-id`)"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mycursor.close()
        ids = []
        for i in myresult:
            ids.append(i[0])
        return ids