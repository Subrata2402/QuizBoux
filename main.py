import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
import aiohttp
import asyncio
import socket

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = f"with Mimir Quiz in {str(len(self.client.guilds))} guilds", url = "https://app.mimirquiz.com")
        await self.client.change_presence(activity=game)
        
    @commands.command()
    async def invite(self, ctx):
        """Get an invite link of bot."""
        embed = discord.Embed(title = "Invite me to your server.",
            url = f"https://discord.com/api/oauth2/authorize?client_id={self.client.user.id}&permissions=523376&scope=bot",
            color = discord.Colour.random())
        await ctx.reply(content = ctx.author.mention, embed = embed)
    
    
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
        await ctx.send(f"Hostname : `{hostname}`\nIP Address : `{ip_address}`")
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def sl(self, ctx):
        servers = self.client.guilds
        members = [guild.member_count for guild in servers]
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
    
    @commands.command(aliases = ["p"])
    async def price(self, ctx, mimir:float = None):
        """Get or calculate current price of Mimir Token."""
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        url = "https://api.coingecko.com/api/v3/coins/mimir-token"
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url) as response:
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
    async def nextquiz(self, ctx, game_num:int = 1):
        """Get next quiz details."""
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        await ws.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        """Start Websocket."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        if not ws.ws_is_opened:
            await ws.send_hook("**Websocket Opened!**")
            await ws.start_hook()
        else:
            await ws.send_hook("**Websocket Already Opened!**")
         
    @commands.command()
    async def close (self, ctx):
        """Close Websocket."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        if ws.ws_is_opened:
            await ws.close_hook()
        else:
            await ws.send_hook("**Websocket Already Closed!**")
        
    @commands.command()
    async def setup(self, ctx, channel: discord.TextChannel = None):
        """Setup mimir quiz channel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.reply(ctx.author.mention + ", You don't have enough permission to run this command!")
        if not channel: return await ctx.reply(ctx.author.mention + ", You didn't mention any channel.")
        webhook = await channel.create_webhook(name = "Mimir Quiz")
        check = db.mimir_details.find_one({"guild_id": ctx.guild.id})
        if check:
            update = {"web_url": webhook.url}
            db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            embed = discord.Embed(title = "Mimir Quiz Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Mimir Quiz Channel.")
        else:
            db.mimir_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "token": None})
            embed = discord.Embed(title = "Mimir Quiz Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Mimir Quiz Channel.")
            
        
intents = discord.Intents.all()
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents = intents)
client.add_cog(MimirQuiz(client))

@client.event
async def on_message(message):
    if not message.guild:
        return #await message.channel.send("**You cannot be used me in private messages.**")
    await client.process_commands(message)
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.Qt4OvfOh7YZhH5hPoQzd7iatWGc")
