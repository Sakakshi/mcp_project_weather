import requests

# MCP server endpoint and tool
MCP_URL = "http://localhost:4200/call"

def get_weather(city):
    payload = {
        "tool": "get_weather",
        "params": {"city": city}
    }
    response = requests.post(MCP_URL, json=payload)
    if response.ok:
        return response.json()
    else:
        return {"error": response.text}

if __name__ == "__main__":
    result = get_weather("Kolkata")
    print("Weather in Kolkata:", result)
