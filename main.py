import discord
from discord.ext import commands
from Websocket.ws import Websocket

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        
    @commands.command(aliases = ["quiz", "mimir"])
    async def nextquiz(self, ctx):
        await self.get_quiz_details("send")
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        if not self.ws_is_opened:
            await self.start_hook()
        else:
            await self.send_hook("Websocket Already Opened!")
         
    @commands.command()
    async def close (self, ctx):
        if self.ws_is_opened:
            await self.close_hook()
        else:
            await self.send_hook("Websocket already closed!")
   
    

client = commands.Bot(command_prefix = ">")
client.add_cog(MimirQuiz(client))
            
client.run("ODAzMTc1OTQ1OTMwMTQ1Nzky.YA594w.Hzq49nLxp-KzwFRKh9mqDvi3Mqg")
