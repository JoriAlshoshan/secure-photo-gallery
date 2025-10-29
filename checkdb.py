import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()


#check users table
cur.execute("SELECT * FROM users")

# check images table
#cur.execute("SELECT * FROM images") 

users = cur.fetchall()

for user in users:
    print(user)

con.close()
