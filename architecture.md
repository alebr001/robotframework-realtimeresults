[ Robot Framework run ]
        |
        v
[ realtimeresults listener ] -----> [ Webservice (API) ] -----> [ Dashboard frontend (grafieken)]


| Component          | Wat is het?                  | Wanneer starten?     | Voorbeeld                                                        |
| ------------------ | ---------------------------- | -------------------- | ---------------------------------------------------------------- |
| **Robot run**      | Voert je tests uit           | Als laatste          | `robot --listener realtimeresults.listener.RealTimeResults tests/` |
| **Listener**       | Stuurt testevents door       | Draait mee met Robot | Wordt automatisch gestart via `--listener`                       |
| **Webservice**     | Ontvangt testevents via HTTP | **Vooraf** starten   | `python backend/app.py` of `flask run`                           |
| **Dashboard (UI)** | Toont frontend in browser    | Meestal altijd aan   | React/Vue app via `npm run dev`                                  |



          ┌────────────┐
          │ Robot Test │
          └─────┬──────┘
                │
                ▼
          ┌────────────┐
          │  Listener  │
          ├────────────┤
          │ + store_event()
          │ + LokiSink.handle_event()  →  Loki
          └─────┬──────┘
                │
                ▼
          FastAPI backend (serveert je dashboard)
                │
      ┌─────────┴─────────┐
      ▼                   ▼
 /events (store)   /loki_query?query=... → Loki