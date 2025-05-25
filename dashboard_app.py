from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
import os
from pathlib import Path
import subprocess
import threading

app = Flask(__name__)

class DashboardAPI:
    def __init__(self):
        self.db_path = "job_applications.db"
        self.init_db()
    
    def init_db(self):
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_url TEXT, company TEXT, position TEXT,
                application_date TEXT, status TEXT DEFAULT 'applied',
                resume_version TEXT, cover_letter_version TEXT, notes TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, company TEXT, location TEXT, description TEXT,
                requirements TEXT, salary TEXT, url TEXT UNIQUE,
                posted_date TEXT, visa_sponsorship BOOLEAN,
                source TEXT, scraped_date TEXT)''')
            conn.commit()
            conn.close()
    
    def get_stats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) FROM jobs')
            total_jobs = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM applications')
            total_apps = cursor.fetchone()[0] or 0
            today = datetime.now().date().isoformat()
            cursor.execute('SELECT COUNT(*) FROM applications WHERE DATE(application_date) = ?', (today,))
            apps_today = cursor.fetchone()[0] or 0
            cursor.execute('SELECT COUNT(*) FROM jobs WHERE DATE(posted_date) = ? OR DATE(scraped_date) = ?', (today, today))
            jobs_today = cursor.fetchone()[0] or 0
            success_rate = round((total_apps / max(total_jobs, 1)) * 100, 1) if total_jobs > 0 else 0
        except:
            total_jobs = total_apps = apps_today = jobs_today = success_rate = 0
        conn.close()
        return {
            'jobs_scanned_today': jobs_today,
            'applications_today': apps_today,
            'total_applications': total_apps,
            'total_jobs': total_jobs,
            'success_rate': success_rate
        }
    
    def get_recent_jobs(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT title, company, location, posted_date, visa_sponsorship, source, salary FROM jobs ORDER BY id DESC LIMIT ?', (limit,))
            jobs = cursor.fetchall()
            result = []
            for job in jobs:
                result.append({
                    'title': job[0] or 'Software Developer',
                    'company': job[1] or 'Tech Company',
                    'location': job[2] or 'Remote',
                    'posted_date': job[3] or datetime.now().isoformat(),
                    'visa_sponsorship': job[4] if job[4] is not None else True,
                    'source': job[5] or 'Bot',
                    'salary': job[6] or 'Competitive'
                })
        except:
            result = []
        conn.close()
        return result
    
    def get_applications(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT company, position, application_date, status, resume_version FROM applications ORDER BY id DESC LIMIT ?', (limit,))
            apps = cursor.fetchall()
            result = []
            for app in apps:
                resume_file = os.path.basename(app[4]) if app[4] else 'resume.txt'
                result.append({
                    'company': app[0] or 'Tech Company',
                    'title': app[1] or 'Software Developer',
                    'application_date': app[2] or datetime.now().isoformat(),
                    'status': app[3] or 'applied',
                    'resume_file': resume_file
                })
        except:
            result = []
        conn.close()
        return result
    
    def get_resume_files(self):
        resume_dir = Path("generated_resumes")
        if not resume_dir.exists():
            return []
        try:
            files = []
            for file_path in resume_dir.glob("*.txt"):
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            files.sort(key=lambda x: x['created'], reverse=True)
            return files[:20]
        except:
            return []

dashboard_api = DashboardAPI()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    return jsonify(dashboard_api.get_stats())

@app.route('/api/jobs')
def api_jobs():
    return jsonify(dashboard_api.get_recent_jobs())

@app.route('/api/applications')
def api_applications():
    return jsonify(dashboard_api.get_applications())

@app.route('/api/files')
def api_files():
    return jsonify(dashboard_api.get_resume_files())

@app.route('/api/run-bot', methods=['POST'])
def api_run_bot():
    try:
        data = request.get_json() or {}
        max_apps = data.get('max_apps', 3)
        dry_run = data.get('dry_run', True)
        
        bot_files = ['job_application_bot.py', 'simple_job_bot.py', 'http_job_bot.py']
        bot_file = None
        for file in bot_files:
            if os.path.exists(file):
                bot_file = file
                break
        
        if not bot_file:
            return jsonify({'status': 'error', 'message': 'No bot file found'}), 400
        
        def run_bot():
            try:
                cmd = ['python', bot_file]
                if bot_file == 'job_application_bot.py':
                    if not dry_run:
                        cmd.append('--real')
                    cmd.extend(['--max-apps', str(max_apps)])
                else:
                    if dry_run:
                        cmd.append('--dry-run')
                    cmd.extend(['--max-apps', str(max_apps)])
                
                subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            except:
                pass
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success', 
            'message': f'Bot started using {bot_file}',
            'mode': 'dry_run' if dry_run else 'live',
            'max_apps': max_apps
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/bot-status')
def api_bot_status():
    db_exists = os.path.exists(dashboard_api.db_path)
    resume_dir = Path("generated_resumes")
    resume_count = len(list(resume_dir.glob("*.txt"))) if resume_dir.exists() else 0
    
    return jsonify({
        'status': 'ready',
        'database_exists': db_exists,
        'database_path': dashboard_api.db_path,
        'resume_files': resume_count,
        'last_updated': datetime.now().isoformat()
    })

if __name__ == '__main__':
    Path('templates').mkdir(exist_ok=True)
    print("🚀 Dashboard running at http://localhost:5000")
    print("📄 Make sure dashboard.html is in templates/dashboard.html")
    app.run(debug=True, host='0.0.0.0', port=5000)