import discord, aiohttp, asyncio, socket
from discord.ext import commands
from database import db
from translate import translate, languages
import os, sys, traceback, datetime

class MainClass(commands.Cog):
    
    def __init__(self, client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        # game = discord.Streaming(name = f"with {str(len(self.client.guilds))} guilds | {str(len(self.client.users))} users", url = "https://app.mimirquiz.com")
        # await self.client.change_presence(activity=game)
        while True:
            game = discord.Game(f"with {str(len(self.client.guilds))} guilds | {str(len(self.client.users))} users")
            await self.client.change_presence(status=discord.Status.dnd, activity=game)
            await asyncio.sleep(5)
            game = discord.Game("with Mimir & Display | -help")
            await self.client.change_presence(status=discord.Status.dnd, activity=game)
            await asyncio.sleep(5)
            
        
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
        print(f"Ignoring exception in command {ctx.command}", file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
            )
    
    
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
        
    @commands.command()
    @commands.is_owner()
    async def reply(self, ctx, user_id=None, *, args=None):
        if not user_id:
            return await ctx.channel.send("You didn't provide a user's id.")
        try:
            target = await self.client.fetch_user(user_id)
            #embed=discord.Embed(title="__Reply from Bot Owner :__", description=args, color=discord.Colour.random())
            if not args:
                embed = discord.Embed(title = "__Invalid Transaction ID !__", color = discord.Colour.random(),
                    description = "Invalid Transaction ID provided! Don't worry if you already paid the amount, start this process once again and send your Transaction ID!")
                return await target.send(embed = embed)
            await target.send(args)
            embed=discord.Embed(description=f"DM successfully sent to {target.name}")
            await ctx.channel.send(embed=embed)
        except:
            await ctx.channel.send("Couldn't dm the given user.")
    
        
    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def subscribe(self, ctx, guild_id: int = None):
        if ctx.guild: await ctx.send(ctx.author.mention + "**, Please use the command in DM!**")
        if not guild_id: return await ctx.send("Please enter your guild id!")
        guild = self.client.get_guild(guild_id)
        if not guild: return await ctx.send("Please provide a valid guild id!")
        embed = discord.Embed(title = "__Subscription Details !__",
            description = "One Week : ₹50.00/$1.00\nOne Month : ₹180.00/$3.50",
            color = discord.Colour.random())
        embed.add_field(name = "__Payment Details !__", value = "Paytm : [Click Here](https://paytm.me/x-WGerG) (For QR Code : [Click Here](https://cdn.discordapp.com/attachments/799861610654728212/978009606716555375/Screenshot_2022-05-23-00-29-55-83.jpg))\nPaypal : [Click Here](https://paypal.me/sakhman)\n\nPlease send the exact amount to the following payment link. After payment send your Transaction ID/UPI Ref.No. here within 5 minutes.", inline = False)
        embed.set_footer(text = "Payment Created by : {}".format(ctx.author), icon_url = ctx.author.avatar_url)
        m = await ctx.author.send(embed = embed)
        try:
            message = await self.client.wait_for("message", timeout = 300.0, check = lambda message: message.author == ctx.author and message.channel == ctx.channel)
        except:
            embed = discord.Embed(title = "__Time's Up !__", color = discord.Colour.random(),
                description = "You failed to send your Transaction ID within time. Don't worry if you already paid the amount then start this process once again and send your Transaction ID.")
            return await m.edit(embed = embed)
        id = message.content.strip()
        embed = discord.Embed(title = "__Payment in Review !__", color = discord.Colour.random(),
            description = "Thanks for the subscription. Your guild will be added as a premium after verify the payment details.")
        await ctx.author.send(embed = embed)
        channel = self.client.get_channel(940249905300131871)
        embed = discord.Embed(title = "__Payment Information !__",
            description = f"```\n" \
                f"Username       : {ctx.author}\n" \
                f"User ID        : {ctx.author.id}\n" \
                f"Guild Name     : {guild.name}\n" \
                f"Guild ID       : {guild.id}\n" \
                f"Transaction ID : {id}\n```",
            color = discord.Colour.random())
        await channel.send(embed = embed)
        await channel.send(f"```\n{ctx.prefix}addpremium {guild_id} {ctx.author.id}\n```")
        await self.client.get_user(660337342032248832).send("Someone buy premium subscription for display Trivia!")
        
    @commands.command()
    @commands.is_owner()
    async def addpremium(self, ctx, guild_id: int = None, subscriber: int = None, days: int = None):
        if not guild_id: return await ctx.send("Guild I'd is not provided!")
        guild = self.client.get_guild(guild_id)
        check = db.display_details.find_one({"guild_id": guild_id})
        if not check: return await ctx.send("Guild does not find in the database.")
        current_time = datetime.datetime.utcnow()
        change_time = datetime.timedelta(days = days)
        date_time = current_time + change_time
        update = {"subscription": True, "expired_time": date_time, "claimed_time": current_time, "subscriber": subscriber}
        db.display_details.update_one({"guild_id": guild_id}, {"$set": update})
        await ctx.send("Subscription added successfully for **{}**!".format(guild.name))
    
    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def subscription(self, ctx, guild_id: int = None):
        if "Display Access" not in [role.name for role in ctx.author.roles]:
            return await ctx.reply(ctx.author.mention + ", You need `Display Access` role to run this command!")
        if not guild_id: guild_id = ctx.guild.id
        guild = self.client.get_guild(guild_id)
        data = db.display_details.find_one({"guild_id": guild.id})
        em = discord.Embed(title = "__Missing Subscription !__", color = discord.Colour.random(),
            description = "This guild doesn't have any active subscription. For subscribe use `{}subscribe [guild_id]` in bot's DM!".format(ctx.prefix))
        if not data or not data.get("subscription"):
            return await ctx.send(embed = em)
        expired_time = data.get("expired_time")
        claimed_time = data.get("claimed_time")
        subscriber = self.client.get_user(data.get("subscriber"))
        current_time = datetime.datetime.utcnow()
        if current_time > expired_time:
            return await ctx.send(embed = em)
        expired_date = f"<t:{int(expired_time.timestamp())}>"
        claimed_date = f"<t:{int(claimed_time.timestamp())}>"
        embed = discord.Embed(title = "__Subscription Details !__", color = discord.Colour.random())
        if guild.id != ctx.guild.id: embed.add_field(name = "Guild Information :", value = f"Name : {guild.name}\nOwner : {guild.owner}", inline = False)
        embed.add_field(name = "Claimed Date :", value = claimed_date, inline = False)
        embed.add_field(name = "Claimed By :", value = f"{subscriber}\n(`{subscriber.id}`)", inline = False)
        embed.add_field(name = "Expired Date :", value = expired_date, inline = False)
        embed.set_thumbnail(url = guild.icon_url)
        embed.set_footer(text = f"Requested by : {ctx.author}", icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)
    
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
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def help(self, ctx):
        embed = discord.Embed(color = discord.Colour.random())
        embed.add_field(name = f"{ctx.prefix}help", value = "Shows this message.", inline = False)
        embed.add_field(name = f"{ctx.prefix}setup [mimir/display/hq] [channel]", value = "Setup channel for Mimir/Display.", inline = False)
        embed.add_field(name = f"{ctx.prefix}price (amount)", value = "Shows current price of mimir token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}nextquiz [mimir/hq] (number)", value = "Shows upcoming mimir/hq quiz details.", inline = False)
        #embed.add_field(name = f"{ctx.prefix}nexthq", value = "Shows upcoming show details of HQ Trivia.", inline = False)
        embed.add_field(name = f"{ctx.prefix}addtoken [mimir/hq] [token]", value = "Add/Update mimir/hq authorization token.", inline = False)
        embed.add_field(name = f"{ctx.prefix}login [username] [password]", value = "Login to Display for start websocket. Before login please read the note carefully.\n\n**__Note :__** Please don't use username and password of your main account for the chances of account ban. If account will get ban then we are not responsible for this.", inline = False)
        embed.add_field(name = f"{ctx.prefix}getvideo", value = "Get a video where you can find how to get authorization token of mimir.", inline = False)
        embed.add_field(name = f"{ctx.prefix}start [mimir/display/hq]", value = "Start Websocket of Mimir/Display/HQ.", inline = False)
        embed.add_field(name = f"{ctx.prefix}close [mimir/display/hq]", value = "Close Websocket of Mimir/Display/HQ.", inline = False)
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
        await channel.send(embed=embed)
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
        print("Extensions Loaded Successful!")
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.L5411_ltMGYE1Hcioe-nudFmaq0")
