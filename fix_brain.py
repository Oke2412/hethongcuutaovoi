import codecs
import re

with codecs.open('core/brain.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix the broken string literals
content = content.replace('"[Ngư\u1eddi dùng đã g\u1eedi m\u1ed9t b\u1ee9c \u1ea3nh. Hãy x\u1eed lý nó.]\n"', '"[Ngư\u1eddi dùng đã g\u1eedi m\u1ed9t b\u1ee9c \u1ea3nh. Hãy x\u1eed lý nó.]\\n"')
content = content.replace('"[Ngư\u1eddi dùng đã g\u1eedi m\u1ed9t b\u1ee9c \u1ea3nh. Hãy x\u1eed lý nó.]\r\n"', '"[Ngư\u1eddi dùng đã g\u1eedi m\u1ed9t b\u1ee9c \u1ea3nh. Hãy x\u1eed lý nó.]\\n"')

# Just to be extremely safe, I will re-write the entire method using a clean script
# Let's write the whole file to ensure it's correct.
