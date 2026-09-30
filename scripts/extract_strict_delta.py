import os, glob, json

brain_dir = 'C:/Users/Asus/.gemini/antigravity/brain'
log_files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript_full.jsonl'))
log_files.sort(key=lambda x: os.path.getmtime(x))

clean_text = ''
agent_turns = 0

# Check the last 15 files to be safe, but only process ones belonging to amazing-nobel
for log in log_files[-15:]:
    # First pass: identify workspace
    is_amazing_nobel = False
    try:
        with open(log, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i > 50: break
                if 'amazing-nobel' in line:
                    is_amazing_nobel = True
                    break
    except: pass
    
    # If not amazing-nobel, skip this session completely to avoid contamination
    if not is_amazing_nobel:
        continue
        
    # Second pass: extract data
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
                    content = data.get('content', '') or ''
                    content = content.strip()
                    if not content: continue
                    
                    if content.startswith('Created At:') or content.startswith('Tool is running') or content.startswith('Encountered error'):
                        continue
                        
                    if '<CONTEXT_SUMMARY>' in content: continue
                    if '<SYSTEM_MESSAGE>' in content: continue
                    
                    start = content.find('<thinking>')
                    end = content.find('</thinking>')
                    if start != -1 and end != -1:
                        content = content[:start] + content[end+11:]
                        content = content.strip()
                        
                    if content:
                        clean_text += f'\n[Agent]: {content[:5000]}\n'
                        agent_turns += 1
    except Exception as e: pass

out_path = 'C:/Users/Asus/Documents/antigravity/amazing-nobel/docs/tien_kiep/raw_chat_delta.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(clean_text)

print(f"Extracted clean text strictly from amazing-nobel. Found {agent_turns} Agent Turns. Size: {len(clean_text)/1024:.2f} KB")
