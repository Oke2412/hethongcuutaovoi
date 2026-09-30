import os, glob, json
brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
log_files.sort(key=lambda x: os.path.getmtime(x))
recent_logs = log_files[-4:-1]

clean_text = ''
agent_turns = 0
for log in recent_logs:
    try:
        with open(log, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                source = data.get('source')
                
                if source == 'USER_EXPLICIT':
                    content = data.get('content', '').strip()
                    if content:
                        clean_text += f'\n[User]: {content}\n'
                        
                elif source == 'MODEL':
                    tool_calls = data.get('tool_calls', [])
                    # ONLY KEEP if there are NO tool calls (final response)
                    if not tool_calls:
                        content = data.get('content', '') or ''
                        if '<CONTEXT_SUMMARY>' in content:
                            content = content.split('</CONTEXT_SUMMARY>')[-1]
                        if '<SYSTEM_MESSAGE>' in content:
                            content = content.split('</SYSTEM_MESSAGE>')[-1]
                        
                        start = content.find('<thinking>')
                        end = content.find('</thinking>')
                        if start != -1 and end != -1:
                            content = content[:start] + content[end+11:]
                            
                        content = content.strip()
                        if content:
                            clean_text += f'\n[Agent]: {content}\n'
                            agent_turns += 1
    except Exception as e: pass

print(f'Final Agent Turns: {agent_turns}')
print(f'File Size: {len(clean_text.encode("utf-8")) / 1024:.2f} KB')

out_path = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/raw_chat_delta_smart.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(clean_text)
