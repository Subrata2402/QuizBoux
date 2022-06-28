import aiohttp, json, discord
from discord import commands

class SbWebSocket(object):
	
	def __init__(self, client: commands.Bot, token: str):
		self.client = client
		self.vid = None
		self.partner_hash = None
		self.host = "https://api.playswagiq.com/"
		self.icon_url = "https://cdn.discordapp.com/attachments/799861610654728212/991317134930092042/swagbucks_logo.png"
		self.headers = {
			"content-type": "application/x-www-form-urlencoded",
			"Host": "app.swagbucks.com",
			"user-agent": "SwagIQ-Android/34 (okhttp/3.10.0);Realme RMX1911",
			"accept-encoding": "gzip",
			"authorization": token
		}
		
	@property
	def game_is_active(self) -> None:
		data = await self.fetch("POST", "trivia/join", headers = headers)
		if data["success"]:
			return True

	async def fetch(self, method = "GET", function = "", params = None, headers = None, data = None):
		"""
		Request Swagbucks to perform the action.
		"""
		async with aiohttp.ClientSession() as client_session:
			response = await client_session.request(method = method, url = self.host + function, params = params, headers = headers, data = data)
			if response.status != 200:
				await self.send_hook("Something went wrong!")
				#raise Exception("Something went Wrong!")
			return await response.json()
	
	async def send_answer(self, qid: str, aid: str):
		"""
		Send answer to the game.
		"""
		params = {
			"vid": self.vid, "qid": qid, "aid": aid, "timeDelta": 5000
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/answer", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully sent the answer.")
		else:
			await self.send_hook("Failed to send answer.\n```\n{}\n```".format(data))
	
	async def confirm_rebuy(self):
		"""
		If any question is wrong then we are eliminated.
		For come back and join again to the game we use a rejoin.
		To use this function we can send a rejoin. 
		"""
		params = {
			"vid": self.vid, "useLife": True, "partnerHash": self.partner_hash
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully rejoin in the game.")
		else:
			await self.send_hook("Failed to rejoin in the game.\n```\n{}\n```".format(data))
			
	async def complete_game(self):
		"""
		After end of the game check the details won or not
		and how many sb earn from the live game.
		"""
		params = {
			"vid": self.vid
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully complete the game.")
			winner = data.get("winner")
			sb = data.get("sb")
			await self.send_hook("You {} the game and got {} SB!".format('won' if winner else 'lost', sb))
		else:
			await self.send_hook("Failed to complete the game.\n```\n{}\n```".format(data))
			
	async def show_details(self):
		"""
		Get the details of the current game show.
		"""
		data = await self.fetch("POST", "trivia/home", headers = headers)
		prize = data["episode"]["grandPrizeDollars"]
		time = data["episode"]["start"]
		embed=discord.Embed(title = "__SwagIQ Next Show Details !__", description=f"• Show Name : Swagbucks Live\n• Show Time : <t:{time}>\n• Prize Money : ${prize}", color = discord.Colour.random())
		embed.set_thumbnail(url = self.icon_url)
		embed.set_footer(text = "Swagbucks Live")
		embed.timestamp = datetime.utcnow()
	
		