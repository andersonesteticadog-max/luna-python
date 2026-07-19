def carregar_system_prompt():
    with open("prompts/system_prompt.md", "r", encoding="utf-8") as f:
        return f.read()
