import os, glob, json
brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
log_files.sort(key=lambda x: os.path.getmtime(x))
for log in log_files[-4:-1]:
    for line in open(log, 'r', encoding='utf-8'):
        if 'client-env' in line:
            data = json.loads(line)
            print("Source:", data.get('source'))
            print("Type:", data.get('type'))
            print("Keys:", list(data.keys()))
            if 'tool_calls' in data:
                print("Has tool calls")
            break
