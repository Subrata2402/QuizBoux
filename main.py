import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
import aiohttp
import asyncio

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = "with Mimir Quiz!", url = "https://app.mimirquiz.com")
        await self.client.change_presence(activity=game)
        await self.start_ws_loop()
        
    @commands.command()
    @commands.is_owner()
    async def add(self, ctx, *, args):
        """Added a question in databse."""
        qa = args.split(" | ")
        question = qa[0]
        answer = qa[1]
        get_type = await self.add_question(question, answer)
        if get_type:
            await self.send_hook("**Successfully Added Question!**")
        else:
            await self.send_hook("**Already Added!**")
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def pay(self, ctx):
        """Pay Fees."""
        await self.pay_fees()
       
    @commands.command(aliases = ["p"])
    async def price(self, ctx, mimir:float = None):
        """Get or calculate current price of Mimir Token."""
        url = "https://api.coingecko.com/api/v3/coins/mimir-token"
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url) as response:
                if response.status != 200:
                    return await self.send_hook("**Something unexpected happened while fetching current price!**")
                if not mimir: mimir = 1.0
                data = await response.json()
                name = data.get("name")
                price = data.get("market_data").get("current_price").get("usd")
                usd = float("{:.2f}".format(price*mimir))
                price = data.get("market_data").get("current_price").get("inr")
                inr = float("{:.2f}".format(price*mimir))
                embed = discord.Embed(
                    color = discord.Colour.random(),
                    title = f"**__Current Price of {name}__**",
                    description = f"**ᛗ{mimir} ≈ ${usd} ≈ ₹{inr}**")
                await self.send_hook(embed = embed)
        
    @commands.command()
    async def addtoken(self, ctx, token):
        """Update Token."""
        await ctx.message.delete()
        url = "https://api.mimir-prod.com//games/list?type=both"
        headers = {
            "host": "api.mimir-prod.com",
            "authorization": f"Bearer {token}",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
            "content-type": "application/json",
            "accept": "*/*",
            "origin": "https://app.mimirquiz.com",
            "referer": "https://app.mimirquiz.com/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9"
            }
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url, headers = headers) as response:
                if response.status != 200:
                    return await self.send_hook("**The token has expired or invalid!**")
                update = {"token": token}
                db.token.update_one({"id": "3250"}, {"$set": update})
                await self.send_hook("**Token Successfully Updated!**")
        
    @commands.command()
    async def loop(self, ctx):
        """Start Websocket Loop."""
        if self.loop_is_active:
            await self.send_hook("**Loop Already Activated!**")
        else:
            await self.start_ws_loop()
        
    @commands.command(aliases = ["quiz", "mimir"])
    async def nextquiz(self, ctx, game_num:int = 1):
        """Get next quiz details."""
        await self.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx, time:int = 0):
        """Start Websocket."""
        await asyncio.sleep(time)
        if not self.ws_is_opened:
            await self.send_hook("**Websocket Opened!**")
            await self.start_hook()
        else:
            await self.send_hook("**Websocket Already Opened!**")
         
    @commands.command()
    async def close (self, ctx):
        """Close Websocket."""
        if self.ws_is_opened:
            await self.close_hook()
        else:
            await self.send_hook("**Websocket Already Closed!**")
        
    @commands.command()
    async def tq(self, ctx):
        """Get how many questions has stored in database."""
        questions = list(db.question_base.find())
        await self.send_hook(embed = discord.Embed(title = f"Total Questions : {len(questions)}", color = discord.Colour.random()))
    
intents = discord.Intents.all()
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents = intents)
client.add_cog(MimirQuiz(client))

@client.event
async def on_message(message):
    if not message.guild:
        return #await messag 08e.channel.send("**You cannot be used me in private messages.**")
    if message.guild.id != 935980609908658277:
    	return
    await client.process_commands(message)
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.OFUuud6gDHl5TYbcie3guwxPMI8")
