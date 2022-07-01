import discord
from Websocket.swagbucks_ws import SbWebSocket, SwagbucksLive
from discord.ext import commands
from database import db

class SwagbucksTrivia(commands.Cog, SwagbucksLive):
	
	def __init__(self, client):
		super().__init__(client)
		self.client = client

	@commands.command()
	async def sbstart(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Username is required.")
		ws = SbWebSocket(self.client, username.lower())
		await ws.get_ws()
		if ws.ws:
			if ws.ws.open:
				return await ws.send_hook("Websocket Already Opened!")
		await ws.send_hook("Websocket Connecting...")
		await ws.connect_websocket()
		
	@commands.command()
	async def sbclose(self, ctx, username: str = None):
		ws = SbWebSocket(self.client, username.lower())
		await ws.close_ws()
	
	@commands.command()
	async def sblogin(self, ctx, email_id: str = None, password: str = None):
		if not email_id or not password:
			return await ctx.send("Username or Password is required to login to Swagbucks.")
		await self.login(email_id, password)
		
	@commands.command()
	async def sbupdate(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Required username to update of Swagbucks account.")
		details = db.sb_details.find_one({"username": username.lower()})
		if not details:
			return await ctx.send("No account found.")
		email_id, password = details["email_id"], details["password"]
		db.sb_details.delete_one({"username": username.lower()})
		await self.login(email_id, password)
		
	@commands.command()
	async def details(self, ctx, username: str = None):
		if not username:
			return await ctx.send("Required username to get details of Swagbucks account.")
		await self.account_details(username.lower())
		
	@commands.command()
	async def nextshow(self, ctx):
		username = list(db.sb_details.find())[0]["username"]
		ws = SwagbucksLive(self.client, username)
		await ws.show_details()
		
	# @commands.command()
	# async def sbtoken(self, ctx, email_id: str = None, password: str = None):
	# 	if ctx.guild:
	# 		return await ctx.send("Please use this command in Private Messages.")
	# 	if not email_id or not password:
	# 		return await ctx.send("Username or Password is required to login to Swagbucks.")
	# 	token = await self.login(email_id, password, "GET")
	# 	await ctx.send("```\n{}\n```".format(token))
		
def setup(client):
	client.add_cog(SwagbucksTrivia(client))