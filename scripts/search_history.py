import os, glob, json

brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
log_files.sort(key=lambda x: os.path.getmtime(x))

for log in log_files[-10:]:
    session_id = log.split(os.sep)[-4]
    try:
        with open(log, 'r', encoding='utf-8') as f:
            for line in f:
                if 'run_multi_turn_extraction' in line or '15,000' in line or 'tối ưu' in line.lower():
                    data = json.loads(line)
                    if data.get('source') == 'USER_EXPLICIT':
                        print(f"\n[Session {session_id[:8]}] USER SAID:\n{data.get('content')}")
                    elif data.get('source') == 'MODEL':
                        content = data.get('content', '')
                        if 'run_multi_turn_extraction' in content:
                            print(f"\n[Session {session_id[:8]}] MODEL ACTION:\n{content[:500]}")
    except Exception as e:
        pass
