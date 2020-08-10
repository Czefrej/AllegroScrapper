import mysql.connector

class DBManager:
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host="database-2.cj4ujco21i0x.eu-central-1.rds.amazonaws.com",
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

    def getActiveProxies(self):
        mycursor = self.mydb.cursor()
        sql = "SELECT proxy_string FROM proxy WHERE active = 1;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        proxy_string = []
        for x in myresult:
            proxy_string.append(x[0])
        return proxy_string


    def saveCategoryTo(self):
        mycursor = self.mydb.cursor()
        sql = "LOAD DATA LOCAL INFILE 'categories.csv' INTO TABLE category;"
        mycursor.execute(sql)
        self.mydb.commit()

    def getCategories(self):
        mycursor = self.mydb.cursor()
        sql = "SELECT id FROM category;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        ids = []
        for x in myresult:
            ids.append(x[0])
        return ids