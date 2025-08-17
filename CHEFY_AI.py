from openai import OpenAI
from flask import Flask, request, jsonify
from threading import Thread
import queue, os, uuid, asyncio
import stage
from edge_tts import Communicate
from pydub import AudioSegment, generators
import time, socket

text_q = queue.Queue()
reply_q = queue.Queue() 
app = Flask(__name__, static_folder="static")

r, mp3_file = "", ""

@app.route("/push", methods=["POST"])

def push():
    user_input = request.get_json(force=True).get("text", "")
    text_q.put(user_input)
    try:
        r, mp3_file = reply_q.get(timeout=40)
    except:
        return jsonify({"reply": "다시 시도해주세요", "mp3": ""})

    mp3_url = f"http://{request.host}/static/{mp3_file}" if mp3_file else ""
    return jsonify({"reply":r, "mp3":mp3_url})

Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()

client = OpenAI(api_key="yourkey")        
R = stage.R
S = stage.stage
I = stage.I
index = 1

v = "ko-KR-SunHiNeural"
rate = "+30%"
dir = os.path.abspath("static")                 
os.makedirs(dir, exist_ok=True)

def speak(t):

    id = uuid.uuid4().hex
    mp3_path = os.path.join(dir, f"{id}.mp3")

    if (not t) or (not t.strip()) or t.strip() == '""' or t.strip() == '"':
        try:
            q = generators.Sine(1000).to_audio_segment(duration=400).apply_gain(-35)
            q.export(mp3_path, format="mp3")
            return os.path.basename(mp3_path)
        except Exception as e:
            print("error1", e)
            return ""

    try:
        asyncio.run(Communicate(text=t, voice=v, rate=rate).save(mp3_path))
        return os.path.basename(mp3_path)
    except Exception as e:
        print("error2", e)
        return ""

Prem = ["안녕하세요! 요리 도우미 쉐피입니다. 요리도중 질문이 있으면 말씀해 주세요."]
SYSTEM_PROMPT = ("너는 요리 어플의 음성 요리 도우미 챗봇, 쉐피야. 사용자에게 친절하고 부드러운 말투로 요리지식에 대한 구체적인 대답을 줘.\n"
                 "1. 사용자가 요리와 관련없는 질문을 하거나 대답을 요구하면, 무조건 요리에 관련된 질문을 해달라고 출력해.\n"
                 "2. 노이즈나 의미없는 말로 판단되면 무조건 \"\" 를 출력해줘.\n"
                 "3. 대화 맥락이나 직전 답변 내용, 너(쉐피)에 관한 질문은 무조건 대답해줘. 쉐피 호출시에도 대답해줘.\n"
                 "3. 감정적인 대답을 대신 대처법을 안내해줘.\n"
                 "4. 인사말 예시: 안녕하세요! 요리 도우미 쉐피입니다. 요리 도중 질문이 있으면 언제든지 말씀해 주세요!\n"
                 "5. 요리 도중 대답은 구체적으로, 하지만 140자 안쪽으로 대답해.\n"
                 "6. 넌 현재 요리 레시피, 메뉴와 현재 요리 단계에 대해서 질문을 받아야해, 다음 요리 단계에 대한 내용은 절대 답변하지마.\n"
                 )

while True:
    user_input = text_q.get() #블로킹
    print("입력:", user_input)

    if user_input == "dlstk":
        Prem = ["안녕하세요! 요리 도우미 쉐피입니다. 요리도중 질문이 있으면 말씀해 주세요."]
        index = 1
        r = Prem[0]
        mp3_file = speak(r)
        print(r)  
        reply_q.put((r, mp3_file))  
        continue

    if user_input in ["그만", "종료"]:
        r = "대화를 종료합니다."
        mp3_file = speak(r)
        print(r)
        reply_q.put((r, mp3_file))  
        break
    
    if user_input == "stst":
        if index < len(S) - 1:
            index += 1
            r = f"다음 단계입니다. {S[index]}"
            mp3_file = speak(r)
            print(r) 
            reply_q.put((r, mp3_file))
        else:
            r = "모든 단계가 끝났습니다. 맛있게 드세요!"
            mp3_file = speak(r)
            print(r)
            reply_q.put((r, mp3_file))
        Prem.append(r)
        continue


    messages=[
        {"role": "system", "content":SYSTEM_PROMPT},
        {"role": "assistant", "content": f"현재 요리 레시피, 메뉴: {R}, 레시피 전체 재료: {I}, 현재 요리 단계: {S[index]}, 이전 요리 단계: {S[index-1]}, 직전 쉐피의 답변: {Prem[-1]}."},
        {"role": "user", "content": user_input}
    ]

    r = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=150,
    ).choices[0].message.content.strip()

    Prem.append(r)
    print(r)
    mp3_file = speak(r)
    reply_q.put((r, mp3_file))