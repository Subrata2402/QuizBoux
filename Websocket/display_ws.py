import json, discord, websockets, requests
from bs4 import BeautifulSoup
from unidecode import unidecode
from datetime import datetime
import aiohttp, asyncio, re, threading
from database import db
from config import *
storingWs = {}
total_question = 0


class DisplayWebSocket(object):
	
	def __init__(self, guild_id = None, client = None):
		self.guild_id = guild_id
		self.client = client
		self.icon_url = "https://media.discordapp.net/attachments/840293855555092541/969343263276404836/Screenshot_2022-04-29-02-15-17-18.jpg"
		self.prize_pool = 500 # default prize pool of the quiz
		self.ws = None

	async def get_ws(self):
		"""Get Websocket."""
		self.ws = storingWs.get(self.guild_id)

	async def get_web_url(self) -> None:
		"""Get discord channel Webhook url for different guild."""
		web_url = db.display_details.find_one({"guild_id": self.guild_id})
		if not web_url:
			return web_url
		web_url = web_url.get("web_url")
		async with aiohttp.ClientSession() as session:
			response = await session.get(web_url)
			if response.status != 200:
				return None
		return web_url
		
	async def send_hook(self, content = "", embed = None):
		"""Send message with Discord channel Webhook."""
		web_url = await self.get_web_url()
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(content = content, embed = embed, username = self.client.user.name, avatar_url = self.client.user.avatar_url)
			
	async def close_ws(self):
		"""Close Websocket."""
		await self.get_ws()
		if not self.ws:
			await self.send_hook("**Websocket Already Closed!**")
		else:
			if self.ws.closed:
				return await self.send_hook("**Websocket Already Closed!**")
			await self.ws.close()
			await self.send_hook("**Websocket Closed!**")

	async def get_not_question(self, question) -> bool:
		"""Check either a question negative or not."""
		for negative_word in negative_words:
			if negative_word in question:
				not_question = True
				break
			else:
				not_question = False
		return not_question
	
	async def rating_search_one(self, question_url, options, not_question) -> None:
		"""Get Google search results through rating."""
		r = requests.get(question_url)
		res = str(r.text).lower()
		count_options = {}
		for option in options:
			_option = replace_options.get(option)
			option = _option if _option else option
			count_option = res.count(option.lower())
			count_options[option] = count_option
		max_count = max(list(count_options.values()))
		min_count = min(list(count_options.values()))
		min_max_count = min_count if not_question else max_count
		embed = discord.Embed(title=f"__Search Results -{order[0]}__", color = discord.Colour.random())
		embed.set_footer(text = "Display Trivia")
		embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == min_max_count:
				description += f"{order[index]}. {option} : {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option} : {count_options[option]}\n"
		embed.description = description
		await self.send_hook(embed = embed)
	
	async def rating_search_two(self, question_url, choices, not_question) -> None:
		"""Get 2nd Google search results through rating."""
		r = requests.get(question_url)
		res = str(r.text).lower()
		count_options = {}
		for choice in choices:
			option = ""
			count_option = 0
			options = tuple(choice.split(" "))
			for opt in options:
				_option = replace_options.get(opt)
				opt = _option if _option else opt
				count = 0 if opt.lower() in ignore_options else res.count(opt.lower())
				count_option += count
				option += f"{opt}({count}) "
			count_options[option] = count_option
		max_count = max(list(count_options.values()))
		min_count = min(list(count_options.values()))
		min_max_count = min_count if not_question else max_count
		embed = discord.Embed(title=f"__Search Results -{order[1]}__", color = discord.Colour.random())
		embed.set_footer(text = "Display Trivia")
		embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == min_max_count:
				description += f"{order[index]}. {option}: {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option}: {count_options[option]}\n"
		embed.description = description
		if max_count != 0: await self.send_hook(embed = embed)
	
	async def direct_search_result(self, question_url, options):
		"""Get Direct google search results."""
		r = requests.get(question_url)
		soup = BeautifulSoup(r.text , "html.parser")
		response = soup.find("div" , class_='BNeawe')
		result = str(response.text)
		embed = discord.Embed(
			description = result,
			color = discord.Colour.random(),
			timestamp = datetime.utcnow()
			)
		embed.set_footer(text="Search with Google")
		option_found = False
		for index, option in enumerate(options):
			if option.lower().strip() in result.lower():
				embed.title = f"__Option {order[index]}. {option}__"
				embed.description = re.sub(f'{option.strip()}', f'**__{option}__**', result, flags = re.IGNORECASE)
				option_found = True
		if not option_found:
			embed.title = f"__Direct Search Result !__"
		await self.send_hook(embed = embed)
	
	async def api_search_result(self, question, options, not_question) -> None:
		"""Get Google search results through the api."""
		if self.guild_id != 973610992510570546: return
		url = 'https://jhatboyrahul.herokuapp.com/api/getResults'
		headers = {"Authorization": "RainBhai12"}
		payload = {'question': question, 'answer': options}
		response = requests.post(url, headers=headers, json=payload).json()
		count_options = dict(zip(options, response["data"]))
		max_count, min_count = max(response['data']), min(response["data"])
		min_max_count = min_count if not_question else max_count
		embed = discord.Embed(title=f"__Api Search Results !__", color = discord.Colour.random())
		embed.set_footer(text = "Display Trivia")
		embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == min_max_count:
				description += f"{order[index]}. {option} : {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option} : {count_options[option]}\n"
		embed.description = description
		await self.send_hook(embed = embed)
	
	async def get_sub_protocol(self, username = None, password = None):
		"""Login display social and take the auth token."""
		username = username if username else db.display_details.find_one({"guild_id": self.guild_id})["username"]
		password = password if password else db.display_details.find_one({"guild_id": self.guild_id})["password"]
		login_url = "https://api.tsuprod.com/api/v1/user/login"
		data = json.dumps({
			"login": username,
			"password": password,
			"client_version": "2.4.0.3(154)"
		})
		headers = {
			"Host": "api.tsuprod.com",
			"content-type": "application/json; charset=UTF-8",
			"accept-encoding": "gzip",
			"user-agent": "okhttp/4.9.1",
			"app_version": "2.4.0.3"
		}
		async with aiohttp.ClientSession() as session:
			response = await session.post(url = login_url, headers = headers, data = data)
			if response.status != 200:
				if not username:
					await self.send_hook("```\nSomething went wrong, If you didn't login yet or changed the username or password then please login again to start the websocket.\n```")
				else:
					return None
				raise "Username or password is wrong."
			data = await response.json()
			auth_token = data["data"]["auth_token"]
			return auth_token

	async def connect_ws(self):
		sub_protocol = await self.get_sub_protocol()
		socket_url = "wss://trivia-websockets.tsuprod.com/"
		headers = {
			"Upgrade": "websocket",
			"Connection": "Upgrade",
			"Sec-WebSocket-Version": "13",
			"Sec-WebSocket-Extensions": "permessage-deflate",
			"Host": "trivia-websockets.tsuprod.com",
			"Accept-Encoding": "gzip",
			"User-Agent": "okhttp/4.9.1"
		}
		send_data = False # check data send or not
		connect = False # check Websocket connect or not
		question_ids = [] # store question
		correct_answer_ids = [] # Store correct answer id of a question
		show_winners = False # check winner shows or not
		answer_pattern = [] # Store answer number of each question
		try:
			self.ws = await websockets.connect(socket_url, subprotocols = [sub_protocol], extra_headers = headers, ping_interval = 15)
		except Exception as e:
			return await self.send_hook("```\nSomething went wrong while connecting to the websocket, please join once in the trivia in your application by the same account which was logged in to the bot and then try to start the websocket.\n```")
		storingWs[self.guild_id] = self.ws # store Websocket for each guild
		async for message in self.ws:
			message_data = json.loads(message)
			if message_data.get("status") == "Connected":
				"""Check either Websocket connect or not."""
				print("Websocket Connected!")
				await self.send_hook("**Websocket Connecting...**")
				
			if message_data.get("type") == "games_list":
				"""Get games list and take game id from it then send game id to ws for subscribe the current game."""
				game_id = message_data["data"][0]["id"]
				survey_type = message_data["data"][0]["survey_type"]
				if not send_data and survey_type == 1:
					await self.ws.send(json.dumps({"action": "subscribe", "data": {"game_id": game_id}}))
					send_data, connect = True, True
					await self.send_hook("**Websocket Successfully Conncted!**")
					try:
						log_channel = self.client.get_channel(967462642723733505) or (await self.client.fetch_channel(967462642723733505))
						guild = self.client.get_guild(self.guild_id) or (await self.client.fetch_guild(self.guild_id))
						await log_channel.send(f"Display Bot started in **{guild.name}**!")
					except Exception as e:
						print(e)
			
			if message_data.get("t") == "poll":
				pass

			elif message_data.get("type") == "poll":
				pass

			elif message_data.get("t") == "trivium":
				"""Raised this event when shows the question."""
				global total_question, google_question
				question_id = message_data["q"][0]["id"]
				if question_id not in question_ids:
					question_ids.append(question_id)
					self.prize_pool = message_data["j"]
					total_question = message_data["max_q"]
					question_number = message_data["q"][0]["nth"]
					question = message_data["q"][0]["q"].strip()
					options = [unidecode(option["a"].strip()) for option in message_data["q"][0]["a"]]
					raw_question = str(question).replace(" ", "+")
					google_question = "https://google.com/search?q=" + raw_question
					u_options = "+or+".join(options)
					raw_options = str(u_options).replace(" ", "+")
					search_with_all = "https://google.com/search?q=" + raw_question + "+" + raw_options
					not_question = await self.get_not_question(question.lower())
					is_not = "(Not Question)" if not_question else ""
					
					embed = discord.Embed(color = discord.Colour.random())
					embed.title = f"Question {question_number} out of {total_question} {is_not}"
					embed.description = f"[{question}]({google_question})\n\n[Search with all options]({search_with_all})"
					for index, option in enumerate(options):
						embed.add_field(name = f"Option - {order[index]}", value = f"[{option.strip()}]({google_question + '+' + str(option).strip().replace(' ', '+')})", inline = False)
					embed.set_footer(text = "Display Trivia")
					embed.set_thumbnail(url = self.icon_url)
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					
					target_list = [
							self.rating_search_one(google_question, options, not_question),
							self.rating_search_two(google_question, options, not_question),
							self.api_search_result(question, options, not_question),
							self.direct_search_result(google_question, options),
						]
							#self.direct_search_result(search_with_all, choices)
					for target in target_list:
						thread = threading.Thread(target = lambda: asyncio.run(target))
						thread.start()
						
					await asyncio.sleep(9)
					await self.send_hook(embed = discord.Embed(title = "⏰ | Time's Up!", color = discord.Colour.random()))
					
			elif message_data.get("t") == "results":
				"""Raised this event when shows the status of a question."""
				total_players, total_ratio = 0, 0
				check_result = False
				for index, data in enumerate(message_data["q"][0]["a"]):
					if data["c"]:
						check_result = True
						ans_num = index
						answer = data["a_c"]
						answer_id = data["id"]
						advance_players = data["t"]
						advance_ratio = float(data["p"])
					total_players += data["t"]
					total_ratio += float(data["p"])
				if check_result and answer_id not in correct_answer_ids:
					correct_answer_ids.append(answer_id)
					answer_pattern.append(str(ans_num+1))
					eliminate_players = total_players - advance_players
					eliminate_ratio = float("{:.2f}".format(total_ratio - advance_ratio))
					question_number = message_data["q"][0]["nth"]
					question = message_data["q"][0]["q_c"]
					ans = 0 if advance_players == 0 else (self.prize_pool)/(advance_players)
					payout = float("{:.2f}".format(ans))
					
					embed = discord.Embed(color = discord.Colour.random())
					embed.title = f"Question {question_number} out of {total_question}"
					embed.description = f"[{question}]({google_question})"
					embed.add_field(name = "Correct Answer :-", value = f"Option {order[ans_num]}. {answer}", inline = False)
					embed.add_field(name = "Status :-",
						value = f"Advancing Players : {advance_players} ({advance_ratio}%)\nEliminated Players : {eliminate_players} ({eliminate_ratio}%)\nCurrent Payout : ${payout}",
						inline = False
						)
					embed.add_field(name = "Ongoing Pattern :-", value = answer_pattern, inline = False)
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = "Display Trivia")
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					
			elif message_data.get("game_type") == "trivium":
				"""Raised this condition when shows the winners of the quiz."""
				if not show_winners:
					show_winners = True
					prize_pool = message_data["prize_pool"]
					num_winners = message_data["num_winners"]
					share = message_data["share"]
					
					embed = discord.Embed(title = "__Game Summary !__",
						description = f"● Payout : ${share}\n● Total Winners : {num_winners}\n● Prize Money : ${prize_pool}",
						color = discord.Colour.random(),
						)
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = "Display Trivia")
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					await self.close_ws()
