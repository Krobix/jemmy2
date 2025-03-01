import json, os, random

data_folder = "/home/brendon/Documents/dexport/"
#These are per file
conversations = 1100
conversation_msg_range = (5, 21)

training_file = "training_data.txt"
eval_file = "eval_data.txt"

trainings = ""
evals = ""

def convo_to_str(cname, convo):
    val = ("")
    val+=f"<|channel {cname}|>"
    for msg in convo:
        val+=f"<|message {msg["author"]["name"]}|>{msg["content"]}<|endmessage|>"
    val+="<|endoftext|>\n"
    return val


for fn in os.listdir(data_folder):
    with open(data_folder+fn, "r") as f:
        eval_convos_amount = int(conversations * 0.1)
        print(f"Reading {fn}...")
        data = json.load(f)
        messages = data["messages"]
        cname = data["channel"]["name"]
        convos = []
        while (len(convos) < conversations+eval_convos_amount) and len(messages)>0:
            clen = random.randrange(*conversation_msg_range)
            if clen>len(messages):
                break
            print(f"Conversation length: {clen}")
            c=[]
            for i in range(clen):
                msg = messages.pop(0)
                c.append(msg)
            convos.append(c)
        if len(convos)<conversations+eval_convos_amount:
            eval_convos_amount = int(len(convos)*0.1)
        for c in convos[:len(convos)-eval_convos_amount]:
            cs=convo_to_str(cname, c)
            trainings+=cs
        for c in convos[len(convos) - eval_convos_amount:]:
            cs=convo_to_str(cname,c)
            evals+=cs

with open(training_file, "w") as f:
    f.write(trainings)

with open(eval_file, "w") as f:
    f.write(evals)