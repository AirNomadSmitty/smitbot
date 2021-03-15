from discord.ext import tasks, commands
import aiohttp
import pickle
from os import path
import time
from datetime import datetime, timedelta
from mappers.geoContestMapper import GeoContestMapper, GeoContest
from mappers.geoContestResultsMapper import GeoContestResultsMapper, GeoContestResults
from cogs.geoguessr.maps import MAPS


class GeoguessrCog(commands.Cog, ):
    def __init__(self, bot, email: str, password: str, cookieFile: str, geoContestMapper: GeoContestMapper, geoContestResultsMapper: GeoContestResultsMapper):
        self.bot = bot
        self.geoContestMapper = geoContestMapper
        self.geoContestResultsMapper = geoContestResultsMapper
        self.request = GeoguessrRequest(email, password, cookieFile)
        self.lastAction = time.time()
        self.lastCreated = None
        self.polling.start()
    

    def cog_unload(self):
        self.polling.cancel()

    @commands.command()
    async def geome(self, ctx, map: str='urban', options: str='mpz', seconds: int=0):
        """Generates link to a geoguessr challenge
        USAGE: !geome [map code | 'diverse' | 'urban'] [allowed move/pan/zoom (characters 'm', 'p', and/or 'z')] [time limit (seconds), optional]
        EXAMPLE: !geome urban MPZ
        EXAMPLE !geome 586446600eac72a13c2ce96c M 120"""
        if self.lastCreated is not None and datetime.now() - self.lastCreated < timedelta(minutes=2):
            await(ctx.send("Can only make a new challenge once every 2 minutes, sorry!"))
        else:
            # Options handling
            mapId = map
            forbidMoving = True
            forbidRotating = True
            forbidZooming = True

            if map.lower() in MAPS:
                mapId = MAPS[map]
            for char in options:
                if char.lower() == 'm':
                    forbidMoving = False
                elif char.lower() == 'p':
                    forbidRotating = False
                elif char.lower() == 'z':
                    forbidZooming = False

            r = await self.request.post('https://www.geoguessr.com/api/v3/challenges', {"map":mapId,"isCountryStreak":False,"forbidMoving":forbidMoving,"forbidRotating":forbidRotating,"forbidZooming":forbidZooming,"timeLimit":seconds})
            js = await r.json()
            token = js['token']
            self.geoContestMapper.create(token, ctx.channel.id)
            await ctx.send('https://www.geoguessr.com/challenge/' + token)
            self.lastCreated = datetime.now()
        self.toggleFastPolling(True)
        self.lastAction = time.time()
    

    @tasks.loop(minutes=1.0)
    async def polling(self):
        await self.bot.wait_until_ready()
        if time.time() - self.lastAction > 1800:
            self.toggleFastPolling(False)
        contests = self.geoContestMapper.getRecent(5)
        for contest in contests:
            r = await self.request.get('https://www.geoguessr.com/api/v3/results/scores/'+contest.geoToken+'/0/26')
            results = self.geoContestResultsMapper.getFromGeoToken(contest.geoToken)
            js = await r.json()
            if r.status == 200:
                if( len(js) > len(results) ):
                    self.lastAction = time.time()
                    self.toggleFastPolling(True)
                    for user in js:
                        self.geoContestResultsMapper.update(contest.geoContestId, user['playerName'], user['totalScore'])
                    results = self.geoContestResultsMapper.getFromGeoToken(contest.geoToken)
                    message = "New challenge finishers! Here's the current leaderboard for https://www.geoguessr.com/challenge/"+contest.geoToken+":"
                    for result in results:
                        message += "\n" + result.username + " " + str(result.score)
                    channel = self.bot.get_channel(contest.channelId)
                    if channel != None:
                        await channel.send(message)
            else:
                print(contest.geoToken)
                print(js)

    def toggleFastPolling(self, fastPolling: bool):
        if fastPolling:
            self.polling.change_interval(minutes=1.0)
        else:
            self.polling.change_interval(minutes=10.0)


class GeoguessrRequest():
    def __init__(self,email: str, password: str, cookieFile: str):
        self.email = email
        self.password = password
        self.cookieFile = cookieFile
        self.cookies = None
        if( not path.exists(self.cookieFile) ):
            with aiohttp.ClientSession() as session:
                with session.post('https://www.geoguessr.com/api/v3/accounts/signin', json={"email":self.email, "password":self.password}) as r:
                    self.cookies = r.cookies
                    with open(self.cookieFile, 'wb') as f:
                        pickle.dump(r.cookies, f)
        else:
            with open(self.cookieFile, 'rb') as f:
                self.cookies = pickle.load(f)

    async def post(self, url: str, json: dict):
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            return await session.post(url, json=json)
    
    async def get(self, url):
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            return await session.get(url)


    
