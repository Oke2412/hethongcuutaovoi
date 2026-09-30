import os, glob, json, re
brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
log_files.sort(key=lambda x: os.path.getmtime(x))
recent_logs = log_files[-5:]

clean_text = ''
for log in recent_logs:
    try:
        for line in open(log, 'r', encoding='utf-8'):
            data = json.loads(line)
            source = data.get('source')
            content = data.get('content', '') or ''
            
            # Filter out context summary and system messages
            content = re.sub(r'<CONTEXT_SUMMARY>.*?</CONTEXT_SUMMARY>', '', content, flags=re.DOTALL)
            content = re.sub(r'<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>', '', content, flags=re.DOTALL)
            content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
            
            if source == 'USER_EXPLICIT' and content.strip():
                clean_text += f'\n[User]: {content.strip()}\n'
            elif source == 'MODEL' and content.strip():
                clean_text += f'\n[Agent]: {content.strip()}\n'
    except Exception as e: pass

print(f'Total length of pure chat text: {len(clean_text)} chars')
print(f'File size: {len(clean_text.encode("utf-8")) / 1024:.2f} KB')
