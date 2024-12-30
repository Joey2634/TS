from configs.Database import Database, AI_DB, DEV, WIND_DB


def updateAHRelation(env=DEV):
    wind = Database(WIND_DB)
    wind.cursor.execute("select s_info_windcode,s_info_windcod2 from wind.shszrelatedsecurities")
    data = wind.cursor.fetchall()
    DB = Database(AI_DB[env])
    DB.cursor.execute("delete from AH_related")
    DB.cursor.executemany("insert into AH_related values(%s,%s)", list(data))
    DB.conn.commit()

if __name__ == '__main__':
    updateAHRelation()