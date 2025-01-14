from flask import Blueprint, request, jsonify, render_template, Response
import time
import json
import io
from app.utils import extract_zip_in_memory, extract_text_from_pdf, process_text_streams_and_store_in_pinecone, generate_answer

routes = Blueprint('routes', __name__)

@routes.route("/")
def home():
    """
    Home route to display the main page.
    """
    return render_template("index.html")

progress_data = {"progress": 0}  # Shared progress state

@routes.route("/progress")
def progress():
    """
    SSE endpoint to send progress updates.
    """
    def generate():
        while progress_data["progress"] < 100:
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(0.5)
        yield f"data: {json.dumps(progress_data)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@routes.route("/upload", methods=["POST"])
def upload_and_process_zip():
    """
    Endpoint to upload a ZIP file, extract PDF files in memory, convert them to TXT, and store them in Pinecone.
    """
    global progress_data
    progress_data["progress"] = 0

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    if not uploaded_file.filename.endswith(".zip"):
        return jsonify({"error": "File must be a ZIP."}), 400

    try:
        file_stream = io.BytesIO(uploaded_file.read())
        extracted_files = extract_zip_in_memory(file_stream)

        pdf_files = {name: content for name, content in extracted_files.items() if name.endswith(".pdf")}

        if pdf_files:
            txt_streams = []
            total_files = len(pdf_files)
            processed_files = 0

            for file_name, pdf_content in pdf_files.items():
                try:
                    text = extract_text_from_pdf(pdf_content)
                    if text.strip():
                        txt_streams.append((file_name.replace(".pdf", ".txt"), io.BytesIO(text.encode("utf-8"))))
                except Exception as e:
                    print(f"Error extracting text from PDF {file_name}: {e}")

                # Update progress
                processed_files += 1
                progress_data["progress"] = int((processed_files / total_files) * 100)

            if txt_streams:
                process_text_streams_and_store_in_pinecone(txt_streams)
                progress_data["progress"] = 100
                return jsonify({"message": "PDF files processed, converted to text, and stored in Pinecone successfully!"})
            else:
                progress_data["progress"] = 100
                return jsonify({"message": "No text could be extracted from the PDFs in the uploaded ZIP."}), 200
        else:
            progress_data["progress"] = 100
            return jsonify({"message": "No PDF files found in the uploaded ZIP."}), 200

    except Exception as e:
        progress_data["progress"] = 100
        return jsonify({"error": str(e)}), 500
    
    
@routes.route("/generate", methods=["POST"])
def generate_summaries():
    """
    Endpoint to generate summaries for key points.
    """
    data = request.get_json()

    key_points = data.get("key_points")
    num_key_points = data.get("num_key_points", 3)

    if not key_points or not isinstance(key_points, list):
        return jsonify({"error": "Invalid key points data."}), 400

    try:
        answers = generate_answer(key_points, num_key_points)
        return jsonify({"answers": answers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
