import discord
from Websocket.swagbucks_ws import SbWebSocket
from discord.ext import commands
from database import db

class SwagbucksTrivia(commands.Cog):
    
    def __init__(self, client):
    	super().__init__(client)
        self.client = client

	@commands.command()
	async def sbstart(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Username is required.")
		
		
	@commands.command()
	async def sblogin(self, ctx, email_id: str = None, password: str = None):
		if not email_id or not password:
			return await ctx.send("Username or Password is required to login to Swagbucks.")
		await self.login(ctx, email_id, password)
		
	@commands.command()
	async def details(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Required username to get details of Swagbucks account.")
		await self.account_details(ctx, username)
		
	@commands.command()
	async def nextshow(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Required username to get show details.")
		details = db.