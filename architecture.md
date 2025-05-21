[ Robot Framework run ]
        |
        v
[ realtimelogger listener ] -----> [ Webservice (API) ] -----> [ Dashboard frontend (grafieken)]


| Component          | Wat is het?                  | Wanneer starten?     | Voorbeeld                                                        |
| ------------------ | ---------------------------- | -------------------- | ---------------------------------------------------------------- |
| **Robot run**      | Voert je tests uit           | Als laatste          | `robot --listener realtimelogger.listener.RealTimeLogger tests/` |
| **Listener**       | Stuurt testevents door       | Draait mee met Robot | Wordt automatisch gestart via `--listener`                       |
| **Webservice**     | Ontvangt testevents via HTTP | **Vooraf** starten   | `python backend/app.py` of `flask run`                           |
| **Dashboard (UI)** | Toont frontend in browser    | Meestal altijd aan   | React/Vue app via `npm run dev`                                  |
