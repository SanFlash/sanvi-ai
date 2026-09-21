"""SANVI natural-language planner."""
from __future__ import annotations
import base64, json, os
from pathlib import Path
from typing import Any
import httpx

SYSTEM = """You are SANVI, a Windows + Android computer-use planner.
Return ONLY valid JSON: {"done":false,"reply":"short response","actions":[{"tool":"...","args":{...}}]}
Available tools: open_app, close_app, browser_open, browser_search, type_text, press_keys, click_xy, move_mouse, double_click, right_click, scroll, clipboard_get, clipboard_set, screenshot, camera_photo, camera_preview, system_info, list_files, read_file, write_file, delete_file, list_processes, android_devices, android_open, android_tap, android_tap_text, android_type, android_key, android_screenshot, run_powershell, run_cmd.
Rules: use the smallest number of actions; never invent success; use screenshots before coordinate GUI decisions; use Android UI/screenshot before guessing coordinates; understand Hindi/Hinglish; respect current task context; do not bypass credentials/OTP/CAPTCHA; do not generate arbitrary destructive commands unless explicitly requested; never output code instead of a tool call."""

def _image_data(path: str) -> str:
    p=Path(path)
    mime="image/png" if p.suffix.lower()==".png" else "image/jpeg"
    return "data:"+mime+";base64,"+base64.b64encode(p.read_bytes()).decode("ascii")

def _extract_json(text: str) -> dict[str, Any]:
    text=text.strip()
    if text.startswith("```"): text=text.split("\n",1)[1].rsplit("```",1)[0].strip()
    start,end=text.find("{"),text.rfind("}")
    if start<0 or end<=start: raise ValueError("Planner did not return JSON.")
    value=json.loads(text[start:end+1])
    if not isinstance(value,dict): raise ValueError("Planner JSON is not an object.")
    return value

def plan(command: str, screenshot_path: str|None=None, context: list[dict[str,str]]|None=None) -> dict[str,Any]:
    provider=os.getenv("SANVI_AI_PROVIDER","openai").lower().strip()
    model=os.getenv("SANVI_AI_MODEL","gpt-5.6-luna").strip()
    parts=[{"type":"input_text","text":"User command:\n"+command}]
    if context: parts.append({"type":"input_text","text":"Recent task context:\n"+json.dumps(context[-8:])})
    if screenshot_path and Path(screenshot_path).exists(): parts.append({"type":"input_image","image_url":_image_data(screenshot_path)})
    if provider=="ollama":
        prompt=SYSTEM+"\n\n"+ "\n".join(p.get("text","") for p in parts if p.get("type")=="input_text")
        with httpx.Client(timeout=90) as client:
            r=client.post(os.getenv("SANVI_OLLAMA_URL","http://127.0.0.1:11434/api/chat"),json={"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],"stream":False,"format":"json"})
            r.raise_for_status(); return _extract_json(r.json()["message"]["content"])
    key=os.getenv("OPENAI_API_KEY","").strip()
    if not key: raise RuntimeError("No AI planner configured. Set OPENAI_API_KEY, or use SANVI_AI_PROVIDER=ollama.")
    payload={"model":model,"input":[{"role":"system","content":[{"type":"input_text","text":SYSTEM}]},{"role":"user","content":parts}],"text":{"format":{"type":"json_object"}}}
    with httpx.Client(timeout=90) as client:
        r=client.post("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},json=payload)
        r.raise_for_status(); data=r.json()
    output=data.get("output_text","")
    if not output:
        chunks=[]
        for item in data.get("output",[]):
            for content in item.get("content",[]):
                if content.get("type") in {"output_text","text"}: chunks.append(content.get("text",""))
        output="".join(chunks)
    return _extract_json(output)


def describe_image(image_path: str, question: str = "Describe what is visible in this image.") -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for camera vision.")
    model = os.getenv("SANVI_AI_MODEL", "gpt-5.6-luna").strip()
    prompt = question + "\nAnswer concisely and only describe information actually visible."
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": "You are SANVI's visual perception module. Do not invent details. Describe only what is visible."}]},
            {"role": "user", "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": _image_data(image_path)}
            ]}
        ]
    }
    with httpx.Client(timeout=90) as client:
        r = client.post("https://api.openai.com/v1/responses", headers={"Authorization": "Bearer "+key, "Content-Type": "application/json"}, json=payload)
        r.raise_for_status()
        data = r.json()
    output = data.get("output_text", "")
    if output:
        return output.strip()
    chunks=[]
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text","text"}:
                chunks.append(content.get("text",""))
    return "".join(chunks).strip()
