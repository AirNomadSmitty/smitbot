import discord
from discord.ext import tasks, commands
import random
import aiohttp
from mysql.connector import connect, Error
from cogs.geoguessr.geoguessrCog import GeoguessrCog
from mappers.geoContestMapper import GeoContestMapper
from mappers.geoContestResultsMapper import GeoContestResultsMapper
from configparser import RawConfigParser


description = '''Smitty's first bot :)'''

intents = discord.Intents.default()
intents.members = True

config = RawConfigParser()
config.read("config.ini")

bot = commands.Bot(command_prefix='!', description=description, intents=intents)
try:
    mysqlCon = connect(
        host=config['mysql']['host'],
        user=config['mysql']['user'],
        password=config['mysql']['password'],
        database=config['mysql']['database'],)
except Error as e:
        print(e)

bot.add_cog(GeoguessrCog(bot, 
config['geoguessr']['email'], 
config['geoguessr']['password'], 
config['geoguessr']['auth_cookie_file'], 
GeoContestMapper(mysqlCon), 
GeoContestResultsMapper(mysqlCon)))
                
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def sporcleme(ctx):
    """Generates a link to a random sporcle quiz"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.sporcle.com/games/random.php", skip_auto_headers={"User-Agent"},allow_redirects=False, ) as r:
            await ctx.send("https://www.sporcle.com"+r.headers["Location"])


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))

@bot.command()
async def repeat(ctx, times: int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await ctx.send(content)

@bot.command()
async def hypeme(ctx):
    """Hypes you!"""
    num = random.randrange(12)
    if num == 5:
        await ctx.send("{} nah".format(ctx.author.mention))
    else:
        await ctx.send("{} LET'S GOOOOO!!!!!".format(ctx.author.mention))

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send('{0.name} joined in {0.joined_at}'.format(member))

# @bot.command()
# async def gasmeupfam(ctx, member: discord.Member):


@bot.group()
async def cool(ctx):
    """Says if a user is cool.
    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))

@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')

bot.run(config['discord']['token'])
