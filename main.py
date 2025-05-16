from fastapi import FastAPI, Request, HTTPException
import os
from dotenv import load_dotenv
import google.generativeai as genai
from weather import extract_city, extract_day, get_weather_for_day, get_forecast

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()
chat_store = {}

@app.get("/")
async def root():
    return {"message": "Welcome to the Gemini chatbot API. Use POST /chat to ask weather questions."}

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("message", "").strip()
    client_ip = request.client.host

    if not user_input:
        raise HTTPException(status_code=400, detail="No message provided.")

    try:
        city = extract_city(user_input)
        day_offset = extract_day(user_input)

        if "weather" in user_input.lower():
            if not city:
                reply = "Please specify a city. Example: 'What's the weather in Mumbai tomorrow?'"
            elif any(word in user_input.lower() for word in ["week", "forecast", "7 day"]):
                reply = get_forecast(city)
            else:
                reply = get_weather_for_day(city, day_offset or 0)
        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            convo = model.start_chat()
            response = await convo.send_message_async(user_input)
            reply = response.text

        if client_ip not in chat_store:
            chat_store[client_ip] = []
        chat_store[client_ip].append({"user": user_input, "bot": reply})

        return {
            "reply": reply,
            "using_model": "OpenWeatherMap" if "weather" in user_input.lower() else "Gemini"
        }

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def history(request: Request):
    client_ip = request.client.host
    return {"client_ip": client_ip, "chat_history": chat_store.get(client_ip, [])}
