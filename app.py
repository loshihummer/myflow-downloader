from flask import Flask, render_template_string, request, send_file, flash, redirect, url_for
import yt_dlp
import os
import time
import glob

app = Flask(__name__)
app.secret_key = 'myflow_cyber_secret'

# Server ပေါ်တွင် ယာယီသိမ်းမည့် နေရာ
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# HTML Template (Cyberpunk Style)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MyFlow Cyber Downloader</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts: Orbitron & Rajdhani -->
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --neon-blue: #00f3ff;
            --neon-dim: rgba(0, 243, 255, 0.2);
            --bg-dark: #050505;
        }
        body {
            background-color: var(--bg-dark);
            font-family: 'Rajdhani', sans-serif;
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 30px 30px;
            color: #e0faff;
            overflow-x: hidden;
        }

        /* Cyber Card Container */
        .cyber-card {
            background: rgba(10, 15, 20, 0.9);
            border: 1px solid var(--neon-blue);
            box-shadow: 0 0 15px var(--neon-dim), inset 0 0 20px var(--neon-dim);
            clip-path: polygon(
                20px 0, 100% 0, 
                100% calc(100% - 20px), calc(100% - 20px) 100%, 
                0 100%, 0 20px
            );
            position: relative;
        }

        .cyber-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 50px; height: 50px;
            border-top: 3px solid var(--neon-blue); border-left: 3px solid var(--neon-blue);
            clip-path: polygon(0 0, 100% 0, 0 100%);
        }
        .cyber-card::after {
            content: ''; position: absolute; bottom: 0; right: 0; width: 50px; height: 50px;
            border-bottom: 3px solid var(--neon-blue); border-right: 3px solid var(--neon-blue);
            clip-path: polygon(100% 100%, 0 100%, 100% 0);
        }

        .cyber-input {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid #334155;
            border-left: 4px solid var(--neon-blue);
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        .cyber-input:focus {
            border-color: var(--neon-blue);
            box-shadow: 0 0 15px var(--neon-dim);
            background: rgba(0, 243, 255, 0.05);
        }

        .cyber-btn {
            background: var(--neon-blue);
            color: #000;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            clip-path: polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px);
            transition: all 0.3s ease;
        }
        .cyber-btn:hover {
            background: #fff;
            box-shadow: 0 0 20px var(--neon-blue);
            transform: translateY(-2px);
        }

        .cyber-radio:checked + div {
            background-color: var(--neon-blue);
            box-shadow: 0 0 10px var(--neon-blue);
        }

        .loader { border: 3px solid transparent; border-top: 3px solid #000; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

    <div class="cyber-card p-10 w-full max-w-md">
        
        <!-- Header -->
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-white mb-2 tracking-wider font-['Orbitron'] uppercase" style="text-shadow: 2px 2px 0px #ff00ff, -2px -2px 0px #00f3ff;">YT TERMINAL</h1>
            <div class="h-[1px] w-1/2 bg-cyan-500 mx-auto mb-2 shadow-[0_0_10px_#00f3ff]"></div>
            <p class="text-cyan-300 text-sm font-bold tracking-[0.2em] uppercase" style="text-shadow: 0 0 5px rgba(0,243,255,0.5);">
                Developed by MyFlow Production
            </p>
        </div>

        <!-- Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="mb-6 p-3 border-l-4 text-center text-sm font-bold {{ 'border-red-500 bg-red-900/30 text-red-200' if category == 'error' else 'border-green-500 bg-green-900/30 text-green-200' }}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <!-- Form -->
        <form action="/download" method="post" onsubmit="showLoading()">
            <div class="mb-8 relative">
                <label class="text-cyan-500 text-xs font-bold mb-1 block uppercase tracking-widest">Input Stream</label>
                <input type="text" name="url" placeholder="ENTER TARGET URL..." required
                       class="cyber-input w-full px-4 py-3 text-cyan-100 placeholder-slate-500 outline-none">
            </div>
            
            <!-- Options -->
            <div class="flex justify-center gap-6 mb-8 bg-black/40 p-3 border border-slate-700/50">
                <label class="flex items-center gap-3 cursor-pointer group">
                    <input type="radio" name="format" value="video" checked class="cyber-radio hidden peer">
                    <div class="w-4 h-4 border border-cyan-400 peer-checked:bg-cyan-400 transition-all duration-300 rotate-45"></div>
                    <span class="text-slate-400 peer-checked:text-cyan-400 font-bold tracking-widest uppercase text-sm">Video</span>
                </label>
                <label class="flex items-center gap-3 cursor-pointer group">
                    <input type="radio" name="format" value="audio" class="cyber-radio hidden peer">
                    <div class="w-4 h-4 border border-cyan-400 peer-checked:bg-cyan-400 transition-all duration-300 rotate-45"></div>
                    <span class="text-slate-400 peer-checked:text-cyan-400 font-bold tracking-widest uppercase text-sm">Audio (M4A)</span>
                </label>
            </div>

            <!-- Download Button -->
            <div class="flex justify-center mb-8">
                <button type="submit" id="downloadBtn" 
                        class="cyber-btn py-3 px-8 text-sm flex items-center gap-3">
                    <span>Initiate Download</span>
                    <div class="loader" id="spinner"></div>
                </button>
            </div>
        </form>

        <!-- Footer / Socials -->
        <div class="border-t border-slate-800 pt-6 text-center">
            <p class="text-[10px] text-slate-500 mb-3 font-mono uppercase tracking-widest">Connect to Network</p>
            <div class="flex justify-center gap-6">
                <a href="https://www.tiktok.com/@myflowproduction" target="_blank" class="group relative">
                    <div class="absolute inset-0 bg-cyan-400 blur-md opacity-0 group-hover:opacity-50 transition duration-300"></div>
                    <i class="fa-brands fa-tiktok text-2xl text-slate-400 group-hover:text-white relative z-10 transition"></i>
                </a>
                <a href="https://www.facebook.com/myflowproduction" target="_blank" class="group relative">
                    <div class="absolute inset-0 bg-blue-600 blur-md opacity-0 group-hover:opacity-50 transition duration-300"></div>
                    <i class="fa-brands fa-facebook text-2xl text-slate-400 group-hover:text-white relative z-10 transition"></i>
                </a>
            </div>
        </div>
    </div>

    <script>
        function showLoading() {
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('downloadBtn').classList.add('opacity-75', 'cursor-wait');
            document.querySelector('#downloadBtn span').innerText = 'EXECUTING...';
        }
    </script>
</body>
</html>
"""

def clear_old_files():
    files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
    for f in files:
        try:
            if os.path.getmtime(f) < time.time() - 600: 
                os.remove(f)
        except: pass

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    clear_old_files()
    url = request.form.get('url')
    format_type = request.form.get('format')
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'restrictfilenames': True,
        'quiet': True,
    }

    if format_type == 'audio':
        # M4A setting
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
    else:
        # Video setting
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'audio' and not filename.endswith('.m4a'):
                base = os.path.splitext(filename)[0]
                possible_m4a = base + ".m4a"
                if os.path.exists(possible_m4a):
                    filename = possible_m4a

            return send_file(filename, as_attachment=True)

    except Exception as e:
        error_msg = str(e)
        if "Sign in" in error_msg:
             flash("ACCESS DENIED: Server IP Blocked by YouTube. Try again later.", "error")
        else:
             flash(f"SYSTEM ERROR: {str(e)}", "error")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)