import json
import os
import time

conv_ids = [
    "2593185d-02de-4307-a31a-f239e5579ed2",
    "681eb3b4-e409-4383-915c-b0f97b6a1452",
    "6ade3e7d-9bc7-411a-b152-8c14aa138805",
    "df402205-0524-4e39-b2ae-21bfc9783e3d",
    "f62a239a-4d92-4d86-b6e7-e3108b3b1c2f",
    "be4f61a4-29db-4d7d-99db-7758f0301717",
    "19ff1cf1-67e3-4def-bffb-1fccb676bf9c",
    "d66b04d5-cb52-420a-8dca-02e8c63a51ec",
    "283d27eb-fefd-400a-a02d-a40109959484",
    "b55107d7-146e-42b0-a498-60696e6ad522",
    "022ada69-d9e7-4e5c-afbf-061cf910f52c",
    "a5bed3c4-d34f-430d-aeb2-4358d789eb2e",
    "1e34764a-f3cd-416e-9e75-f7fa5888732e",
    "fd4b1a92-02a6-40a6-a7b9-7d9098834d54",
    "0371b97b-a722-4dd7-97bb-26d21bda4426",
    "c239886d-8b3a-4b79-95bc-1b9c978921f3"
]

def check_all_done():
    all_results = []
    all_done = True
    for cid in conv_ids:
        path = f"/Users/couozu/.gemini/antigravity/brain/{cid}/.system_generated/logs/transcript.jsonl"
        if not os.path.exists(path):
            all_done = False
            continue
            
        with open(path, 'r') as f:
            lines = f.readlines()
            
        found_message = False
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("tool_calls"):
                    for tc in data["tool_calls"]:
                        if tc.get("name") == "send_message":
                            found_message = True
                            msg = tc.get("argumentsJson")
                            if isinstance(msg, str):
                                import json
                                msg = json.loads(msg).get("Message", "")
                            
                            if "```json" in msg:
                                json_str = msg.split("```json")[1].split("```")[0]
                                all_results.extend(json.loads(json_str))
                            break
                if found_message: break
            except:
                pass
                
        if not found_message:
            all_done = False
            
    return all_done, all_results

while True:
    done, res = check_all_done()
    if done:
        with open('/tmp/vocab.json', 'w') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"All agents finished! Total entries: {len(res)}")
        break
    else:
        time.sleep(2)
