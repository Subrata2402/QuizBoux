import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        
    @commands.command()
    @commands.is_owner()
    async def addtoken(self, ctx, token):
        await ctx.message.delete()
        update = {"token": token}
        db.token.update_one({"id": "3250"}, {"$set": update})
        await self.send_hook("Successfully Updated!")
        
    @commands.command()
    @commands.is_owner()
    async def tq(self, ctx):
        questions = list(db.question_base.find())
        await self.send_hook(f"Total Questions : {len(questions)}")
        
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
            await self.send_hook("Websocket Already Closed!")


client = commands.Bot(command_prefix = "m!", strip_after_prefix = True, case_insensitive = True)
client.add_cog(MimirQuiz(client))
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.OFUuud6gDHl5TYbcie3guwxPMI8")
