import os


DEEPSEEK_API_KEY = ''

CLOSEAI_API_KEY = ''
OPENAI_API_BASE = "https://api.openai-proxy.org/v1"

PINECE_API_KEY = ''

os.environ['OPENAI_API_BASE'] = OPENAI_API_BASE
os.environ['OPENAI_API_KEY'] = CLOSEAI_API_KEY
