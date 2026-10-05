import json
def test_library():
    with open("data/default_commands.json",encoding="utf-8") as f: data=json.load(f)
    assert len(data)>=300
    assert all(x["title"] and x["command"] and x["description"] for x in data)
