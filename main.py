import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
import aiohttp
import asyncio

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        super().__init__(client)
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = "with Mimir Quiz!", url = "https://app.mimirquiz.com")
        await self.client.change_presence(activity=game)
        
    @commands.command(hidden = True)
    @commands.is_owner()
    async def add(self, ctx, *, args):
        """Added a question in databse."""
        if ctx.guild.id != 935980609908658277:
            return
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
        if ctx.guild.id != 935980609908658277:
            return
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
                if ctx.guild.id != 935980609908658277:
                    return await ctx.send(embed = embed)
                await self.send_hook(embed = embed)
        
    @commands.command()
    async def addtoken(self, ctx, *, token = None):
        """Update Token."""
        if ctx.guild.id != 935980609908658277:
            return
        if not token: return
        await ctx.message.delete()
        token = token.strip("Bearer").strip()
        await self.get_quiz_details()
        await self.get_access_token(token)
        update = {"token": token}
        db.token.update_one({"id": "3250"}, {"$set": update})
        await self.send_hook("**Token Successfully Updated!**")
        
    @commands.command(aliases = ["quiz", "mimir"])
    async def nextquiz(self, ctx, game_num:int = 1):
        """Get next quiz details."""
        if ctx.guild.id != 935980609908658277:
            url = "https://api.mimir-prod.com//games/next?"
            async with aiohttp.ClientSession() as session:
                async with session.get(url = url) as response:
                    if response.status != 200:
                        return await ctx.send("**Something Unexpected happened while fetching quiz details!**")
                    r = await response.json()
                    data = r["data"]["data"]
                    if len(data) < game_num:
                        return await ctx.send("**Quiz Not Found!**")
                    data = data[game_num-1]
                    icon_url = data.get("previewImageUrl") or data.get("backgroundImageLandscapeUrl")
                    topic = data["label"]
                    description = data.get("description")
                    prize = data["reward"]
                    time = f'<t:{int(data["scheduled"]/1000)}>'
                    gameType = data["winCondition"]
                    value = data.get("entryFee")
                    embed = discord.Embed(
                        title = "**__Mimir Upcoming Quiz Details !__**",
                        description = description,
                        color = discord.Colour.random(),
                        )
                    #timestamp = datetime.datetime.utcnow()
                    embed.add_field(name = "Quiz Topic :", value = topic, inline = False)
                    embed.add_field(name = "Prize Money :", value = f"ᛗ{prize}", inline = False)
                    if value: embed.add_field(name = "Entry Fee :", value = f"ᛗ{value}", inline = False)
                    embed.add_field(name = "Date & Time :", value = time, inline = False)
                    embed.set_footer(text = f"Upcoming Quiz No. - {'0' if game_num < 10 else ''}{game_num}")
                    embed.set_thumbnail(url = icon_url)
                    #await self.send_hook(embed = embed)
                    return await ctx.send(embed = embed)
        await self.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx, time:int = 0):
        """Start Websocket."""
        if ctx.guild.id != 935980609908658277:
            return
        await asyncio.sleep(time)
        if not self.ws_is_opened:
            await self.send_hook("**Websocket Opened!**")
            await self.start_hook()
        else:
            await self.send_hook("**Websocket Already Opened!**")
         
    @commands.command()
    async def close (self, ctx):
        """Close Websocket."""
        if ctx.guild.id != 935980609908658277:
            return
        if self.ws_is_opened:
            await self.close_hook()
        else:
            await self.send_hook("**Websocket Already Closed!**")
        
    @commands.command()
    async def tq(self, ctx):
        if ctx.guild.id != 935980609908658277:
            return
        """Get how many questions has stored in database."""
        questions = list(db.question_base.find())
        await self.send_hook(embed = discord.Embed(title = f"Total Questions : {len(questions)}", color = discord.Colour.random()))
    
intents = discord.Intents.all()
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents = intents)
client.add_cog(MimirQuiz(client))
client.remove_command("help")

@client.event
async def on_message(message):
    if not message.guild:
        return #await messag 08e.channel.send("**You cannot be used me in private messages.**")
    await client.process_commands(message)
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.Qt4OvfOh7YZhH5hPoQzd7iatWGc")
