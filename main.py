import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
import aiohttp
import asyncio

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        game = discord.Streaming(name = "with Mimir Quiz!", url = "https://app.mimirquiz.com")
        await self.client.change_presence(activity=game)
        
    
    @commands.command()
    async def addtoken(self, ctx, *, token = None):
        """Update Token."""
        if not token: return await ctx.reply(ctx.author.mention + ", You didn't enter token.")
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
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
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        await ws.get_quiz_details(get_type = "send", game_num = game_num)
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        """Start Websocket."""
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
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", You didn't setup any channel for Mimir Quiz.")
        if ws.ws_is_opened:
            await ws.close_hook()
        else:
            await ws.send_hook("**Websocket Already Closed!**")
        
    @commands.command()
    async def setup(self, ctx, channel: discord.TextChannel = None):
        """Get how many questions has stored in database."""
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
client.remove_command("help")

@client.event
async def on_message(message):
    if not message.guild:
        return #await messag 08e.channel.send("**You cannot be used me in private messages.**")
    await client.process_commands(message)
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.Qt4OvfOh7YZhH5hPoQzd7iatWGc")
