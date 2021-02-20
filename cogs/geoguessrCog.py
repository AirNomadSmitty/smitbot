from discord.ext import tasks, commands
import aiohttp
import pickle
from os import path
from datetime import datetime, timedelta
from mappers.geoContestMapper import GeoContestMapper, GeoContest
from mappers.geoContestResultsMapper import GeoContestResultsMapper, GeoContestResults

class GeoguessrCog(commands.Cog, ):
    def __init__(self, bot, email: str, password: str, cookieFile: str, geoContestMapper: GeoContestMapper, geoContestResultsMapper: GeoContestResultsMapper):
        self.bot = bot
        self.geoContestMapper = geoContestMapper
        self.geoContestResultsMapper = geoContestResultsMapper
        self.email = email
        self.password = password
        self.lastCreated = None
        self.cookies = None
        self.cookieFile = cookieFile
        if( not path.exists(cookieFile) ):
            with aiohttp.ClientSession() as session:
                with session.post('https://www.geoguessr.com/api/v3/accounts/signin', json={"email":email, "password":password}) as r:
                    self.cookies = r.cookies
                    with open(cookieFile, 'wb') as f:
                        pickle.dump(r.cookies, f)
                    self.polling.start()

        else:
            with open(cookieFile, 'rb') as f:
                self.cookies = pickle.load(f)
                self.polling.start()
    

    def cog_unload(self):
        self.polling.cancel()

    @commands.command()
    async def geome(self, ctx):
        """Generates link to a geoguessr challenge"""
        if self.lastCreated is not None and datetime.now() - self.lastCreated < timedelta(minutes=2):
            await(ctx.send("Can only make a new challenge once every 2 minutes, sorry!"))
        else:
            async with aiohttp.ClientSession(cookies=self.cookies) as session:
                async with session.post('https://www.geoguessr.com/api/v3/challenges', json={"map":"59a1514f17631e74145b6f47","isCountryStreak":False,"forbidMoving":False,"forbidRotating":False,"forbidZooming":False,"timeLimit":150}) as r:
                    js = await r.json()
                    token = js['token']
                    self.geoContestMapper.create(token, ctx.channel.id)
                    await ctx.send('https://www.geoguessr.com/challenge/' + token)
                    self.lastCreated = datetime.now()
    

    @tasks.loop(seconds=45.0)
    async def polling(self):
        await self.bot.wait_until_ready()
        print("polling")
        contests = self.geoContestMapper.getRecent(5)
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
                for contest in contests:
                    results = self.geoContestResultsMapper.getFromGeoToken(contest.geoToken)
                    async with session.get('https://www.geoguessr.com/api/v3/results/scores/'+contest.geoToken+'/0/26') as r:
                        js = await r.json()
                        if r.status != 401:
                            if( len(js) > len(results) ):
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