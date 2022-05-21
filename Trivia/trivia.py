import discord, aiohttp, asyncio, socket
from discord.ext import commands
from Websocket.mimir_ws import MimirWebSocket
from Websocket.display_ws import DisplayWebSocket
from Websocket.hq_ws import HQWebSocket
from database import db

class TriviaClass(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Trivia Cog is Ready!")
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def getvideo(self, ctx):
        url = "https://media.discordapp.net/attachments/799861610654728212/968092655932289024/VID-20220425-WA0004.mp4"
        with open("Video/VID-20220425-WA0004.mp4", "rb") as f:
            file = discord.File(f, filename = "How-to-get-Mimir-Quiz-Authorization-Token.mp4", spoiler = False)
            embed = discord.Embed(title = "__HttpCanary Apk Download Link :__", description = "https://m.apkpure.com/httpcanary-%E2%80%94-http-sniffer-capture-analysis/com.guoshi.httpcanary/download?from=amp_info", color = discord.Colour.random())
            await ctx.send(file = file, embed = embed)
    
    @commands.command(aliases = ["p"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def price(self, ctx, mimir:float = None):
        """Get or calculate current price of Mimir Token."""
        ws = Websocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        url = "https://api.coingecko.com/api/v3/coins/mimir-token"
        async with aiohttp.ClientSession() as session:
            response = await session.get(url = url)
            if response.status != 200:
                return await ws.send_hook("Something unexpected happened while fetching current price!")
            if not mimir: mimir = 1.0
            data = await response.json()
            name = data.get("name")
            price = data.get("market_data").get("current_price").get("usd")
            usd = float("{:.2f}".format(price*mimir))
            price = data.get("market_data").get("current_price").get("inr")
            inr = float("{:.2f}".format(price*mimir))
            embed = discord.Embed(
                color = discord.Colour.random(),
                title = f"__Current Price of {name}__",
                description = f"ᛗ{mimir} ≈ ${usd} ≈ ₹{inr}")
            await ws.send_hook(embed = embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def addhqtoken(self, ctx, *, token = None):
        """Add or update Token."""
        if "HQ Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `HQ Access` role to run this command!")
        if not token: return await ctx.reply(ctx.author.mention + ", You didn't enter token.")
        ws = HQWebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for HQ Trivia.")
        token = token.strip("Bearer").strip()
        await ws.is_expired(token)
        update = {"token": token}
        db.hq_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ws.send_hook("Token Successfully Updated!")
        await ctx.message.delete()
    
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def addtoken(self, ctx, *, token = None):
        """Add or update Token."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        if not token: return await ctx.reply(ctx.author.mention + ", You didn't enter token.")
        ws = MimirWebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        token = token.strip("Bearer").strip()
        await ws.get_quiz_details()
        await ws.get_access_token(token)
        update = {"token": token}
        db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ws.send_hook("Token Successfully Updated!")
        await ctx.message.delete()
        
    @commands.command(aliases = ["quiz", "mimir"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    async def nextquiz(self, ctx, game_num:int = 1):
        """Get next quiz details."""
        ws = MimirWebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        await ws.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command()
    @commands.guild_only()
    async def login(self, ctx, username = None, password = None):
        """Login to Display."""
        if "Display Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
        if not username or not password:
            return await ctx.reply(ctx.author.mention + ", You didn't mention username or password.\n```\n{}{} [username] [password]\n```".format(ctx.prefix, ctx.command.name))
        ws = DisplayWebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Display Trivia.")
        response = await ws.get_sub_protocol(username, password)
        if not response: return await ctx.reply(ctx.author.mention + ", Enter username or password is incorrect! If you enter all right details then try again after some times.")
        update = {"username": username, "password": password}
        db.display_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ctx.reply(ctx.author.mention + ", You have successfully login to Display!")
        await ctx.message.delete()
    
    @commands.command(aliases = ["open"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.guild_only()
    async def start(self, ctx, trivia = "mimir", demo = None):
        """Start Websocket."""
        if trivia.lower() == "mimir":
            if "Mimir Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
            ws = MimirWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
            if not ws.is_ws_open:
                await ws.send_hook("Websocket Opened!")
                await ws.start_hook()
            else:
                await ws.send_hook("Websocket Already Opened!")
        elif trivia.lower() == "display":
            if "Display Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
            ws = DisplayWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
            await ws.get_ws()
            if ws.ws:
                if ws.ws.open:
                    return await ws.send_hook("Websocket Already Opened!")
            await ws.send_hook("Websocket Opened!")
            await ws.connect_ws()
        elif trivia.lower() == "hq":
            if "HQ Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `HQ Access` role to run this command!")
            ws = HQWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
            await ws.get_ws()
            if ws.ws:
                if ws.ws.open:
                    return await ws.send_hook("Websocket Already Opened!")
            await ws.send_hook("Websocket Opened!")
            await ws.connect_ws(demo)
        else:
            await ctx.reply(ctx.author.mention + ', Please mention between `Display` or `Mimir`!')
         
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def close (self, ctx, trivia = "mimir"):
        """Close Websocket."""
        if trivia.lower() == "mimir":
            if "Mimir Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
            ws = MimirWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
            if ws.is_ws_open:
                await ws.close_hook()
            else:
                await ws.send_hook("Websocket Already Closed!")
        elif trivia.lower() == "display":
            if "Display Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
            ws = DisplayWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
            await ws.close_ws()
        elif trivia.lower() == "hq":
            if "HQ Access" not in [role.name for role in ctx.author.roles]:
                return await ctx.reply(ctx.author.mention + ", You need `HQ Access` role to run this command!")
            ws = HQWebSocket(guild_id = ctx.guild.id, client = self.client)
            web_url = await ws.get_web_url()
            if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
            await ws.close_ws()
        else:
            await ctx.reply(ctx.author.mention + ', Please mention between `Display` or `Mimir`!')
        
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setup(self, ctx, trivia = "mimir", channel: discord.TextChannel = None):
        """Setup mimir quiz channel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.reply(ctx.author.mention + ", You don't have enough permission to run this command!")
        if not channel: channel = ctx.channel
        if trivia.lower() == "mimir":
            webhook = await channel.create_webhook(name = "Mimir Quiz")
            check = db.mimir_details.find_one({"guild_id": ctx.guild.id})
            if check:
                update = {"web_url": webhook.url}
                db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            else:
                db.mimir_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "token": "eyJraWQiOiJYS1wvRlBZOFlcL1lJejV1VHJSSEdhOTZ6VHp0M1lWTlwvR25UQ0JrMitlbXNNPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI1ZTliNTY5YS0wNDIzLTQ4ODMtOTAyZS05YTQxYjM4YjJhYzQiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfME93Q2RwclNoIiwiY29nbml0bzp1c2VybmFtZSI6ImJlcm5mcmllZDMyNTBtZXllckBnbWFpbC5jb20iLCJvcmlnaW5fanRpIjoiMGVkYjIyZjQtNDBmMC00MjUwLWI0NzMtMzE3MzUwMzRiNWNkIiwiYXVkIjoiMnN1MG1qY3JqcXN2amlwZTYyYThnY281NDYiLCJldmVudF9pZCI6ImI2MDQ2OTcyLWFjMDYtNDJkYS04MzYyLTYzYWM2ZjNkNWFiMCIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNjUwMDQzNzkyLCJleHAiOjE2NTAwNDczOTIsImlhdCI6MTY1MDA0Mzc5MiwianRpIjoiMTFjMDFhMTgtYTQyMS00MjVmLTk4N2ItNGY5ZDliZGJjZDk5IiwiZW1haWwiOiJiZXJuZnJpZWQzMjUwbWV5ZXJAZ21haWwuY29tIn0.P6DjqvX_BqT60wliNRFg38RjE7AIU4yyCYv3eh8ShmlN7jO5THvuQp8h5hfa7Oss49xNytPZE7Dk74tEcNgI7QLTKI5_-xDZUGLCvGDenfCtiAK6TKYMgzOWjOVzS3LiCXNLAVjgKTBmq5iOehQPz1XN7Wvxq7cn7xMgnD1XXtJ4i5-jjI4DSpC6gnDSIEUfqpfm3pGv14R_HrIM5-6arWaZuxyPWBywh7fDmh1F5Z47dBd9gDFNR2LKFM1fFcn8-EVtl83FazRUJUO1l_KIio8Z1Awki0O-KvAfX0xGY7HkrFqZd_CdJY93eKHWR0qZZj-fdcq1BVtqyPsp76VlFQ:0xFCCd91Ca80bbf04da2Af2AA9E5569fdA28843D2E"})
            embed = discord.Embed(title = "Mimir Quiz Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            if channel != ctx.channel: await ctx.reply(ctx.author.mention + ", You have successfully setup Mimir Quiz Channel.")
        elif trivia.lower() == "display":
            webhook = await channel.create_webhook(name = "Display Trivia")
            check = db.display_details.find_one({"guild_id": ctx.guild.id})
            if check:
                update = {"web_url": webhook.url}
                db.display_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            else:
                db.display_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "username": None, "password": None,"subscription": False})
            embed = discord.Embed(title = "Display Trivia Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            if channel != ctx.channel: await ctx.reply(ctx.author.mention + ", You have successfully setup Display Trivia Channel.")
        elif trivia.lower() == "hq":
            webhook = await channel.create_webhook(name = "HQ Trivia")
            check = db.hq_details.find_one({"guild_id": ctx.guild.id})
            if check:
                update = {"web_url": webhook.url}
                db.hq_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            else:
                db.hq_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "token": "eyZjskiehnjmeh.jeinfmg", "subscription": False})
            embed = discord.Embed(title = "HQ Trivia Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            if channel != ctx.channel: await ctx.reply(ctx.author.mention + ", You have successfully setup HQ Trivia Channel.")
        else:
            await ctx.reply(ctx.author.mention + ', Please mention between `Display` or `Mimir` or `HQ`!')

def setup(client):
    client.add_cog(TriviaClass(client))
