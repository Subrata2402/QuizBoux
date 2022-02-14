import requests
import json
import discord
from discord.ext import commands
import datetime
from sseclient import SSEClient
import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
google_question = "https://google.com/search?q="
question_number = total_question = 0
from database import db
order = ["１", "２", "３", "４", "５", "６", "７", "８", "９", "０"]

class Websocket:
	
	def __init__(self):
		self.prize = 50 # Default prize money of quiz
		self.pattern = [] # Store answer pattern of the current quiz
		self.web_url = "https://discord.com/api/webhooks/938473130568065135/BGawZsFeWa59epspDbywoJNX1t-rQ4hiJroj7A6-vyZ7ZBtOipZlLIWIXaEciR-y8f2I"
		self.token = None
		self.ws_is_opened = False
		self.icon_url = "https://media.discordapp.net/attachments/938473054718279730/941230541687119932/924632014617972736.png"
		self.loop_is_active = False
		self.game_id = None
		self.partner_id = None
		self.user_id = None
		self.bearer_token = None
		self.value = None # Entry Fee of the quiz
		
	@property
	def game_is_active(self):
		url = "https://api.mimir-prod.com//games/next?" # api url of the mimir quiz details
		r = requests.get(url).json()
		data = r["data"]["data"][0]
		active = data["active"]
		return active
		
	async def close_hook(self):
		"""Close Websocket."""
		self.ws_is_opened = False
		print("Websocket Closed!")
		await self.send_hook("**Websocket Closed!**")

	async def get_token(self):
		"""Take Authorization Bearer Token from the database."""
		token = db.token.find_one({"id": "3250"})["token"]
		self.token = token

	async def send_hook(self, content = "", embed = None):
		"""Send message with Discord channel Webhook."""
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(self.web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(
				content = content,
				embed = embed,
				username = "Mimir Quiz",
				avatar_url = self.icon_url
				)
				
	async def get_answer(self, question):
		"""Take answer from the database if question found in db."""
		question = db.question_base.find_one({"question": question})
		if not question:
			return None
		answer = question.get("answer")
		return answer

	async def update_question(self, question, answer):
		"""Update answer if question found but answer not found."""
		question = db.question_base.find_one({"question": question})
		if question:
			update = {"answer": answer}
			db.question_base.update_one({"question": question}, {"$set", update})

	async def add_question(self, question, answer):
		"""Add Question in the database for the repeated questions."""
		# check if question is in the database
		check = db.question_base.find_one({"question": question})
		if not check:
			# insert question and answer if question not in databse
			db.question_base.insert_one({"question": question, "answer": answer})
			return True
		return False
				
	async def pay_fees(self):
		"""Pay fees in the paid games."""
		url = "https://api.mimir-prod.com/games/pay-fee"
		await self.get_quiz_details()
		data = json.dumps({
				"transaction": {
				"target": "0x4357d1eE11E7db4455527Fe3dfd0B882Cb334357",
				"to": "0xa02963C078fd71079cCcE5e0049b0Abf8AEDD178",
				"value": "50000000000000000000",
				"deadline": 1643540139,
				"v": 28,
				"r": "0x8e2c03e1d075ea83032c6d2faf128e07249e2496f3a20d0598ef4d680e313ca8",
				"s": "0x10e878cdf7164200e70b831a1cd838eb68e100839d9569c99bd27d2f98687419"
				},
			"game_id": self.game_id
			})
		headers = {
			"host": "api.mimir-prod.com",
			"authorization": f"Bearer {self.token}",
			"user-agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
			"content-type": "application/json",
			"accept": "*/*",
			"origin": "https://app.mimirquiz.com",
			"referer": "https://app.mimirquiz.com/",
			"accept-encoding": "gzip, deflate, br",
			"accept-language": "en-US,en;q=0.9,bn;q=0.8,hi;q=0.7"
		}
		async with aiohttp.ClientSession() as session:
			async with session.post(url = url, headers = headers, data = data) as response:
				if response.status != 200:
					await self.send_hook("**The Token has Expired!**")
					raise commands.CommandError("Pay Fees Error...!")
				r = await response.json()
				success = r["data"]["success"] # Return True if success else False
				if success:
					print("Fee Paid!")
					#await self.send_hook("**Fee Successfully Paid!**")
					#await self.send_hook(f"```\n{r}\n```")
				#else:
					#await self.send_hook("**Something wrong in 117 line!**")
				
	async def get_quiz_details(self, get_type = None, game_num:int = 1):
		"""Get quiz details and take game_id, partner_id, prize money etc."""
		await self.get_token() # Take token from the database
		url = "https://api.mimir-prod.com//games/next?" # api url of the mimir quiz details
		async with aiohttp.ClientSession() as session:
			async with session.get(url = url) as response:
				if response.status != 200:
					await self.send_hook("**Something unexpected happened while fetching quiz details!**")
					raise commands.CommandError("Token has expired!")
				r = await response.json()
				data = r["data"]["data"]
				if len(data) < game_num:
				    return await self.send_hook("**Quiz Not Found!**")
				data = data[game_num-1]
				#self.game_is_active = data["active"] # if game is live
				image_1 = data.get("backgroundImageLandscapeUrl")
				image_2 = data.get("previewImageUrl")
				self.icon_url = image_2 if not image_1 else image_1
				topic = data["label"]
				description = data.get("description")
				self.prize = data["reward"]
				time = f'<t:{int(data["scheduled"]/1000)}>'
				gameType = data["winCondition"]
				self.value = data.get("entryFee")
				self.game_id = data["id"]
				self.partner_id = data["partnerId"]
				if get_type == "send":
					embed = discord.Embed(
						title = "**__Mimir Upcoming Quiz Details !__**",
						description = description,
						color = discord.Colour.random(),
						)
						#timestamp = datetime.datetime.utcnow()
					embed.add_field(name = "Quiz Topic :", value = topic, inline = False)
					embed.add_field(name = "Prize Money :", value = f"ᛗ{self.prize}", inline = False)
					if self.value: embed.add_field(name = "Entry Fee :", value = f"ᛗ{self.value}", inline = False)
					embed.add_field(name = "Date & Time :", value = time, inline = False)
					embed.set_footer(text = f"Upcoming Quiz No. - {'0' if game_num < 10 else ''}{game_num}")
					embed.set_thumbnail(url = self.icon_url)
					await self.send_hook(embed = embed)

	async def get_access_token(self):
		"""Fetch access token to pass the authorization token.
		It's need for get the host of the live quiz api url."""
		await self.get_quiz_details() # To run this function take partner id of the quiz
		if self.value: await self.pay_fees()
		url = f"https://apic.us.theq.live/v2/oauth/token?partnerCode={self.partner_id}" # Get access token api url
		headers = {
			"host": "apic.us.theq.live",
			"user-Agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
			"accept": "application/json, text/plain, */*",
			"content-type": "application/json",
			"origin": "https://play.us.theq.live",
			"referer": "https://play.us.theq.live/",
			"accept-encoding": "gzip, deflate, br",
			"accept-language": "en-US,en;q=0.9,bn;q=0.8,hi;q=0.7"
		}
		post_data = json.dumps({"mimir":{"accessToken": self.token}})
		async with aiohttp.ClientSession() as session:
			async with session.post(url = url, headers = headers, data = post_data) as response:
				if response.status != 200:
					await self.send_hook("**Access Token Error...**")
					raise commands.CommandError("Get access token error...") # If response status not equal to 200 then raise an exception.
				r = await response.json()
				new_token = r["oauth"]["accessToken"]
				token_type = r["oauth"]["tokenType"]
				self.user_id = r["user"]["id"]
				self.bearer_token = token_type + " " + new_token
				
	async def get_host(self):
		"""Take host for live quiz api url."""
		# To run this function take live quiz bearer token
		await self.get_access_token()
		url = f"https://apic.us.theq.live/v2/games/active/{self.game_id}?userId={self.user_id}"
		headers = {
			"Host": "apic.us.theq.live",
			"accept": "application/json, text/plain, */*",
			"authorization": f"{self.bearer_token}",
			"sec-ch-ua-mobile": "?1",
			"user-agent": "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36",
			"origin": "https://play.us.theq.live",
			"referer": "https://play.us.theq.live/",
			"accept-encoding": "gzip, deflate, br",
			"accept-language": "en-US,en;q=0.9,bn;q=0.8,hi;q=0.7"
		}
		async with aiohttp.ClientSession() as session:
			async with session.get(url = url, headers = headers) as response:
				if response.status != 200:
					await self.send_hook("**Host Error...(Game is not live)**")
					raise commands.CommandError("Host Error")
				r = await response.json()
				data = r["game"]
				#self.game_is_active = data["active"]
				host = data.get("host")
				if not host:
					# check if not host that means fees not paid for the paid quiz.
					await self.send_hook("**Fees Not Paid!**")
					raise commands.CommandError("Fees Not Paid!")
				return host

	async def start_hook(self):
		"""Main function of the websocket. For Start websocket."""
		await self.send_hook("**Websocket Connecting...**")
		if not self.game_is_active:
			return await self.send_hook("**Game is Not Live!**")
		host = await self.get_host()
		url = f"https://{host}/v2/event-feed/games/{self.game_id}"
		headers = {
			"Host": host,
			"Connection": "keep-alive",
			'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
			"Accept": "text/event-stream",
			"Cache-Control": "no-cache",
			"Authorization": self.bearer_token,
			"sec-ch-ua-mobile": "?1",
			"User-Agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
			'sec-ch-ua-platform': '"Android"',
			"Origin": "https://play.us.theq.live",
			"Sec-Fetch-Site": "same-site",
			"Sec-Fetch-Mode": "cors",
			"Referer": "https://play.us.theq.live/",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "en-US,en;q=0.9,bn;q=0.8,hi;q=0.7"
		}
		try: # try to connect sseclient
			messages = SSEClient(url, headers = headers)
		except:
			return await self.send_hook("**Failed to Connect Websocket!**")
		self.ws_is_opened = True
		for msg in messages:
			event = msg.event
			print(event)
			print(msg.data)
			if self.ws_is_opened == False:
				"""For close socket."""
				return
			
			if event == "GameStatus":
				"""Game status event when connect socket successfully it shows the current status of the quiz."""
				await self.send_hook("**Websocket is Connected Successfully!**")

			elif event == "ViewCountUpdate":
				"""Live users update event."""
				data = json.loads(msg.data)
				count = data.get("viewCnt")
				await self.send_hook(embed = discord.Embed(title = f"🔴 Total Lives : {count} Users", color = discord.Colour.random()))
			
			elif event == "GameUpdate":
				"""When the Game will update like as rewards."""
				data = json.loads(msg.data)
				self.prize = data["reward"]

			elif event == "GameReset":
				"""When the game was reset."""
				await self.send_hook(embed = discord.Embed(title = "The Game has Reset!", color = discord.Colour.random()))

			elif event == "QuestionStart":
				"""Question start event when question coming up on the mobile screen."""
				global google_question, question_number, total_question
				data = json.loads(msg.data)
				embed = discord.Embed(color = discord.Colour.random())
				question = str(data["question"]).strip()
				question_number = data["number"]
				total_question = data["total"]
				response_time = data["secondsToRespond"]
				point_value = data.get("pointValue")
				raw_question = str(question).replace(" ", "+")
				google_question = "https://google.com/search?q=" + raw_question
				if data["questionType"] == "POPULAR":
					embed.title = f"**Question {question_number} out of {total_question}**"
					embed.description = f"**[{question}]({google_question})**"
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = f"Response Time : {response_time} secs | Points : {point_value}")
					await self.send_hook(embed = embed)
					
				elif data["questionType"] == "TRIVIA":
					choices = data["choices"]
					bing_question = "https://bing.com/search?q=" + raw_question
					options = ""
					for choice in choices:
						option = choice["choice"]
						options += option.strip() + "+"
					raw_options = str(options).replace(" ", "+")
					search_with_all = "https://google.com/search?q=" + raw_question + raw_options
					not_question = True if "not" in question.lower() else False
					is_not = "(Not Question)" if not_question else ""
					
					embed.title = f"**Question {question_number} out of {total_question} {is_not}**"
					embed.description = f"**[{question}]({google_question})\n\n[Search with all options]({search_with_all})**"
					for index, choice in enumerate(choices):
						embed.add_field(name = f"**Option -{order[index]}**", value = f"**[{choice['choice'].strip()}]({search_with_all})**", inline = False)
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = f"Response Time : {response_time} secs | Points : {point_value}")
					await self.send_hook(embed = embed)
					
					answer = await self.get_answer(question)
					answer_send = False
					if answer:
						for index, choice in enumerate(choices):
							if answer.lower() == str(choice["choice"]).strip().lower():
								await self.send_hook(embed = discord.Embed(title = f"**__Option {order[index]}. {answer}__**", color = discord.Colour.random()))
								answer_send = True
						if not answer_send: await self.send_hook(embed = discord.Embed(title = f"**__{answer}__**", color = discord.Colour.random()))
					
					# Google Search Results
					r = requests.get(google_question)
					res = str(r.text).lower()
					count_options = {}
					for choice in choices:
						option = choice["choice"]
						count_option = res.count(option.lower())
						count_options[option] = count_option
					max_count = max(list(count_options.values()))
					min_count = min(list(count_options.values()))
					min_max_count = min_count if not_question else max_count
					embed = discord.Embed(title="**__Google Search Results !__**", color = discord.Colour.random())
					embed.set_footer(text = "Mimir Quiz")
					embed.timestamp = datetime.datetime.utcnow()
					description = ""
					for index, option in enumerate(count_options):
						if min_max_count != 0 and count_options[option] == min_max_count:
							description += f"{order[index]}. {option} : {count_options[option]} ✅\n"
						else:
							description += f"{order[index]}. {option} : {count_options[option]}\n"
					embed.description = f"**{description}**"
					await self.send_hook(embed = embed)
					
					#Google Search Results 2
					try:
						r = requests.get(google_question)
						res = str(r.text).lower()
						count_options = {}
						for choice in choices:
							option = choice["choice"]
							count_option = 0
							options = tuple(choice["choice"].split(" "))
							for opt in options:
								count_option += res.count(opt.lower())
							count_options[option] = count_option
						max_count = max(list(count_options.values()))
						min_count = min(list(count_options.values()))
						min_max_count = min_count if not_question else max_count
						embed = discord.Embed(title="**__Google Search Results !__**", color = discord.Colour.random())
						embed.set_footer(text = "Mimir Quiz")
						embed.timestamp = datetime.datetime.utcnow()
						description = ""
						for index, option in enumerate(count_options):
							if min_max_count != 0 and count_options[option] == min_max_count:
								description += f"{order[index]}. {option} : {count_options[option]} ✅\n"
							else:
								description += f"{order[index]}. {option} : {count_options[option]}\n"
						embed.description = f"**{description}**"
						await self.send_hook(embed = embed)
					except:
						pass
					
					# Print Direct Search Results Text
					r = requests.get(google_question)
					soup = BeautifulSoup(r.text , "html.parser")
					response = soup.find("div" , class_='BNeawe')
					result = str(response.text)
					embed = discord.Embed(
						description = result,
						color = discord.Colour.random(),
						timestamp = datetime.datetime.utcnow()
						)
					embed.set_footer(text="Search with Google")
					option_found = False
					for index, choice in enumerate(choices):
						if choice["choice"].lower() in result.lower():
							embed.title = f"**__Option {order[index]}. {choice['choice']}__**"
							option_found = True
					if not option_found:
						embed.title = f"**__Direct Search Result !__**"
					await self.send_hook(embed = embed)

			elif event == "QuestionEnd":
				"""Raised when the question has ended!"""
				embed = discord.Embed(title = "Question has Ended!", color = discord.Colour.random())
				await self.send_hook(embed = embed)

			elif event == "QuestionResult":
				"""Raised when show the result of the question."""
				data = json.loads(msg.data)
				question = str(data["question"]).strip()
				if data["questionType"] == "TRIVIA":
					point_value = data.get("pointValue")
					answer_id = data.get("answerId")
					selection = data.get("selection")
					score = data.get("score")
					total_players, total_ratio = 0, 0
					for index, choice in enumerate(data["choices"]):
						if choice["correct"] == True:
							ans_num = index + 1
							answer = str(choice["choice"]).strip()
							advance_players = choice["responses"]
							advance_ratio = choice["userResponseRatio"]
						total_players += choice["responses"]
						total_ratio += choice["userResponseRatio"]
					eliminate_players = total_players - advance_players
					pE = float("{:.2f}".format(total_ratio - advance_ratio))
					pA = float("{:.2f}".format(advance_ratio))
					self.pattern.append(str(ans_num))
					await self.add_question(question, answer)
					ans = (self.prize)/(advance_players)
					payout = float("{:.2f}".format(ans))
					embed = discord.Embed(
						title = f"**Question {question_number} out of {total_question}**",
						description = f"**[{question}]({google_question})**",
						color = discord.Colour.random(),
						)
						#timestamp = datetime.datetime.utcnow()
					embed.add_field(name = "**Correct Answer :-**", value = f"**Option {order[ans_num-1]}. {answer}**", inline = False)
					embed.add_field(name = "**Status :-**",
						value = f"**Advancing Players : {advance_players} ({pA}%)\nEliminated Players : {eliminate_players} ({pE}%)\nCurrent Payout : ᛗ{payout}**",
						inline = False
					)
					embed.add_field(name = "**Ongoing Pattern :-**", value = f"**{self.pattern}**", inline = False)
					embed.set_footer(text = f"Correct : {'True' if (selection and selection == answer_id) else 'False'} | Total Points : {score}")
					embed.set_thumbnail(url = self.icon_url)
					await self.send_hook(embed = embed)

			elif event == "GameWinners":
				"""Raised this event when Show the winners."""
				data = json.loads(msg.data)
				winners = int(data["winnerCount"])
				ans = (self.prize)/(winners)
				payout = float("{:.2f}".format(ans))
				embed = discord.Embed(title = "**__Game Summary !__**",
					description = f"**● Payout : ᛗ{payout}\n● Total Winners : {winners}\n● Prize Money : ᛗ{self.prize}**",
					color = discord.Colour.random(),
					timestamp = datetime.datetime.utcnow()
					)
				embed.set_thumbnail(url = self.icon_url)
				embed.set_footer(text = "Mimir Quiz")
				await self.send_hook(embed = embed)
				
				winners = data["winners"]
				description = ""
				for index, winner in enumerate(winners):
					description += f"{'0' if index+1 < 10 else ''}{index+1} - {winner.get('user')}\n"
				embed = discord.Embed(title = "List of Game Winners Name !",
					description = f"```\n{description}\n```"
					)
				await self.send_hook(embed = embed)
				
			elif event == "GameEnded":
				"""When game has ended, raise this event."""
				embed = discord.Embed(title = "**__Game has Ended !__**",
					description = "**Thanks for playing!**", color = discord.Colour.random()
					)
				await self.send_hook(embed = embed)
				self.pattern.clear() # Clear answer pattern.
				await self.close_hook() # Socket Close automatically when the game was ended.
				return