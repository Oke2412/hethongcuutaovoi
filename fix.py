import re
with open('core/llm.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('"energy": {
                        "type": "integer"
                    }', '"energy": {
                        "type": "integer",
                        "description": "Thang diem 1-10"
                    }')
c = c.replace('"mood": {
                        "type": "integer"
                    }', '"mood": {
                        "type": "integer",
                        "description": "Thang diem 1-10"
                    }')
c = c.replace('"health": {
                        "type": "integer"
                    }', '"health": {
                        "type": "integer",
                        "description": "Thang diem 1-10"
                    }')
with open('core/llm.py', 'w', encoding='utf-8') as f:
    f.write(c)
