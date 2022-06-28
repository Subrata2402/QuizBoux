import aiohttp, json, discord
from discord import commands

class SbWebSocket(object):
	
	def __init__(self, client: commands.Bot, token: str):
		self.client = client
		self.token = token
		self.vid = None
		self.partner_hash = None
		self.host = "https://api.playswagiq.com/"
		self.headers = {
			"content-type": "application/x-www-form-urlencoded",
			"Host": "app.swagbucks.com",
			"user-agent": "SwagIQ-Android/34 (okhttp/3.10.0);Realme RMX1911",
			"accept-encoding": "gzip"
		}

	async def fetch(self, method = "GET", function = "", params = None, headers = None, data = None):
		async with aiohttp.ClientSession() as client_session:
			response = await client_session.request(method = method, url = self.host + function, params = params, headers = headers, data = data)
			if response.status != 200:
				await self.send_hook("Something went wrong!")
				#raise Exception("Something went Wrong!")
			return await response.json()
	
	async def send_answer(self, qid: str, aid: str):
		params = {
			"vid": self.vid, "qid": qid, "aid": aid, "timeDelta": 5000
		}
		self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/answer", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully sent the answer.")
		else:
			await self.send_hook("Failed to send answer.\n```\n{}\n```".format(data))
	
	async def confirm_rebuy(self):
		params = {
			"vid": self.vid, "useLife": True, "partnerHash": self.partner_hash
		}
		self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully rejoin in the game.")
		else:
			await self.send_hook("Failed to rejoin in the game.\n```\n{}\n```".format(data))
			
	async def complete_game(self):
		params = {
			"vid": self.vid
		}
		self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully complete the game.")
			winner = data.get("winner")
			sb = data.get("sb")
			await self.send_hook("You {} the game and got {} SB!".format('won' if winner else 'lost', sb))
		else:
			await self.send_hook("Failed to complete the game.\n```\n{}\n```".format(data))
			
	async def 