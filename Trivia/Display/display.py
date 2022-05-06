import discord
from discord.ext import commands
from Websocket.websocket import WebSocket
from database import db

class DisplayTrivia(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = f"with Display Trivia!", url = "https://app.displaysocial.com")
        await self.client.change_presence(activity=game)
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        """Start Websocket."""
        if "Display Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
        ws = WebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
        await ws.get_ws()
        if ws.ws:
            if ws.ws.open:
                return await ws.send_hook("**Websocket Already Opened!**")
        await ws.send_hook("**Websocket Opened!**")
        await ws.connect_ws()
        
    @commands.command()
    async def close(self, ctx):
        """Close Websocket."""
        if "Display Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
        ws = WebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Display Trivia.")
        await ws.close_ws()
        
    @commands.command()
    async def login(self, ctx, username = None, password = None):
        """Login to Display."""
        if "Display Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
        if not username or not password:
            return await ctx.reply(ctx.author.mention + ", You didn't mention username or password.\n```\n{}{} [username] [password]\n```".format(ctx.prefix, ctx.command.name))
        ws = WebSocket(guild_id = ctx.guild.id, client = self.client)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Display Trivia.")
        response = await ws.get_sub_protocol(username, password)
        if not response: return await ctx.reply(ctx.author.mention + ", Enter username or password is incorrect!")
        update = {"username": username, "password": password}
        db.display_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ctx.reply(ctx.author.mention + ", You have successfully login to Display!")
        await ctx.message.delete()
        
    @commands.command()
    async def setup(self, ctx, channel: discord.TextChannel = None):
        """Setup Display channel."""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.reply(ctx.author.mention + ", You don't have enough permission to run this command!")
        if not channel: channel = ctx.channel
        webhook = await channel.create_webhook(name = "Display Trivia")
        check = db.display_details.find_one({"guild_id": ctx.guild.id})
        if check:
            update = {"web_url": webhook.url}
            db.display_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
            embed = discord.Embed(title = "Display Trivia Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Display Trivia Channel.")
        else:
            db.display_details.insert_one({"guild_id": ctx.guild.id, "web_url": webhook.url, "username": None, "password": None,"subscription": False})
            embed = discord.Embed(title = "Display Trivia Channel Updated!", color = discord.Colour.random())
            await webhook.send(embed = embed)
            await ctx.reply(ctx.author.mention + ", You have successfully setup Display Trivia Channel.")


def setup(client):
    client.add_cog(DisplayTrivia(client))
