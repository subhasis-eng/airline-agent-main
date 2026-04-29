import gradio as gr
import requests
import json
import time
import threading

FASTAPI_URL = "http://localhost:8000"  # FastAPI host & port


# -------------------------------
# Upload PDF to FastAPI
# -------------------------------
def upload_pdf_to_api(pdf_file):
    if pdf_file is None:
        return "Please upload a PDF", "", ""

    files = {"file": (pdf_file.name, open(pdf_file.name, "rb"), "application/pdf")}
    response = requests.post(f"{FASTAPI_URL}/upload", files=files)

    if response.status_code != 200:
        return f"Error: {response.text}", "", ""

    data = response.json()

    events_json = json.dumps(data.get("events", []), indent=2)
    routing_json = json.dumps(data.get("routing", []), indent=2)

    return "Upload Successful!", events_json, routing_json


# -------------------------------
# Live Logs Poller
# -------------------------------
stop_polling = False


def poll_logs():
    logs_display = ""

    while not stop_polling:
        try:
            r = requests.get(f"{FASTAPI_URL}/logs")
            logs = r.json().get("logs", [])

            logs_display = json.dumps(logs, indent=2)
            log_box.update(logs_display)

        except Exception as e:
            pass

        time.sleep(2)


# -------------------------------
# Gradio UI Layout
# -------------------------------
with gr.Blocks(title="Airline IRROPS Dashboard") as ui:

    gr.Markdown(
        "# ✈️ Airline IRROPS Event Analyzer\nUpload operational PDFs → Parse → Route → Process Agents"
    )

    with gr.Row():
        pdf_input = gr.File(label="Upload PDF File", file_types=[".pdf"])
        submit_btn = gr.Button("Process PDF")

    with gr.Row():
        events_output = gr.Code(label="Extracted Events (JSON)")
        routing_output = gr.Code(label="Agent Routing Decisions (JSON)")

    status_box = gr.Textbox(label="Status")
    log_box = gr.Code(label="Real-Time Task Worker Logs")

    submit_btn.click(
        fn=upload_pdf_to_api,
        inputs=pdf_input,
        outputs=[status_box, events_output, routing_output],
    )

    # Start log polling thread
    t = threading.Thread(target=poll_logs, daemon=True)
    t.start()


# -------------------------------
# Launch Gradio Server
# -------------------------------
ui.launch(server_name="0.0.0.0", server_port=7860)
