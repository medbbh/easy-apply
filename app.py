from flask import Flask, render_template, jsonify, request, send_file, abort
from pathlib import Path
import threading
import json

from job_scraper import JobScraper
from document_generator import DocumentGenerator

app = Flask(__name__)

class SimpleJobBot:
    def __init__(self):
        self.base_output_dir = Path("job_applications")
        self.base_output_dir.mkdir(exist_ok=True)
        self.current_results = []
        self.is_searching = False
        self.scraper = JobScraper()
        self.doc_generator = DocumentGenerator()
        
    def search_jobs(self, keywords, user_profile=None):
        self.is_searching = True
        self.current_results = []
        
        try:
            results = self.scraper.search_and_prepare(keywords, self.doc_generator, user_profile)
            self.current_results = results
        except Exception as e:
            print(f"Error during job search: {e}")
            self.current_results = []
        finally:
            self.is_searching = False
    
    def get_status(self):
        return {
            'is_searching': self.is_searching,
            'results_count': len(self.current_results),
            'results': self.current_results
        }

job_bot = SimpleJobBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_jobs():
    data = request.get_json() or {}
    keywords = data.get('keywords', [])
    user_profile = data.get('userProfile')
    
    if not keywords:
        return jsonify({'error': 'No keywords provided'}), 400
    
    thread = threading.Thread(target=job_bot.search_jobs, args=(keywords, user_profile))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'Job search started with user profile'})

@app.route('/api/status')
def get_status():
    return jsonify(job_bot.get_status())

@app.route('/api/results')
def get_results():
    return jsonify(job_bot.current_results)

@app.route('/view/resume/<folder_name>')
def view_resume(folder_name):
    """View resume PDF in browser"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        pdf_file = job_folder / "resume.pdf"
        
        if not pdf_file.exists():
            abort(404)
        
        return send_file(pdf_file, mimetype='application/pdf')
        
    except Exception as e:
        print(f"Error viewing resume: {e}")
        abort(500)

@app.route('/view/cover-letter/<folder_name>')
def view_cover_letter(folder_name):
    """View cover letter PDF in browser"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        pdf_file = job_folder / "cover_letter.pdf"
        
        if not pdf_file.exists():
            abort(404)
        
        return send_file(pdf_file, mimetype='application/pdf')
        
    except Exception as e:
        print(f"Error viewing cover letter: {e}")
        abort(500)

@app.route('/download/resume/<folder_name>')
def download_resume(folder_name):
    """Download resume file - PDF priority, fallback to txt"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        
        if not job_folder.exists():
            abort(404)
        
        file_options = [
            (job_folder / "resume.pdf", "application/pdf", "pdf"),
            (job_folder / "resume.txt", "text/plain", "txt")
        ]
        
        for file_path, mimetype, extension in file_options:
            if file_path.exists():
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=f"{folder_name}_resume.{extension}",
                    mimetype=mimetype
                )
        
        abort(404)
        
    except Exception as e:
        print(f"Error downloading resume: {e}")
        abort(500)

@app.route('/download/cover-letter/<folder_name>')
def download_cover_letter(folder_name):
    """Download cover letter - PDF priority, fallback to txt"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        
        if not job_folder.exists():
            abort(404)
        
        file_options = [
            (job_folder / "cover_letter.pdf", "application/pdf", "pdf"),
            (job_folder / "cover_letter.txt", "text/plain", "txt")
        ]
        
        for file_path, mimetype, extension in file_options:
            if file_path.exists():
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=f"{folder_name}_cover_letter.{extension}",
                    mimetype=mimetype
                )
        
        abort(404)
        
    except Exception as e:
        print(f"Error downloading cover letter: {e}")
        abort(500)

@app.route('/download/job-info/<folder_name>')
def download_job_info(folder_name):
    """Download job information JSON"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        job_info_path = job_folder / "job_info.json"
        
        if not job_info_path.exists():
            abort(404)
        
        return send_file(
            job_info_path,
            as_attachment=True,
            download_name=f"{folder_name}_job_info.json",
            mimetype="application/json"
        )
        
    except Exception as e:
        print(f"Error downloading job info: {e}")
        abort(500)

@app.route('/api/folder-contents/<folder_name>')
def get_folder_contents(folder_name):
    """Get contents of a job application folder"""
    try:
        job_folder = job_bot.base_output_dir / folder_name
        
        if not job_folder.exists():
            return jsonify({'error': 'Folder not found'}), 404
        
        contents = {
            'folder_name': folder_name,
            'files': []
        }
        
        file_types = [
            ('resume.pdf', 'Resume (PDF)', 'application/pdf'),
            ('resume.txt', 'Resume (Text)', 'text/plain'),
            ('cover_letter.pdf', 'Cover Letter (PDF)', 'application/pdf'),
            ('cover_letter.txt', 'Cover Letter (Text)', 'text/plain'),
            ('job_info.json', 'Job Information', 'application/json')
        ]
        
        for filename, display_name, mimetype in file_types:
            file_path = job_folder / filename
            if file_path.exists():
                file_size = file_path.stat().st_size
                contents['files'].append({
                    'filename': filename,
                    'display_name': display_name,
                    'size': f"{file_size / 1024:.1f} KB",
                    'mimetype': mimetype
                })
        
        return jsonify(contents)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    Path('templates').mkdir(exist_ok=True)
    
    print("🚀 Job Application Bot with User Profiles running at http://localhost:5000")
    print("📄 Using ReportLab for PDF generation - no external dependencies needed!")
    print("👤 Users can now customize their profile for personalized documents!")
    print("✅ PDFs will be generated for all resumes and cover letters")
    
    print("\n🌐 Visit: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)