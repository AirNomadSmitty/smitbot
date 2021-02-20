from mysql.connector import connect, Error, MySQLConnection

class GeoContestResults():
    def __init__(self, geoContestResultId: int, geoContestId: int, userId: int, username: str, score: int):
        self.geoContestResultId = geoContestResultId
        self.geoContestId = geoContestId
        self.userId = userId
        self.username = username
        self.score = score

class GeoContestResultsMapper():
    def __init__(self, mysqlCon: MySQLConnection):
        self.conn = mysqlCon

    def create(self, geoContestId: int, username: str, score: int):
        sql = "INSERT INTO geo_contest_results (geo_contest_id, username, score) VALUES (%s, %s, %s)"
        cursor = self.conn.cursor()
        cursor.execute(sql, (geoContestId, username, score))
        self.conn.commit()

    def update(self, geoContestId: int, username: str, score: int):
        sql = """INSERT INTO geo_contest_results (geo_contest_id, username, score) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE score = %s"""
        cursor = self.conn.cursor()
        cursor.execute(sql, (geoContestId, username, score, score))
        self.conn.commit()


    def getFromGeoToken(self, geoToken: str):
        sql = """SELECT gcr.geo_contest_result_id, gcr.geo_contest_id, gcr.user_id, gcr.username, gcr.score
                FROM geo_contest_results gcr
                INNER JOIN geo_contests gc ON gcr.geo_contest_id = gc.geo_contest_id
                WHERE gc.geo_token = %s
                ORDER BY gcr.score DESC"""
        cursor = self.conn.cursor()
        cursor.execute(sql, (geoToken,))
        rows = cursor.fetchall()
        return self.makeFromRecords(rows)

    def makeFromRecords(self, rows: dict):
        contestResults = []
        for( geoContestResultId, geoContestId, userId, username, score ) in rows:
            contestResults.append(GeoContestResults(geoContestResultId, geoContestId, userId, username, score))
        return contestResults


