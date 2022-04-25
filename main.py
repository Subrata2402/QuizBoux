import discord, aiohttp, asyncio, socket
from discord.ext import commands
from Websocket.ws import Websocket
from database import db

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = f"with Mimir Quiz in {str(len(self.client.guilds))} guilds", url = "https://app.mimirquiz.com")
        await self.client.change_presence(activity=game)
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"):
            return
        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandOnCooldown):
            seconds = float("{:.2f}".format(error.retry_after))
            wait_time = f"```{'0' if seconds < 10 else ''}{seconds} second{'s' if seconds != 1 else ''}```"
            description = ctx.author.mention + ", This command is on cooldown, please retry after " + wait_time + "!"
            return await ctx.reply(description)
        print(error)
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gettokenmethod(self, ctx):
        url = "https://media.discordapp.net/attachments/799861610654728212/968092655932289024/VID-20220425-WA0004.mp4"
        with open("Video/VID-20220425-WA0004.mp4", "rb") as f:
            file = discord.File(f, filename = "How to get Mimir Quiz Authorization Token?", spoiler = True)
            await ctx.send(file = file, content = "> **__HttpCanary Apk Link :** https://m.apkpure.com/httpcanary-%E2%80%94-http-sniffer-capture-analysis/com.guoshi.httpcanary/download?from=amp_info")
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invite(self, ctx):
        """Get an invite link of bot."""
        embed = discord.Embed(title = "Invite me to your server.",
            url = f"https://discord.com/api/oauth2/authorize?client_id={self.client.user.id}&permissions=523376&scope=bot",
            color = discord.Colour.random())
        await ctx.reply(content = ctx.author.mention, embed = embed)
    
    @commands.command(
        name = "botlv",
        description = "Leave a guild.",
        aliases = [],
        usage = "[guild_id] (reason)",
        brief = "9838828292928388383 For abuse of the bot.",
        hidden = True
        )
    @commands.is_owner()
    async def _leave(self, ctx, guild_id:int, *, reason = None):
        guild = self.client.get_guild(guild_id) or (await self.client.fetch_guild(guild_id))
        if not guild: return await ctx.send("Bot is not in this Guild!")
        await guild.leave()
        await ctx.send(f"Successfully left from **{guild.name}**!")
        if reason:
            try:
                await guild.owner.send(reason)
                await ctx.send(f"Successfully send dm to **{guild.owner}**!")
            except:
                await ctx.send(f"Failed to send dm to guild owner **{guild.owner}**.")
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def ip(self, ctx):
        #import socket
        ## getting the hostname by socket.gethostname() method
        hostname = socket.gethostname()
        ## getting the IP address using socket.gethostbyname() method
        ip_address = socket.gethostbyname(hostname)
        ## printing the hostname and ip_address
        print(f"Hostname: {hostname}")
        print(f"IP Address: {ip_address}")
        await ctx.send(f"IP Address : `{ip_address}`")
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def sl(self, ctx):
        servers = self.client.guilds
        members = list(set([guild.member_count for guild in servers]))
        member_list = sorted(members, reverse=True)
        embed = discord.Embed()
        for index, member_count in enumerate(member_list):
            if index >= 22:
                break
            for guild in servers:
                if member_count == guild.member_count:
                    embed.add_field(name=f"{'0' if index+1 < 10 else ''}{index+1}. {guild.name}", value=f"Guild Owner : {guild.owner}\nGuild Members : {guild.member_count}\nGuild ID : {guild.id}")
        await ctx.send(embed=embed)
        
    @commands.command(hidden = True)
    @commands.is_owner()
    async def get_token(self, ctx, guild_id:int):
        token = db.mimir_details.find_one({"guild_id": guild_id}).get("token")
        await ctx.send(f"```\n{token}\n```")
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        channel = self.client.get_channel(935980879262650379)
        embed = discord.Embed(description = f"Command : `{ctx.command.name}`\nGuild : `{ctx.guild.name if ctx.guild else None}`\nChannel : `{ctx.channel.name if ctx.guild else ctx.channel}`\nCommand Failed : `{ctx.command_failed}`\nMessage :\n```\n{ctx.message.content}\n```",
                color = discord.Color.random(),
                timestamp = ctx.author.created_at)
        embed.set_footer(text = f"ID : {ctx.author.id} | Created at")
        embed.set_author(name = ctx.author, icon_url = ctx.author.avatar_url)
        if ctx.guild: embed.set_thumbnail(url = ctx.guild.icon_url)
        await channel.send(embed = embed)
    
    @commands.command(aliases = ["p"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def price(self, ctx, mimir:float = None):
        """Get or calculate current price of Mimir Token."""
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        url = "https://api.coingecko.com/api/v3/coins/mimir-token"
        async with aiohttp.ClientSession() as session:
            response = await session.get(url = url)
            if response.status != 200:
                return await ws.send_hook("**Something unexpected happened while fetching current price!**")
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
            await ws.send_hook(embed = embed)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def addtoken(self, ctx, *, token = None):
        """Add or update Token."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        if not token: return await ctx.reply(ctx.author.mention + ", You didn't enter token.")
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        token = token.strip("Bearer").strip()
        await ws.get_quiz_details()
        await ws.get_access_token(token)
        update = {"token": token}
        db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ws.send_hook("**Token Successfully Updated!**")
        await ctx.message.delete()
        
    @commands.command(aliases = ["quiz", "mimir"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def nextquiz(self, ctx, game_num:int = 1):
        """Get next quiz details."""
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        await ws.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command(aliases = ["open"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def start(self, ctx):
        """Start Websocket."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        ws = Websocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        if not ws.ws_is_opened:
            await ws.send_hook("**Websocket Opened!**")
            await ws.start_hook()
        else:
            await ws.send_hook("**Websocket Already Opened!**")
         
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def close (self, ctx):
        """Close Websocket."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        ws = Websocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        if ws.ws_is_opened:
            await ws.set_hook(False)
        else:
            await ws.send_hook("**Websocket Already Closed!**")
        
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setup(self, ctx, channel: discord.TextChannel = None):
        """Setup mimir quiz channel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.reply(ctx.author.mention + ", You don't have enough permission to run this command!")
        if not channel: channel = ctx.channel
        webhook = await channel.create_webhook(name = "Mimir Quiz")
        check = db.mimir_details.find_one({"guild_id": ctx.guild.id})
        if check:
            update = {"web_url": webhook.url}
            db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            embed = discord.Embed(title = "Mimir Quiz Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Mimir Quiz Channel.")
        else:
            db.mimir_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "token": "eyJraWQiOiJYS1wvRlBZOFlcL1lJejV1VHJSSEdhOTZ6VHp0M1lWTlwvR25UQ0JrMitlbXNNPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI1ZTliNTY5YS0wNDIzLTQ4ODMtOTAyZS05YTQxYjM4YjJhYzQiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfME93Q2RwclNoIiwiY29nbml0bzp1c2VybmFtZSI6ImJlcm5mcmllZDMyNTBtZXllckBnbWFpbC5jb20iLCJvcmlnaW5fanRpIjoiMGVkYjIyZjQtNDBmMC00MjUwLWI0NzMtMzE3MzUwMzRiNWNkIiwiYXVkIjoiMnN1MG1qY3JqcXN2amlwZTYyYThnY281NDYiLCJldmVudF9pZCI6ImI2MDQ2OTcyLWFjMDYtNDJkYS04MzYyLTYzYWM2ZjNkNWFiMCIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNjUwMDQzNzkyLCJleHAiOjE2NTAwNDczOTIsImlhdCI6MTY1MDA0Mzc5MiwianRpIjoiMTFjMDFhMTgtYTQyMS00MjVmLTk4N2ItNGY5ZDliZGJjZDk5IiwiZW1haWwiOiJiZXJuZnJpZWQzMjUwbWV5ZXJAZ21haWwuY29tIn0.P6DjqvX_BqT60wliNRFg38RjE7AIU4yyCYv3eh8ShmlN7jO5THvuQp8h5hfa7Oss49xNytPZE7Dk74tEcNgI7QLTKI5_-xDZUGLCvGDenfCtiAK6TKYMgzOWjOVzS3LiCXNLAVjgKTBmq5iOehQPz1XN7Wvxq7cn7xMgnD1XXtJ4i5-jjI4DSpC6gnDSIEUfqpfm3pGv14R_HrIM5-6arWaZuxyPWBywh7fDmh1F5Z47dBd9gDFNR2LKFM1fFcn8-EVtl83FazRUJUO1l_KIio8Z1Awki0O-KvAfX0xGY7HkrFqZd_CdJY93eKHWR0qZZj-fdcq1BVtqyPsp76VlFQ:0xFCCd91Ca80bbf04da2Af2AA9E5569fdA28843D2E"})
            embed = discord.Embed(title = "Mimir Quiz Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Mimir Quiz Channel.")
            
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, ctx):
        embed = discord.Embed(color = discord.Colour.random())
        embed.add_field(name = f"{ctx.prefix}help", value = "Shows this message.", inline = False)
        embed.add_field(name = f"{ctx.prefix}setup [channel]", value = "Setup mimir quiz channel.", inline = False)
        embed.add_field(name = f"{ctx.prefix}price (amount)", value = "Shows current price of mimir token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}nextquiz (number)", value = "Shows upcoming quiz details.", inline = False)
        embed.add_field(name = f"{ctx.prefix}addtoken [token]", value = "Add/Update mimir authorization token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}start", value = "Start Websocket.", inline = False)
        embed.add_field(name = f"{ctx.prefix}close", value = "Close Websocket.", inline = False)
        embed.add_field(name = f"{ctx.prefix}invite", value = "Get bot invite link.", inline = False)
        embed.set_thumbnail(url = self.client.user.avatar_url)
        embed.set_author(name = "| Mimir Quiz Help Commands !", icon_url = self.client.user.avatar_url)
        embed.set_footer(text = f"Requested by : {ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)
        
intents = discord.Intents.all()
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents = intents)
client.remove_command("help")
client.add_cog(MimirQuiz(client))

@client.event
async def on_message(message):
    if not message.guild and not message.author.bot:
        embed = discord.Embed(description = f"**You cannot be used me in private messages. For invite me [Click Here](https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=523376&scope=bot).**")
        return await message.channel.send(embed = embed)
    await client.process_commands(message)
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.Qt4OvfOh7YZhH5hPoQzd7iatWGc")
