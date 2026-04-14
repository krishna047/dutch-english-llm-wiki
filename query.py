import subprocess
from pathlib import Path

WIKI_DIR = Path("wiki")

def query_wiki(question: str) -> str:
    wiki_content = ""
    for f in WIKI_DIR.glob("*.md"):
        wiki_content += f"\n\n--- {f.name} ---\n" + f.read_text()

    prompt = f"""You are a knowledgeable assistant. The wiki below was built from Dutch source documents and translated into English.

Answer the following question using ONLY the wiki content. If the answer isn't in the wiki, say so.

## Wiki Content:
{wiki_content}

## Question: {question}

Answer in English:"""

    result = subprocess.run(
        ["ollama", "run", "qwen3:14b"],
        input=prompt.encode(), capture_output=True
    )
    return result.stdout.decode()

# Run interactively
while True:
    q = input("\n🔍 Ask your wiki: ")
    if q.lower() == "exit":
        break
    print("\n💬", query_wiki(q))
