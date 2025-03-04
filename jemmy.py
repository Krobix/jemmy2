from llama_cpp import Llama
import discord
import os, random

MODEL_PATH = "/xb/llms/mistral-7b-v0.1.Q5_K_M.gguf"
TEMP = 1.4
REP_PENALTY=1.18
llm = Llama(MODEL_PATH, n_ctx=2048, n_threads=6, n_threads_batch=12)

replace_channel_names = []
bot_name = "jemmy"
def_convo_len = 20

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
    cstr = ""
    for m in messages:
        s = f"{m.author.name}: {m.clean_content}\n\n"
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
    return cstr+("".join(strs))+f"{bot_name}: "

class Jemmy(discord.Client):
    async def on_ready(self):
        print("Logged in.")

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
                print(f"Content: {msg.clean_content}\n\n")
                messages = [msg]
                if is_reply:
                    while messages[0].reference is not None:
                        nm = await msg.channel.fetch_message(messages[0].reference.message_id)
                        messages.insert(0, nm)
                else:
                    messages = []
                    #async for m in msg.channel.history(limit=def_convo_len):
                    #    messages.append(m)
                    messages.append(msg)
                prompt = create_prompt(messages)
                out = llm(prompt=prompt, max_tokens=256, temperature=TEMP, stop=["\n\n"], repeat_penalty=1.18)
                pl = len(prompt)
                outs = out["choices"][0]["text"]
                await msg.reply(outs)

intents = discord.Intents.default()
intents.message_content = True

jemmy = Jemmy(intents=intents)

jemmy.run(token)