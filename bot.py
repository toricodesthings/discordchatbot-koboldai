import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import os

load_dotenv()
botToken = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

web_endpoint = "http://127.0.0.1:5000"
character_list = []

for nfile in os.listdir("characterfiles"):
    if nfile.endswith('.json'):
        with open(os.path.join("characterfiles", nfile)) as f:
            character_data = json.load(f)
            character_list.append(character_data)

if len(character_list) == 1:
    cdata = character_list[0]
    
char_name = cdata["char_name"]
char_greeting = cdata["char_greeting"]

conversation_history = f"{char_name}'s Persona: {cdata['char_persona']}\n" + \
                       '<START>\n' + \
                       f"{char_name}: {char_greeting}"

num_lines_to_keep = 20

a_thread_id = int()
thread = None

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    guild = bot.get_guild("Insert Guild ID")
    bot_member = guild.get_member(bot.user.id)
    await bot_member.edit(nick=char_name)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global thread
    global a_thread_id
    author = message.author
    if bot.user.mentioned_in(message) and 'Start' in message.content:
        all_threads = message.channel.threads
        for i in all_threads:
            if i.id == a_thread_id:
                await message.channel.send("There is already an active thread with this bot.")
                return
        thread = await message.channel.create_thread(
            name="ChatBot",
            type=discord.ChannelType.public_thread
        )
        a_thread_id = thread.id
        global char_greeting
        await thread.send(char_greeting)
    elif isinstance(message.channel, discord.Thread) and message.channel.id == a_thread_id:
        global conversation_history
        global char_name
        global num_lines_to_keep
        global web_endpoint
        content = message.content
        if content.lower() == "session terminate":
            await thread.delete()
            conversation_history = f"{char_name}'s Persona: {cdata['char_persona']}\n" + \
                       '<START>\n' + \
                       f"{char_name}: {char_greeting}"
            return
        
        try: 
            conversation_history += f'You: {content}\n'
            prompt = {
                "prompt": '\n'.join(conversation_history.split('\n')[-num_lines_to_keep:]) + f'{char_name}:',
                "use_story": False,
                "use_memory": False,
                "use_authors_note": False,
                "use_world_info": False,
                "max_context_length": 1838,
                "max_length": 150,
                "rep_pen": 1.2,
                "rep_pen_range": 1024,
                "rep_pen_slope": 0.9,
                "temperature": 0.55,
                "tfs": 0.9,
                "top_a": 0,
                "top_k": 0,
                "top_p": 0.95,
                "typical": 1,
                "sampler_order": [
                    6, 0, 1, 2,
                    3, 4, 5
                ]
            }
            response = requests.post(f"{web_endpoint}/api/v1/generate", json=prompt)
            if response.status_code == 200:
                result = response.json()['results']
                text = (result[0]['text']).split("You: ")
                response_text = text[0].strip().replace(f"{char_name}:", "").strip()
                await thread.send(response_text)
                conversation_history = conversation_history + f'{char_name}: {response_text}\n'
            else:
                await thread.send("Error Retrieving Response")
            
        except requests.exceptions.ConnectionError:
            await thread.send("End Point Error")
    await bot.process_commands(message)

# Run the bot using your bot token
bot.run(botToken)
