"""REST channel for KisanBol: lets IVR, WhatsApp bots or mobile apps reuse the same engine.

Run:  pip install fastapi uvicorn python-multipart   then   uvicorn api:app --port 8000
POST /ask  (multipart: audio file OR text field, optional language, weather_scenario, lat/lon (nearest covered mandi
when none is named) and view_days 1, 3 or 7)"""
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

import kisanbol_engine as engine

app = FastAPI(title="KisanBol API", version="1.0")


@app.get("/health")
def health():
    return {"ok": True, "gnani": engine.gnani_configured(), "evon": engine.evon_configured(),
            "agmarknet": bool(engine.AGMARKNET_API_KEY)}


@app.post("/ask")
async def ask(audio: UploadFile | None = File(None), text: str | None = Form(None),
              language: str = Form("auto"), speak: bool = Form(True), weather_scenario: str | None = Form(None),
              lat: float | None = Form(None), lon: float | None = Form(None), view_days: int | None = Form(None)):
    data = await audio.read() if audio else None
    try:
        res = engine.run_pipeline(audio=data, text=text, language=language, speak=speak and engine.gnani_configured("tts"),
                                  filename=audio.filename if audio else "query.wav", weather_scenario=weather_scenario,
                                  location=(lat, lon) if lat is not None and lon is not None else None,
                                  view_days=view_days if view_days in (1, 3, 7) else None)
    except engine.KisanBolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return res.to_dict()
