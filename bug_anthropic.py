import anthropic
import os


print(len(os.environ.get("ANTHROPIC_API_KEY")))
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens = 1024,
    system="""You are a senior QA engineer. Analyse bug reports and return ONLY a json object with exactly these fields:
    {
    "Severity":"Critical/High/Medium/Low",
    "priority":"P0/P1/P2/P3",
    "component":"which part of the app is affected",
    "suggestion":"One clear fix direction"
    }
    return ONLY the json. No explanation. No markdown""",
    messages=[
        {
            "role": "user",
            "content":"User profile picture not updating after save."
        }])

#Login button not working on mobile Safari. App crashes after clicking.
# Payment page not loading on slow 3G connections.
# User profile picture not updating after save

print(message.content[0].text)
