import os, glob, json

def extract_chat():
    brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
    log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
    log_files.sort(key=lambda x: os.path.getmtime(x))
    recent_logs = log_files[-4:-1] # Skip the active one to avoid lock

    clean_text = ''
    for log in recent_logs:
        try:
            with open(log, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    source = data.get('source')
                    if source in ['USER_EXPLICIT', 'MODEL']:
                        content = data.get('content', '') or ''
                        if len(content) > 5000: continue
                        if '<CONTEXT_SUMMARY>' in content:
                            content = content.split('</CONTEXT_SUMMARY>')[-1]
                        if '<SYSTEM_MESSAGE>' in content:
                            content = content.split('</SYSTEM_MESSAGE>')[-1]
                        
                        start = content.find('<thinking>')
                        end = content.find('</thinking>')
                        if start != -1 and end != -1:
                            content = content[:start] + content[end+11:]
                            
                        content = content.strip()
                        if not content: continue
                        
                        if source == 'USER_EXPLICIT':
                            clean_text += f'\n[User]: {content}\n'
                        elif source == 'MODEL':
                            clean_text += f'\n[Agent]: {content}\n'
        except Exception as e: pass

    out_path = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/raw_chat_delta.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(clean_text)
    print(f"Extracted clean log to {out_path} ({len(clean_text)/1024:.2f} KB)")

if __name__ == '__main__':
    extract_chat()
