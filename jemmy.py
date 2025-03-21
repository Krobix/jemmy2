from llama_cpp import Llama
import discord
import os, random, threading, asyncio, secrets, time, copy

MODEL_PATH = ""
TEMP = 1.1
REP_PENALTY=1.18

replace_channel_names = []
bot_name = "jemmy"
def_convo_len = 15

gens = {}
genlock = threading.Lock()

filter_phrases = ["jem.genconvo"]

with open(f"{os.getenv('HOME')}/token.txt", "r") as f:
    token = f.read()
    token = token.strip()

with open(f"{os.getenv('HOME')}/model.txt", "r") as f:
    MODEL_PATH = f.read().strip()

llm = Llama(MODEL_PATH, n_ctx=2048, n_threads=6, n_threads_batch=12)

def gen_thread_run():
    global gens, genlock
    while True:
        genlock.acquire()
        for g in gens.copy():
            prompt = ""
            if gens[g]["out"] is None:
                prompt = gens[g]["prompt"]
                uname = gens[g]["uname"]
                genlock.release()
                out = llm(prompt=prompt, max_tokens=256, temperature=TEMP, stop=["\n", "jemmy:", f"{uname}:"], repeat_penalty=REP_PENALTY)
                genlock.acquire()
                gens[g]["out"] = out
        genlock.release()
        time.sleep(2)

async def generate(prompt):
    genid = secrets.token_hex(32)
    with genlock:
        gens[genid] = {
            "prompt": prompt,
            "uname": prompt.split(":")[0],
            "out": None
        }
    while True:
        await asyncio.sleep(1)
        if not genlock.locked():
            with genlock:
                if gens[genid]["out"] is not None:
                    out = gens[genid]["out"]
                    gens.pop(genid)
                    return out


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
        mcontent = m.clean_content
        for f in filter_phrases:
            while f in mcontent:
                mcontent = mcontent.replace(f, "")
        s = f"{m.author.name}: {mcontent}\n\n"
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

    async def genconvo(self, clean_name, msg, channel):
        webhook = await channel.create_webhook(name=clean_name)
        msglist = []
        iswh=True
        msglist.append(await self.on_message(msg, alwaysreply=True))
        while len(msglist)<def_convo_len:
            #print(f"genconvo(): msglist: {msglist}")
            if iswh:
                wh = webhook
            else:
                wh = None
            newmsg = await self.on_message(msg=msglist[-1], webhook=wh, alwaysreply=True, replace_msglist=msglist)
            msglist.append(newmsg)
            iswh = not iswh
        await webhook.delete()

    async def on_message(self, msg, webhook=None, alwaysreply=False, replace_msglist=None):
        is_dm = isinstance(msg.channel, discord.channel.DMChannel)
        is_reply = (msg.reference is not None)
        if is_reply:
            is_reply_to_me = (await msg.channel.fetch_message(msg.reference.message_id)).author.id == self.user.id
        else:
            is_reply_to_me = False
        if (msg.author.id == self.user.id) and (not alwaysreply):
            return

        if is_dm or (str(self.user.id) in msg.content) or is_reply_to_me or alwaysreply:
            async with msg.channel.typing():
                print(f"Received message: {msg.author.name}")
                print(f"Content: {msg.clean_content}\n\n")
                messages = [msg]
                if replace_msglist is not None:
                    messages = replace_msglist
                elif is_reply:
                    while messages[0].reference is not None:
                        nm = await msg.channel.fetch_message(messages[0].reference.message_id)
                        messages.insert(0, nm)
                else:
                    messages = []
                    #async for m in msg.channel.history(limit=def_convo_len):
                    #    messages.append(m)
                    messages.append(msg)
                prompt = create_prompt(messages)
                out = await generate(prompt)
                outs = out["choices"][0]["text"]
                if webhook is None:
                    nmsg = await msg.reply(outs)
                else:
                    nmsg = await webhook.send(content=outs, wait=True)
                print(f"Sent message: {nmsg.id}")
                return nmsg

        if msg.clean_content.startswith("jem.genconvo"):
            await self.genconvo(msg.author.name, msg, msg.channel)

intents = discord.Intents.default()
intents.message_content = True

jemmy = Jemmy(intents=intents)
gen_thread = threading.Thread(target=gen_thread_run, name="genthread")

gen_thread.start()
jemmy.run(token)