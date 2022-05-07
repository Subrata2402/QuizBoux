import discord, aiohttp, asyncio, socket
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
from translate import translate, languages
import os, sys, traceback

class MainClass(commands.Cog, Websocket):
    
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
    async def invite(self, ctx):
        """Get an invite link of bot."""
        embed = discord.Embed(title = "Invite me to your server.",
            url = f"https://discord.com/api/oauth2/authorize?client_id={self.client.user.id}&permissions=523376&scope=bot",
            color = discord.Colour.random())
        await ctx.reply(content = ctx.author.mention, embed = embed)
    
    #@commands.command()
    #@commands.cooldown(1, 10, commands.BucketType.guild)
    async def addlang(self, ctx, language = None):
        """Add or update Token."""
        if "Mimir Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Mimir Access` role to run this command!")
        if not language:
            langs = ", ".join([key for key in languages])
            return await ctx.reply(ctx.author.mention + f", You didn't enter any language. Available languages : \n```\n{langs}\n```")
        ws = Websocket(ctx.guild.id)
        web_url = await ws.get_web_url()
        if not web_url: return await ctx.reply(ctx.author.mention + ", Channel not setup for Mimir Quiz.")
        if language.lower() not in languages:
            return await ctx.reply(ctx.author.mention + f", No support for the provided language. Please select on of the supported languages: \n```\n{langs}\n```")
        update = {"language": language}
        db.mimir_details.update_one({"guild_id": ctx.guild.id}, {"$set": update})
        await ws.send_hook("Language Successfully Updated to **{}**!".format(language))
        #await ctx.message.delete()
        
    @commands.command()
    async def translate(self, ctx, language, *, text):
        if language.lower() not in languages:
            langs = ", ".join([key.title() for key in languages])
            return await ctx.reply(ctx.author.mention + f", No support for the provided language. Please select on of the supported languages: \n```\n{langs}\n```")
        translate_text = translate(language, text)
        await ctx.send(f"**__Translate in {language.title()}__**\n```\n" + translate_text + "\n```")
        
    
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
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, ctx):
        embed = discord.Embed(color = discord.Colour.random())
        embed.add_field(name = f"{ctx.prefix}help", value = "Shows this message.", inline = False)
        embed.add_field(name = f"{ctx.prefix}setup [mimir/display] [channel]", value = "Setup channel for Mimir/Display.", inline = False)
        embed.add_field(name = f"{ctx.prefix}price (amount)", value = "Shows current price of mimir token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}nextquiz (number)", value = "Shows upcoming quiz details.", inline = False)
        embed.add_field(name = f"{ctx.prefix}addtoken [token]", value = "Add/Update mimir authorization token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}login [username] [password]", value = "Login to Display for start websocket. Before login please read the note carefully.\n**__Note :__** Please don't use main account id and password for the chances of account ban. If account will get ban then we are not responsible for this.", inline = False)
        embed.add_field(name = f"{ctx.prefix}getvideo", value = "Get a video where you can find how to get authorization token of mimir.", inline = False)
        embed.add_field(name = f"{ctx.prefix}start [mimir/display]", value = "Start Websocket of Mimir/Display. Before start the display websocket please read the note carefully.\n**__Note :__** The websocket will before 30 seconds of the question coming or when question will come, start the websocket. If started before long time  the question coming, close it and start again.", inline = False)
        embed.add_field(name = f"{ctx.prefix}close [mimir/display]", value = "Close Websocket of Mimir/Display.", inline = False)
        embed.add_field(name = f"{ctx.prefix}invite", value = "Get bot invite link.", inline = False)
        embed.set_thumbnail(url = self.client.user.avatar_url)
        embed.set_author(name = f"| {self.client.user.name} Help Commands !", icon_url = self.client.user.avatar_url)
        embed.set_footer(text = f"Requested by : {ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)
        
intents = discord.Intents.all()
client = commands.Bot(command_prefix = "-", strip_after_prefix = True, case_insensitive = True, intents = intents)
client.remove_command("help")
client.add_cog(MainClass(client))

@client.event
async def on_message(message):
    if not message.guild and not message.author.bot:
        channel = client.get_channel(970214184128237630)
        embed=discord.Embed(description=message.content, color=discord.Colour.random())
        embed.set_thumbnail(url=message.author.avatar_url)
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        embed.set_footer(text=f"Name: {message.author} | ID: {message.author.id}", icon_url=message.author.avatar_url)
        if message.attachments: embed.set_image(url = message.attachments[0].url)
        return await channel.send(embed=embed)
        #embed = discord.Embed(description = f"**You cannot be used me in private messages. For invite me [Click Here](https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=523376&scope=bot).**")
        #return await message.channel.send(embed = embed)
    await client.process_commands(message)

extensions = ["Trivia.trivia"]

if __name__ == "__main__":
    failed_ext = ""
    for extension in extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            failed_ext += f"{extension}, "
            print(f"Error loading {extension}", file=sys.stderr)
            traceback.print_exc()
    if failed_ext != "":
        print("Loaded Failed :", failed_ext)
    else:
        print("Loaded Successful!")
            
client.run("NzYwNzIxNDUwNTExNjMwMzc2.X3QLDw.ZMGeJCG9cN0JfkNz8RsOl8c044o")