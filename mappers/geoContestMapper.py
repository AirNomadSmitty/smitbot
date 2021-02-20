from mysql.connector import connect, Error, MySQLConnection

class GeoContest():
    def __init__(self, geoContestId: int, geoToken: str, created: str, channelId: int):
        self.geoContestId = geoContestId
        self.geoToken = geoToken
        self.created = created
        self.channelId = channelId

class GeoContestMapper():
    def __init__(self, mysqlCon: MySQLConnection):
        self.conn = mysqlCon

    def create(self, token: str, channelId: int):
        sql = "INSERT INTO geo_contests (geo_token, channel_id) VALUES (%s, %s)"
        cursor = self.conn.cursor()
        cursor.execute(sql, (token, channelId,))
        self.conn.commit()

    def getRecent(self, limit: int):
        sql = """SELECT geo_contest_id, geo_token, created, channel_id FROM geo_contests
                WHERE created > NOW() - INTERVAL 7 DAY
                ORDER BY geo_contest_id DESC
                LIMIT %s"""
        cursor = self.conn.cursor()
        cursor.execute(sql, (limit,))
        rows = cursor.fetchall()
        return self.makeFromRecords(rows)

    def makeFromRecords(self, rows: dict):
        contests = []
        for( geoContestId, geoToken, created, channelId ) in rows:
            contests.append(GeoContest(geoContestId, geoToken, created, channelId))
        return contests


