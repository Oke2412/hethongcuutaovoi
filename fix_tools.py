
import re

with open('core/llm.py', 'r', encoding='utf-8') as f:
    text = f.read()

reps = {
    r'Truy van lich su, memory, va bieu do nhan qua \(RAG\)\. GOI TOOL NAY KHI thieu ngu canh \(VD: user hoi \'tai sao\?\', \'the nao\?\', hoac nhac toi su kien cu\)\.': 'Query history, memory, and causal graph (RAG). CALL THIS TOOL when lacking context (e.g. user asks why, how, or mentions past events).',
    r'Cau truy van tim kiem tu khoa \(VD: \'giac ngu\', \'tap gym\', \'buon\'\)': 'Keyword search query (e.g. sleep, gym, sad)',
    r'Danh sach thuc the cho Graph Search \(VD: \[\'Sleep\', \'Gym\', \'Mood\'\]\)': 'List of entities for Graph Search',
    r'Tieu hoa van ban tho \(unstructured text\) de trich xuat va luu tru vao GraphRAG \(Neo4j\)\. GOI TOOL NAY khi ban nhan duoc mot doan van ban, lore, hoac text dai chua thong tin moi can ghi nho dai han vao Do thi Nhan qua\.': 'Ingest unstructured text to extract and store in GraphRAG (Neo4j). CALL THIS TOOL to save new lore, long text, or new long-term memories to the Causal Graph.',
    r'Noi dung van ban tho can tieu hoa\.': 'Unstructured text content to ingest.',
    r'Tinh khoang cach \(met\) giua 2 toa do GPS\.': 'Calculate distance in meters between 2 GPS coordinates.',
    r'Huy bo mot nhiem vu \(Quest\)\.': 'Cancel a Quest.',
    r'Danh dau mot nhiem vu \(Quest\) da hoan thanh\.': 'Mark a Quest as completed.',
    r'Quan ly Buff \(Overdrive/Debuff\) hoac Danh hieu \(Title\)\.': 'Manage Buff (Overdrive/Debuff) or Title.',
    r'Cap nhat the trang, nang luong, tam trang, suc khoe, giac ngu\.': 'Update physical status: energy, mood, health, sleep.',
    r'Thang diem 1-10': 'Scale 1-10',
    r'Tao moi, cap nhat tien do, hoac xoa du an\.': 'Create, update progress, or delete a project.',
    r'Them, cap nhat level/EXP, hoac xoa ky nang\.': 'Add, update level/EXP, or delete a capability/skill.',
    r'Cong hoac Tru Tin chi \(Credits\) cua user\.': 'Add or subtract Credits for the user.'
}

for k, v in reps.items():
    text = re.sub(k, v, text)

text = re.sub(r'T.o nhi.m v.*Context\.', 'Create a Quest. IF user does not specify, YOU MUST INFER Title, Description, Reward, Penalty based on Context.', text)

with open('core/llm.py', 'w', encoding='utf-8') as f:
    f.write(text)

