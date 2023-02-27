import requests, discord, re
from discord.ext import commands
from bs4 import BeautifulSoup
import random, openai
import config

class Quizophy(commands.Cog):
	
	def __init__(self, client):
		self.client = client
		self.host = "https://quizophy.in/api/quizzes"
		self.headers = {
			"accept" : "application/json, text/plain, */*",
			"Host" : "quizophy.in",
			"Connection" : "Keep-Alive",
			"Accept-Encoding" : "gzip",
			"User-Agent" : "okhttp/3.12.12"
		}
		
	async def get_quiz_details(self, ctx, quiz: str = "paid", number: int = 1) -> None:
		user_id = random.randint(12288, 18829)
		file = {
			'userid' : (None, user_id),
			'start' : (None, '0'),
			'limit' : (None, '10'),
			'courseid' : (None, 'All'),
			'subjectid' : (None, 'All')
		}
		response = requests.post(self.host + "/get", headers = self.headers, files = file)
		response_data = response.json()
		data = response_data["data" if quiz == "paid" else "freequiz"]
		if len(data) < number:
			return await ctx.send("Quiz Not Found!")
		quiz_data = data[0-number]
		id = quiz_data["id"]
		quiz_key = quiz_data["key"]
		embed = discord.Embed(title = "__Next Quiz Details !__",
			description = "```\n" \
				f"Course Name : {quiz_data.get('coursename')}\n" \
				f"Duration : {quiz_data.get('duration')}\n" \
				f"Entry Fee : ₹{quiz_data.get('entryfee')}\n" \
				f"First Prize : ₹{quiz_data.get('firstprize')}\n" \
				f"Languages : {', '.join(quiz_data.get('language'))}\n" \
				f"Name : {quiz_data.get('name')}\n" \
				f"Total Prize : ₹{quiz_data.get('prizepool')}\n" \
				f"Time : {quiz_data.get('startdate')}\n" \
				f"Total Questions : {quiz_data.get('totalquestions')}\n" \
				f"Spots : {quiz_data.get('totalspots')}\n" \
				f"Total Winner Percentage : {quiz_data.get('totalwinner_percentage')}%\n" \
				f"Users Playing : {quiz_data.get('userplaying')}\n```")
		await ctx.send(embed = embed)
		await ctx.send(quiz_key)
		
	async def get_not_question(self, question) -> bool:
		"""Check either a question negative or not."""
		for negative_word in negative_words:
			if negative_word in question:
				not_question = True
				break
			else:
				not_question = False
		return not_question
		
	async def google_search(self, question_url, options, not_question) -> None:
		"""Get Google search results through rating."""
		r = requests.get(question_url)
		res = str(r.text).lower()
		count_options = {}
		for option in options:
			_option = replace_options.get(option)
			re_option = _option if _option else option
			count_option = res.count(re_option.lower())
			count_options[option] = count_option
		max_count = max(list(count_options.values()))
		min_count = min(list(count_options.values()))
		min_max_count = min_count if not_question else max_count
		#embed = discord.Embed(title=f"__Search Results -{order[0]}__", color = discord.Colour.random())
		#embed.set_footer(text = "Display Trivia")
		#embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == min_max_count:
				description += f"{index+1}. {option} : {count_options[option]} ✅\n"
			else:
				description += f"{index+1}. {option} : {count_options[option]}\n"
		#embed.description = description
		#await self.send_hook(embed = embed)
		return description

	async def google_search_two(self, ctx, question_url, choices, not_question) -> None:
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
		embed = discord.Embed(color = discord.Colour.random())
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == min_max_count:
				description += f"{order[index]}. {option}: {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option}: {count_options[option]}\n"
		embed.description = description
		await ctx.send(embed = embed)

	async def direct_search_result(self, ctx, question_url, options):
		"""Get Direct google search results."""
		r = requests.get(question_url)
		soup = BeautifulSoup(r.text , "html.parser")
		response = soup.find("div" , class_='BNeawe')
		result = str(response.text)
		embed = discord.Embed(
			description = result,
			color = discord.Colour.random(),
			#timestamp = datetime.utcnow()
			)
		#embed.set_footer(text="Search with Google")
		option_found = False
		for index, option in enumerate(options):
			if option.lower().strip() in result.lower():
				embed.title = f"__Option {order[index]}. {option}__"
				embed.description = re.sub(f'{option.strip()}', f'**__{option}__**', result, flags = re.IGNORECASE)
				option_found = True
		if not option_found:
			embed.title = f"__Direct Search Result !__"
		await ctx.send(embed = embed)
		

	async def get_ques_and_ans(self, ctx, key:str = "str", language: str = "english") -> None:
		#await self.get_quiz_details(ctx, quiz)
		user_id = random.randint(12288, 18829)
		file = {
			'userid' : (None, user_id),
			'quiz_key': (None, key)
		}
		response = requests.post(self.host + "/practice", headers = self.headers, files = file)
		response_data = response.json()
		if response_data["Error"] != 0:
			return await ctx.send(f"```\n{response_data['message']}\n```")
		quiz_data = response_data["data"]
		
		questions = quiz_data["questions"]
		ques_lang = "question_eng" if language.lower() == "english" else "question_hin"
		ans_lang = ["ans_eng_a", "ans_eng_b", "ans_eng_c", "ans_eng_d", "ans_eng_e", "ans_eng_f"] \
			if language.lower() == "english" else \
			["ans_hin_a", "ans_hin_b", "ans_hin_c", "ans_hin_d", "ans_hin_e", "ans_hin_f"]
		
		for i, data in enumerate(questions):
			embed = discord.Embed(color = discord.Colour.random())
			options = []
			question = data[ques_lang].strip("<style>img { max-width: 100%}</style>")
			not_question = await self.get_not_question(question)
			#ans_num = int(data["right_ans"])
			#answer = data[ans_lang[ans_num]]
			raw_question = question.replace(" ", "+")
			question_url = google_question + raw_question
			for index in range(4):
				#options += f"{index+1}. {} {'✅' if ans_num == index else ''}\n"
				options.append(data[ans_lang[index]])
			value = await self.google_search(question_url, options, not_question)
			embed.description = f"{i+1}. [{question}]({question_url})\n{value}"
			await ctx.send(embed = embed)
			await self.google_search_two(ctx, question_url, options, not_question)
			await self.direct_search_result(ctx, question_url, options)
			
	# def rep(self, num):
	# 	if num == 0: num = 1
	# 	elif num == 1: num = 2
	# 	elif num == 2: num = 3
	# 	elif num == 3: num = 0
	# 	return num

	@commands.Cog.listener()
	async def on_ready(self):
		print("Ready!")
		print("Now bot is Online!")
		
	@commands.command()
	async def answer(self, ctx, key:str = "str", language: str = "english"):
		"""To get the answer of the quiz."""
		user_id = random.randint(12288, 18829)
		file = {
			'userid' : (None, user_id),
			'quiz_key': (None, key)
		}
		response = requests.post(self.host + "/practice", headers = self.headers, files = file)
		response_data = response.json()
		if response_data["Error"] != 0:
			return await ctx.send(f"```\n{response_data['message']}\n```")
		quiz_data = response_data["data"]
		import pprint; pprint.pprint(quiz_data)
		questions = quiz_data["questions"]
		ques_lang = "question_eng" if language.lower() == "english" else "question_hin"
		ans_lang = ["ans_eng_a", "ans_eng_b", "ans_eng_c", "ans_eng_d", "ans_eng_e", "ans_eng_f"] \
			if language.lower() == "english" else \
			["ans_hin_a", "ans_hin_b", "ans_hin_c", "ans_hin_d", "ans_hin_e", "ans_hin_f"]
		embed = discord.Embed(color = discord.Colour.random())
		description = ""
		for i, data in enumerate(questions):
			question = data[ques_lang].strip("<style>img { max-width: 100%}</style>")
			right_ans = data.get("right_ans")
			if not right_ans:
				return await self.get_ques_and_ans(ctx, key, language)
			ans_num = self.rep(int(right_ans)) if i+1 == 8 else int(data["right_ans"])
			answer = data[ans_lang[ans_num]]
			description += f"{'0' if i+1<10 else ''}{i+1}. {answer} ({int(ans_num)+1})\n"
		embed.description = f"```\n{description}\n```"
		await ctx.send(embed = embed)
		
	@commands.command()
	async def quiz(self, ctx, quiz_type: str = "paid", number: int = 1):
		"""To get the quiz details."""
		await self.get_quiz_details(ctx, quiz_type, number)
		
	@commands.command()
	async def gans(self, ctx, key:str = "str", language: str = "english"):
		"""To get the google answer."""
		await self.get_ques_and_ans(ctx, key, language)

	@commands.command()
	async def openai(self, ctx, *, question: str):
		"""To get open ai search result."""
		openai.api_key = "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"
		response = openai.Completion.create(
			model="text-davinci-003",
			prompt=question,
			temperature=0.7,
			max_tokens=256,
			top_p=1,
			frequency_penalty=0,
			presence_penalty=0
		)
		res = response.choices[0].text
		embed = discord.Embed(color = discord.Colour.random())
		embed.description = f"```\n{res}\n```"
		await ctx.send(embed = embed)
		
def setup(client):
	client.add_cog(Quizophy(client))
