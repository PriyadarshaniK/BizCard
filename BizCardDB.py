import pymysql

mydb = pymysql.connect(
  host="localhost",
  user="root",
  password="123456789"
)

mycursor = mydb.cursor()

mycursor.execute("CREATE DATABASE IF NOT EXISTS bizcarddb")

mydb = pymysql.connect(
  host="localhost",
  user="root",
  password="123456789",
  database="bizcarddb"
)

mycursor = mydb.cursor()


#create tables in bizcarddb
# Card Details table
mycursor.execute("""CREATE TABLE IF NOT EXISTS card_details 
                    (id INT AUTO_INCREMENT PRIMARY KEY,
                    company_name VARCHAR(50), 
                    card_holder VARCHAR(50),
                    designation VARCHAR(50),
                    mobile_number VARCHAR(50), 
                    email VARCHAR(50), 
                    website VARCHAR(50), 
                    area VARCHAR(50),
                    city VARCHAR(50),
                    state VARCHAR(50),
                    pin_code VARCHAR(10),
                    image MEDIUMBLOB)"""
                )
