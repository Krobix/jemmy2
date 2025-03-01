from llama_cpp import Llama
import discord
import os, random

MODEL_PATH = f"{os.getenv('HOME')}/jemmy_v1.gguf"
llm = Llama(MODEL_PATH, n_ctw=2048)
replace_channel_names = ["general", "nsfw", "adults-only", "vent"]
bot_name = "jemmy"

with open(f"{os.getenv('HOME')}/token.txt", "r") as f:
    token = f.read()
    token = token.strip()

def getcn(msg):
    if len(replace_channel_names)<1:
        if isinstance(msg.channel, discord.channel.DMChannel):
            return msg.author.name
        else:
            return msg.channel.name
    else:
         return random.choice(replace_channel_names)

def create_prompt(messages, max_len=2048):
    tokenl = []
    strs = []
    cstr = f"<|channel {getcn(messages[0])}|>"
    for m in messages:
        s = f"<|message {m.author.name}|>{m.content}<|endmessage|>"
        strs.append(s)
        tokenl.append(llm.tokenize(s.encode("utf-8")))
    while True:
        tokenlen = 0
        for t in tokenl:
            tokenlen+=len(t)
        if tokenlen>max_len:
            strs.pop(0)
            tokenl.pop(0)
        else:
            break
    return cstr+("".join(strs))+f"<|message {bot_name}|>"

class Jemmy(discord.Client):
    async def on_ready(self):
        print("Logged in. Loading model...")

    async def on_message(self, msg):
        is_dm = isinstance(msg.channel, discord.channel.DMChannel)
        is_reply = (msg.reference is not None)
        if is_reply:
            is_reply_to_me = (await msg.channel.fetch_message(msg.reference.message_id)).author.id == self.user.id
        else:
            is_reply_to_me = False
        if msg.author.id == self.user.id:
            return

        if is_dm or (str(self.user.id) in msg.content) or is_reply_to_me:
            async with msg.channel.typing():
                print(f"Received message: {msg.author.name}")
                print(f"Content: {msg.content}\n\n")
