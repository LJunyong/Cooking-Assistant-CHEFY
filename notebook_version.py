from openai import OpenAI
import speech_recognition as sr
import my_fridge, stage
import os, uuid, asyncio
from edge_tts import Communicate
from pydub import AudioSegment
from pydub.playback import play 

client = OpenAI(api_key="yourkey")
R = stage.R
S = stage.stage
I = stage.I
index = 1

recogn = sr.Recognizer()
mic = sr.Microphone()
recogn.pause_threshold = 1.3                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

v = "ko-KR-SunHiNeural"
rate = "+30%"
dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(dir, exist_ok=True)

def speak(t):
    i = uuid.uuid4().hex
    mp3_path = os.path.join(dir, f"{i}.mp3")
    wav_path = os.path.join(dir, f"{i}.wav")
    try:
        asyncio.run(Communicate(text=t, voice=v, rate=rate).save(mp3_path))
        AudioSegment.from_mp3(mp3_path).export(wav_path, format="wav")
        play(AudioSegment.from_wav(wav_path))
    except Exception as e:
        pass
    finally:
        for p in (mp3_path, wav_path):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
Prem=["안녕하세요! 요리 도우미 CHEFY입니다. 요리도중 질문이 있으면 말씀해 주세요."]
print("안녕하세요! 요리 도우미 CHEFY입니다. 요리도중 질문이 있으면 말씀해 주세요.")                                                                                                                                                                                                                                                                                                                     
speak("안녕하세요! 요리 도우미 쉐피입니다. 요리도중 질문이 있으면 말씀해 주세요.")
SYSTEM_PROMPT = ("너는 요리 어플의 음성 요리 도우미 챗봇, 쉐피야. 사용자에게 친절하고 부드러운 말투로 요리지식에 대한 구체적인 대답을 줘.\n"
                 "1. 사용자가 요리와 관련없는 질문을 하거나 대답을 요구하면, 무조건 요리에 관련된 질문을 해달라고 출력해.\n"
                 "2. 노이즈나 의미없는 말로 판단되면 무조건 \"\" 를 출력해줘.\n"
                 "3. 대화 맥락이나 쉐피의 직전 답변 내용에 대한 질문은 무조건 대답해줘.\n"
                 "3. 감정적인 대답을 대신 대처법을 안내해줘.\n"
                 "4. 인사말 예시: 안녕하세요! 요리 도우미 쉐피입니다. 요리 도중 질문이 있으면 언제든지 말씀해 주세요!\n"
                 "5. 요리 도중 대답은 구체적으로, 하지만 140자 안쪽으로 대답해.\n"
                 "6. 넌 현재 요리 레시피, 메뉴와 현재 요리 단계에 대해서 질문을 받아야해, 다음 요리 단계에 대한 내용은 절대 답변하지마.\n"
                 )

while True:
    try:
        with mic as s:
            print("음성 인식중..")
            a = recogn.listen(s, timeout= None, phrase_time_limit=30)

        user_input = recogn.recognize_google(a, language="ko-KR")
        print("입력:", user_input)

        if user_input in ["다음", "다음 단계"]:
            if index < len(S) - 1:
                index += 1
                print(f"다음 단계입니다. {S[index]}")
                speak(f"다음 단계입니다. {S[index]}")
                Prem.append(r)
            else:
                print("모든 단계가 끝났습니다. 맛있게 드세요!")
                speak("모든 단계가 끝났습니다. 맛있게 드세요!")
                break
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
        print(r)
        speak(r)
        Prem.append(r)
    except sr.UnknownValueError:
        print("음성을 인식하지 못했어요.")
        continue
    except sr.WaitTimeoutError:
        continue
    except Exception as e:
        continue
