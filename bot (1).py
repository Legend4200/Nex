from flask import Flask, request, render_template_string, redirect, session, url_for
import threading, time, requests, pytz
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Configure login credentials (you can change these)
VALID_USERNAME = "Thew_venom"
VALID_PASSWORD = "venom910"

# Storage for tasks and logs
stop_events = {}
task_logs = {}
token_usage_stats = {}

def add_log(task_id, log_message):
    if task_id not in task_logs:
        task_logs[task_id] = []
    task_logs[task_id].append(log_message)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body {
            background-image: url('https://i.ibb.co/hJ4hMJXv/1735118116746.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            height: 100vh;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Arial', sans-serif;
        }
        .login-container {
            background-color: rgba(255, 255, 255, 0.9);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            width: 350px;
            text-align: center;
        }
        .login-container h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        .login-btn {
            width: 100%;
            padding: 12px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .login-btn:hover {
            background-color: #0056b3;
        }
        .error-message {
            color: #dc3545;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="login-btn">Login</button>
            {% if error %}
            <div class="error-message">{{ error }}</div>
            {% endif %}
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V3N0M W3B C0NV0</title>
    <style>
        body {
            background-image: url('https://i.ibb.co/TDDyJMhp/1753527282128.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #ffffff;
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
        }
        h1 {
            color: #ffffff;
            text-align: center;
            margin-top: 0;
            padding-top: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .content {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-label {
            color: #ffffff;
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 12px;
            background-color: rgba(255, 255, 255, 0.9);
            color: #495057;
            border: 1px solid #ced4da;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 16px;
        }
        .btn {
            width: 100%;
            padding: 12px;
            margin-top: 10px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 16px;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        .btn-danger {
            background-color: #dc3545;
            color: white;
        }
        .log-entry {
            margin: 10px 0;
            padding: 12px;
            border-radius: 5px;
            background-color: rgba(0, 0, 0, 0.7);
            border-left: 4px solid #007bff;
            color: #ffffff;
        }
        .success {
            border-color: #28a745;
            color: #28a745;
        }
        .error {
            border-color: #dc3545;
            color: #dc3545;
        }
        .info {
            border-color: #17a2b8;
            color: #17a2b8;
        }
        .group-info {
            padding: 12px;
            margin: 10px 0;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 5px;
            border-left: 4px solid #007bff;
            color: #ffffff;
        }
        .section {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        .token-stats {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #6f42c1;
            color: #ffffff;
        }
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 8px 15px;
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        @media (max-width: 768px) {
            .content {
                padding: 15px;
            }
            h1 {
                font-size: 24px;
            }
            .btn {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
    <h1>V3N0M T9BHIIW RUL3X</h1>
    <div class="content">
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label class="form-label">Token Option:</label>
                <select name="tokenOption" class="form-control" onchange="toggleInputs(this.value)">
                    <option value="single">Single Token</option>
                    <option value="multi">Multi Tokens</option>
                </select>
            </div>
            <div id="singleInput" class="form-group">
                <label class="form-label">Single Token:</label>
                <input type="text" name="singleToken" class="form-control">
            </div>
            <div id="multiInputs" class="form-group" style="display: none;">
                <label class="form-label">Tokens File:</label>
                <input type="file" name="tokensFile" class="form-control">
            </div>
            <div class="form-group">
                <label class="form-label">Conversation ID:</label>
                <input type="text" name="convo" class="form-control" required>
            </div>
            <div class="form-group">
                <label class="form-label">Message File:</label>
                <input type="file" name="msgFile" class="form-control" required>
            </div>
            <div class="form-group">
                <label class="form-label">Interval (sec):</label>
                <input type="number" name="interval" class="form-control" required>
            </div>
            <div class="form-group">
                <label class="form-label">Messages per Token:</label>
                <input type="number" name="msgs_per_token" class="form-control" value="5" required>
            </div>
            <div class="form-group">
                <label class="form-label">Hater Name:</label>
                <input type="text" name="haterName" class="form-control" required>
            </div>
            <button class="btn btn-primary" type="submit">Start</button>
        </form>
        
        <div class="section">
            <form method="POST" action="/stop">
                <div class="form-group">
                    <label class="form-label">Task ID to Stop:</label>
                    <input type="text" name="task_id" class="form-control" required>
                </div>
                <button class="btn btn-danger" type="submit">Stop Task</button>
            </form>
        </div>
        
        <div class="section">
            <h3>Token Checker</h3>
            <form method="POST" action="/check">
                <div class="form-group">
                    <label class="form-label">Token Option:</label>
                    <select name="checkTokenOption" class="form-control" onchange="toggleCheckInputs(this.value)">
                        <option value="single">Single Token</option>
                        <option value="multi">Multi Tokens</option>
                    </select>
                </div>
                <div id="checkSingleInput" class="form-group">
                    <label class="form-label">Single Token:</label>
                    <input type="text" name="checkSingleToken" class="form-control">
                </div>
                <div id="checkMultiInputs" class="form-group" style="display: none;">
                    <label class="form-label">Tokens File:</label>
                    <input type="file" name="checkTokensFile" class="form-control">
                </div>
                <button class="btn btn-primary" type="submit">Check Token(s)</button>
            </form>
        </div>
        
        <div class="section">
            <form method="POST" action="/messenger-conversations">
                <div class="form-group">
                    <label class="form-label">Token:</label>
                    <input type="text" name="token" class="form-control" required>
                </div>
                <button class="btn btn-primary" type="submit">Get Chat Uid</button>
            </form>
        </div>
        
        <div class="section">
            <form method="POST" action="/view-logs">
                <div class="form-group">
                    <label class="form-label">View Logs by Task ID:</label>
                    <input type="text" name="task_id" class="form-control" required>
                </div>
                <button class="btn btn-secondary" type="submit">View Logs</button>
            </form>
        </div>
    </div>
    <script>
        function toggleInputs(value) {
            document.getElementById("singleInput").style.display = value === "single" ? "block" : "none";
            document.getElementById("multiInputs").style.display = value === "multi" ? "block" : "none";
        }
        
        function toggleCheckInputs(value) {
            document.getElementById("checkSingleInput").style.display = value === "single" ? "block" : "none";
            document.getElementById("checkMultiInputs").style.display = value === "multi" ? "block" : "none";
        }
    </script>
</body>
</html>
"""

LOG_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Logs</title>
    <style>
        body { 
            background-image: url('https://i.ibb.co/hJ4hMJXv/1735118116746.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #ffffff; 
            font-family: 'Roboto', sans-serif; 
            padding: 20px;
            margin: 0;
        }
        h1 { 
            color: #ffffff; 
            margin-top: 0;
            padding-top: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .log-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .log-entry { 
            margin: 15px 0; 
            padding: 15px; 
            border-radius: 5px; 
            background-color: rgba(0, 0, 0, 0.7);
            border-left: 4px solid #007bff;
        }
        .success { 
            border-color: #28a745;
            color: #28a745;
        }
        .error { 
            border-color: #dc3545;
            color: #dc3545;
        }
        .info { 
            border-color: #17a2b8;
            color: #17a2b8;
        }
        .token-info {
            border-color: #6f42c1;
            color: #6f42c1;
        }
        .back-btn {
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .token-stats {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #6f42c1;
            color: #ffffff;
        }
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 8px 15px;
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        @media (max-width: 768px) {
            .log-container {
                padding: 15px;
            }
            h1 {
                font-size: 24px;
            }
        }
    </style>
    <script>
        function refreshLogs() {
            fetch(window.location.href)
                .then(response => response.text())
                .then(data => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(data, 'text/html');
                    const newLogs = doc.getElementById('logs').innerHTML;
                    document.getElementById('logs').innerHTML = newLogs;
                    // Scroll to bottom after update
                    window.scrollTo(0, document.body.scrollHeight);
                });
        }
        
        // Refresh every 3 seconds
        setInterval(refreshLogs, 3000);
        
        // Scroll to bottom on initial load
        window.onload = function() {
            window.scrollTo(0, document.body.scrollHeight);
        };
    </script>
</head>
<body>
    <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
    <div class="log-container">
        <h1>Logs for Task ID: {{ task_id }}</h1>
        
        {% if token_stats %}
        <div class="token-stats">
            <h3>Token Usage Statistics</h3>
            {% for token, count in token_stats.items() %}
            <div>Token {{ loop.index }}: {{ count }} messages sent</div>
            {% endfor %}
        </div>
        {% endif %}
        
        <div id="logs">
            {% for log in logs %}
            <div class="log-entry {% if '✅' in log %}success{% elif '❌' in log %}error{% elif 'ℹ️' in log %}info{% elif '🔑' in log %}token-info{% endif %}">{{ log }}</div>
            {% endfor %}
        </div>
        <a href="/" class="back-btn">Back to Main</a>
    </div>
</body>
</html>
"""

TOKEN_CHECK_RESULT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token Check Results</title>
    <style>
        body { 
            background-image: url('https://i.ibb.co/TMwTYmpK/20250716-092131.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            color: #ffffff; 
            font-family: 'Roboto', sans-serif; 
            padding: 20px;
            margin: 0;
        }
        h1 { 
            color: #ffffff; 
            margin-top: 0;
            padding-top: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .result-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        .token-result {
            margin: 15px 0; 
            padding: 15px; 
            border-radius: 5px; 
            background-color: rgba(0, 0, 0, 0.7);
            margin-bottom: 20px;
        }
        .valid {
            border-left: 4px solid #28a745;
        }
        .invalid {
            border-left: 4px solid #dc3545;
        }
        .token-info {
            font-weight: bold;
            margin-bottom: 10px;
            word-break: break-all;
        }
        .back-btn {
            display: inline-block;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .logout-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 8px 15px;
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .summary {
            padding: 15px;
            margin-bottom: 20px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 5px;
            border-left: 4px solid #6f42c1;
        }
    </style>
</head>
<body>
    <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
    <div class="result-container">
        <h1>Token Check Results</h1>
        
        <div class="summary">
            <h3>Summary</h3>
            <p>Total Tokens Checked: {{ total_tokens }}</p>
            <p>Valid Tokens: {{ valid_count }} ({{ (valid_count/total_tokens*100 if total_tokens > 0 else 0)|round(2) }}%)</p>
            <p>Invalid Tokens: {{ invalid_count }} ({{ (invalid_count/total_tokens*100 if total_tokens > 0 else 0)|round(2) }}%)</p>
        </div>
        
        {% for result in results %}
        <div class="token-result {% if result.valid %}valid{% else %}invalid{% endif %}">
            <div class="token-info">Token {{ loop.index }}: {{ result.token_short }}</div>
            {% if result.valid %}
                 <p>✅ Status: Valid</p>
                <p>👤 Name: {{ result.name }}</p>
                <p>🆔 UID: {{ result.uid }}</p>
                {% if result.picture %}
                <img src="{{ result.picture }}" width="100" style="margin-top: 10px;">
                {% endif %}
            {%else %}
                <p>❌ Status: Invalid or Expired</p>
                <p>Error: {{ result.error }}</p>
            {% endif %}
        </div>
        {% endfor %}
        
        <a href="/" class="back-btn">Back to Main</a>
    </div>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template_string(LOGIN_TEMPLATE, error="Invalid username or password")
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template_string(HTML_TEMPLATE)

@app.route("/", methods=["POST"])
def handle_form():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    opt = request.form["tokenOption"]
    convo = request.form["convo"]
    interval = int(request.form["interval"])
    hater = request.form["haterName"]
    msgs_per_token = int(request.form["msgs_per_token"])
    msgs = request.files["msgFile"].read().decode().splitlines()
    
    if opt == "single":
        tokens = [request.form["singleToken"]]
    else:
        tokens = request.files["tokensFile"].read().decode().splitlines()
    
    task_id = str(uuid.uuid4())
    stop_events[task_id] = threading.Event()
    token_usage_stats[task_id] = {token: 0 for token in tokens}
    
    threading.Thread(target=start_messaging, args=(tokens, msgs, convo, interval, hater, opt, task_id, msgs_per_token)).start()
    return f"📨 Messaging started for conversation {convo}. Task ID: {task_id}"

@app.route("/stop", methods=["POST"])
def stop_task():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    task_id = request.form["task_id"]
    if task_id in stop_events:
        stop_events[task_id].set()
        return f"🛑 Task with ID {task_id} has been stopped."
    else:
        return f"⚠️ No active task with ID {task_id}."

@app.route("/check", methods=["POST"])
def check_token():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    opt = request.form.get("checkTokenOption", "single")
    
    if opt == "single":
        tokens = [request.form.get("checkSingleToken", "")]
    else:
        if "checkTokensFile" not in request.files:
            return "No file uploaded"
        tokens = request.files["checkTokensFile"].read().decode().splitlines()
    
    results = []
    valid_count = 0
    invalid_count = 0
    
    for token in tokens:
        token = token.strip()
        if not token:
            continue
            
        token_short = f"{token[:5]}...{token[-5:]}" if len(token) > 10 else token
        result = {"token": token, "token_short": token_short, "valid": False}
        
        try:
            url = f"https://graph.facebook.com/me?fields=id,name,picture&access_token={token}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                result.update({
                    "valid": True,
                    "uid": data.get("id", "N/A"),
                    "name": data.get("name", "Unknown"),
                    "picture": data.get("picture", {}).get("data", {}).get("url", ""),
                })
                valid_count += 1
            else:
                result["error"] = f"HTTP {res.status_code}: {res.text}"
                invalid_count += 1
        except Exception as e:
            result["error"] = str(e)
            invalid_count += 1
        
        results.append(result)
    
    return render_template_string(
        TOKEN_CHECK_RESULT_TEMPLATE,
        results=results,
        total_tokens=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count
    )

@app.route("/messenger-conversations", methods=["POST"])
def fetch_messenger_conversations():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    token = request.form["token"]
    try:
        # First verify token validity
        check_url = f"https://graph.facebook.com/me?access_token={token}"
        check_res = requests.get(check_url)
        
        if check_res.status_code != 200:
            return """
                <div style="background-color: rgba(248, 215, 218, 0.8); padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; color: #000;">
                    ❌ Invalid or expired token
                </div>
            """
            
        # Fetch Messenger conversations
        url = f"https://graph.facebook.com/v19.0/me/conversations?fields=id,name,participants&access_token={token}"
        response = requests.get(url)
        response.raise_for_status()
        
        conversations = response.json().get('data', [])
        
        if not conversations:
            return """
                <div style="background-color: rgba(226, 227, 229, 0.8); padding: 15px; border-radius: 5px; border-left: 4px solid #6c757d; color: #000;">
                 📭 No Messenger conversations found for this token
                </div>
            """
            
        # Format response with conversation details
        conv_list = []
        for conv in conversations:
            conv_id = conv.get('id', 'N/A').replace('t_', '')  # Remove t_ prefix
            conv_name = conv.get('name', 'Unnamed Conversation')
            
            # If no name, get participants
            if not conv_name or conv_name == 'Unnamed Conversation':
                participants = conv.get('participants', {}).get('data', [])
                participant_names = [p.get('name', 'Unknown') for p in participants]
                conv_name = ", ".join(participant_names) if participant_names else "Group Chat"
            
            conv_list.append(f"""
                <div class="group-info">
                    <strong>💬 Conversation Name:</strong> {conv_name}<br>
                    <strong>🆔 Conversation ID:</strong> {conv_id}
                </div>
            """)
            
        return f"""
            <div style="background-color: rgba(233, 236, 239, 0.8); padding: 20px; border-radius: 10px; margin-top: 20px; color: #000;">
                <h3 style="color: #007bff; margin-top: 0;">Messenger Conversations</h3>
                {'<hr style="margin: 15px 0;">'.join(conv_list)}
            </div>
        """
        
    except Exception as e:
        return f"""
            <div style="background-color: rgba(248, 215, 218, 0.8); padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; color: #000;">
                ❌ Error fetching conversations: {str(e)}
            </div>
        """

@app.route("/view-logs", methods=["GET", "POST"])
def view_logs():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if request.method == "POST":
        task_id = request.form["task_id"]
        return redirect(f"/view-logs/{task_id}")
    return render_template_string("""
        <div class="content" style="max-width: 600px; margin: 20px auto; background-color: rgba(0, 0, 0, 0.7);">
            <form method="POST">
                <div class="form-group">
                    <label class="form-label">View Logs by Task ID:</label>
                    <input type="text" name="task_id" class="form-control" required>
                </div>
                <button class="btn btn-secondary" type="submit">View Logs</button>
            </form>
        </div>
    """)

@app.route("/view-logs/<task_id>")
def show_logs(task_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    logs = task_logs.get(task_id, ["No logs found for this task."])
    stats = token_usage_stats.get(task_id, {})
    return render_template_string(LOG_TEMPLATE, task_id=task_id, logs=logs, token_stats=stats)

def start_messaging(tokens, messages, convo_id, interval, hater_name, token_option, task_id, msgs_per_token):
    stop_event = stop_events[task_id]
    token_index = 0
    msg_count_for_current_token = 0
    
    add_log(task_id, f"🚀 Task started for conversation: {convo_id}")
    
    # Get group name info once at start
    token = tokens[0]
    group_name = get_group_name(convo_id, token)
    if group_name:
        add_log(task_id, f"ℹ️ Target Group: {group_name}")
    
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                add_log(task_id, "🛑 Task stopped manually.")
                break
            
            # Select token based on current index
            current_token = tokens[token_index]
            token_display = f"Token {token_index + 1}/{len(tokens)}"
            
            # Send message
            send_msg(convo_id, current_token, msg, hater_name, task_id, token_display)
            
            # Update token usage stats
            token_usage_stats[task_id][current_token] = token_usage_stats[task_id].get(current_token, 0) + 1
            msg_count_for_current_token += 1
            
            # Check if we've sent enough messages with this token
            if msg_count_for_current_token >= msgs_per_token:
                token_index = (token_index + 1) % len(tokens)
                msg_count_for_current_token = 0
                add_log(task_id, f"🔑 Switching to {token_display}")
            
            time.sleep(interval)

def get_group_name(convo_id, token):
    try:
        url = f"https://graph.facebook.com/v15.0/t_{convo_id}?fields=name,participants&access_token={token}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            name = data.get("name")
            if not name:
                participants = data.get("participants", {}).get("data", [])
                participant_names = [p.get("name", "Unknown") for p in participants]
                name = ", ".join(participant_names) if participant_names else "Group Chat"
            return name
        return None
    except:
        return None

def send_msg(convo_id, access_token, message, hater_name, task_id, token_display=""):
    try:
        url = f"https://graph.facebook.com/v15.0/t_{convo_id}/"
        parameters = {
            "access_token": access_token,
            "message": f"{hater_name}: {message}"
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(url, json=parameters, headers=headers)
        
        # Get sender name for logging
        sender_name = get_sender_name(access_token)
        
        if response.status_code == 200:
            log_msg = f"✅ {token_display} | {sender_name} | Message sent: {message}"
            add_log(task_id, log_msg)
        else:
            log_msg = f"❌ {token_display} | {sender_name} | Failed (Code: {response.status_code}): {response.text}"
            add_log(task_id, log_msg)
    except Exception as e:
        log_msg = f"❌ {token_display} | Error: {str(e)}"
        add_log(task_id, log_msg)

def get_sender_name(token):
    try:
        url = f"https://graph.facebook.com/me?fields=name&access_token={token}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("name", "Unknown")
        return "Unknown"
    except:
        return "Unknown"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=21902)