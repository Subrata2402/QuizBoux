import discord
from discord.ext import commands
import dhooks
channel = dhooks.Webhook("https://discord.com/api/webhooks/945352803306577990/y6MOcmueTfpUISdumR6Fss0v7a1xMRnBVywB_k-Fdrj_ecdOiiUXvg3igaI44vnGoNqj")

client = commands.Bot(command_prefix = "-", intents = discord.Intents(messages = True))
client.remove_command("help")

@client.event
async def on_ready():
    print("Ready")
    print(client.user)
    await channel.send(client.user)
	
@client.event
async def on_message_delete(message):
    deleted = discord.Embed(title=f"Username: `{message.author}`\nChannel: `{message.channel.name}`\nMessage Content :-", description=message.content, color=0x4040EC)
    deleted.set_author(name=message.guild.name, icon_url=message.guild.icon_url)
    deleted.set_thumbnail(url= message.guild.icon_url)
    #deleted.set_footer(text=self.client.user.name, icon_url=self.client.user.avatar_url)
    deleted.timestamp = message.created_at
    await channel.send(embed=deleted)
        
client.run("OTM2NTQyMDE1MTI5Mjc2NDU3.YfOsuA.06zDOsRSXyOWbai7YN_lNBPGZ_M")