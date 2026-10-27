import json, sys, urllib.request
def call(name, args):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":args}}).encode()
    req = urllib.request.Request("http://127.0.0.1:9988/mcp", body, {"Content-Type":"application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=600))
    if "error" in r: return "ERR " + json.dumps(r["error"])
    return "\n".join(c.get("text","") for c in r["result"].get("content",[]))
if __name__ == "__main__":
    tool = sys.argv[1]
    if tool == "run":
        code = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else sys.stdin.read()
        print(call("run", {"code": code}))
    else:
        print(call(tool, json.loads(sys.argv[2])))
