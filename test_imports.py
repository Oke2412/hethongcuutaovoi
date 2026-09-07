import sys
import traceback

modules_to_test = [
    'config',
    'db.models',
    'core.omniscience',
    'core.llm',
    'core.llm_tools',
    'core.quest_generator',
    'core.brain',
    'bot.handlers.chat',
    'bot.handlers.location',
    'bot.handlers.status',
    'bot.main',
    'api.main'
]

print("Starting deep import tests...")
all_passed = True
for mod in modules_to_test:
    try:
        __import__(mod)
        print(f"[OK] {mod}")
    except Exception as e:
        print(f"[ERROR] Failed to import {mod}:")
        traceback.print_exc()
        all_passed = False

if all_passed:
    print("All modules imported successfully! No SyntaxErrors or missing dependencies detected at module level.")
    sys.exit(0)
else:
    print("Some modules failed to import.")
    sys.exit(1)
