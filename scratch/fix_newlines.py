app_path = r"c:\Users\SHREYAS\Desktop\MediScan-AI-main\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace any broken multiline replace calls
broken1 = '.replace("\n", "<br/>")'
broken2 = '.replace("\r\n", "<br/>")'

text = text.replace(broken1, r'.replace("\n", "<br/>")')
text = text.replace(broken2, r'.replace("\n", "<br/>")')

with open(app_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed newlines replacement")
