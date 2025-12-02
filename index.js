const fs = require('fs');
const path = require('path');
const express = require('express');
const wiegine = require('fca-mafiya');
const WebSocket = require('ws');

const app = express();
const PORT = process.env.PORT || 4000;

let config = {
  delay: 10,
  running: false,
  currentCookieIndex: 0,
  cookies: []
};

let messageData = {
  threadID: '',
  messages: [],
  currentIndex: 0,
  loopCount: 0,
  hatersName: [],
  lastName: []
};

let wss;

class RawSessionManager {
  constructor() {
    this.sessions = new Map(); // Map of index -> {api, healthy}
    this.sessionQueue = []; // Queue of healthy session indices
    this.currentSessionIndex = 0; // For round-robin rotation
  }

  async createRawSession(cookieContent, index) {
    return new Promise((resolve) => {
      console.log(`🔐 Creating raw session ${index + 1}...`);
      
      // RAW COOKIES DIRECT USE - No JSON parsing
      wiegine.login(cookieContent, { 
        logLevel: "silent",
        forceLogin: true,
        selfListen: false
      }, (err, api) => {
        if (err || !api) {
          console.log(`❌ Raw session ${index + 1} failed:`, err?.error || 'Unknown error');
          
          // Retry after 10 seconds
          setTimeout(() => {
            this.createRawSession(cookieContent, index).then(resolve);
          }, 10000);
          return;
        }

        console.log(`✅ Raw session ${index + 1} created successfully`);
        
        // Test group access
        this.testGroupAccess(api, index).then((canAccess) => {
          if (canAccess) {
            this.sessions.set(index, { api, healthy: true });
            this.sessionQueue.push(index);
            console.log(`🎯 Session ${index + 1} added to rotation`);
          } else {
            console.log(`⚠️ Session ${index + 1} group access limited`);
            this.sessions.set(index, { api, healthy: false });
          }
          resolve(api);
        });
      });
    });
  }

  async testGroupAccess(api, index) {
    return new Promise((resolve) => {
      // Try to get thread info
      api.getThreadInfo(messageData.threadID, (err, info) => {
        if (!err && info) {
          console.log(`✅ Session ${index + 1} - Thread access confirmed`);
          resolve(true);
          return;
        }

        console.log(`❌ Session ${index + 1} - Thread info failed:`, err?.error);
        
        // Try actual message send as test
        api.sendMessage("🧪 Test", messageData.threadID, (err2) => {
          if (!err2) {
            console.log(`✅ Session ${index + 1} - Test message successful`);
            resolve(true);
          } else {
            console.log(`❌ Session ${index + 1} - Test message failed:`, err2?.error);
            resolve(false);
          }
        });
      });
    });
  }

  getNextSession() {
    if (this.sessionQueue.length === 0) {
      return null;
    }
    
    // Round-robin rotation
    const sessionIndex = this.sessionQueue[this.currentSessionIndex];
    this.currentSessionIndex = (this.currentSessionIndex + 1) % this.sessionQueue.length;
    
    const session = this.sessions.get(sessionIndex);
    return session?.api || null;
  }

  getHealthySessions() {
    const healthy = [];
    for (let [index, session] of this.sessions) {
      if (session.healthy) {
        healthy.push(session.api);
      }
    }
    return healthy;
  }

  getHealthyCount() {
    return this.sessionQueue.length;
  }

  getTotalSessions() {
    return this.sessions.size;
  }

  markSessionUnhealthy(index) {
    const session = this.sessions.get(index);
    if (session) {
      session.healthy = false;
      // Remove from queue
      const queueIndex = this.sessionQueue.indexOf(index);
      if (queueIndex > -1) {
        this.sessionQueue.splice(queueIndex, 1);
      }
      console.log(`⚠️ Session ${index + 1} marked as unhealthy`);
    }
  }
}

const rawManager = new RawSessionManager();

class RawMessageSender {
  async sendRawMessage(api, message, threadID, sessionIndex) {
    return new Promise((resolve) => {
      // Direct send with raw cookies
      api.sendMessage(message, threadID, (err) => {
        if (!err) {
          resolve({ success: true, sessionIndex });
          return;
        }

        console.log(`❌ Send error from session ${sessionIndex + 1}:`, err.error);
        
        // Mark session as unhealthy if it fails
        rawManager.markSessionUnhealthy(sessionIndex);
        
        resolve({ success: false, sessionIndex });
      });
    });
  }

  async sendMessageToGroup(finalMessage) {
    const api = rawManager.getNextSession();
    
    if (!api) {
      console.log('❌ No healthy sessions available for rotation');
      return false;
    }

    // Get current session index for tracking
    const currentIndex = (rawManager.currentSessionIndex - 1 + rawManager.sessionQueue.length) % rawManager.sessionQueue.length;
    const sessionIndex = rawManager.sessionQueue[currentIndex];
    
    console.log(`🔄 Using session ${sessionIndex + 1}/${rawManager.getTotalSessions()}`);
    
    const result = await this.sendRawMessage(api, finalMessage, messageData.threadID, sessionIndex);
    return result.success;
  }
}

const rawSender = new RawMessageSender();

async function runRawLoop() {
  if (!config.running) {
    console.log('💤 Raw loop sleeping...');
    return;
  }

  try {
    // Check healthy sessions
    const healthyCount = rawManager.getHealthyCount();
    if (healthyCount === 0) {
      console.log('🔄 No healthy sessions, recreating...');
      await createRawSessions();
      setTimeout(runRawLoop, 5000);
      return;
    }

    // Message processing
    if (messageData.currentIndex >= messageData.messages.length) {
      messageData.loopCount++;
      messageData.currentIndex = 0;
      console.log(`🎯 Loop #${messageData.loopCount} started with ${healthyCount} healthy sessions`);
    }

    const rawMessage = messageData.messages[messageData.currentIndex];
    const randomName = getRandomName();
    const finalMessage = `${randomName} ${rawMessage}`;

    console.log(`📤 Sending message ${messageData.currentIndex + 1}/${messageData.messages.length}`);
    console.log(`🔁 Healthy sessions in rotation: ${healthyCount}`);

    const success = await rawSender.sendMessageToGroup(finalMessage);

    if (success) {
      console.log(`✅ Message ${messageData.currentIndex + 1} sent successfully`);
      messageData.currentIndex++;
    } else {
      console.log('❌ Message failed, will retry with next session');
    }

    // Schedule next message - time.txt se delay use karega
    const delayMs = config.delay * 1000;
    console.log(`⏰ Next message in ${config.delay} seconds...`);
    setTimeout(runRawLoop, delayMs);

  } catch (error) {
    console.log(`🛡️ Error: ${error.message} - Continuing in 10 seconds...`);
    setTimeout(runRawLoop, 10000);
  }
}

async function createRawSessions() {
  console.log('🏗️ Creating raw sessions...');
  
  for (let i = 0; i < config.cookies.length; i++) {
    await rawManager.createRawSession(config.cookies[i], i);
  }
  
  const healthyCount = rawManager.getHealthyCount();
  const totalSessions = rawManager.getTotalSessions();
  console.log(`✅ ${healthyCount}/${totalSessions} sessions healthy and ready for rotation`);
}

function readRequiredFiles() {
  try {
    // Read cookies - RAW FORMAT
    const cookiesPath = path.join(__dirname, 'cookies.txt');
    if (!fs.existsSync(cookiesPath)) throw new Error('cookies.txt not found');
    
    const cookiesContent = fs.readFileSync(cookiesPath, 'utf8');
    config.cookies = cookiesContent.split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0 && !line.startsWith('//'));

    if (config.cookies.length === 0) throw new Error('No valid cookies found');

    // Read thread ID
    const convoPath = path.join(__dirname, 'convo.txt');
    if (!fs.existsSync(convoPath)) throw new Error('convo.txt not found');
    
    messageData.threadID = fs.readFileSync(convoPath, 'utf8').trim();
    if (!/^\d+$/.test(messageData.threadID)) {
      throw new Error('Thread ID must be numeric');
    }

    // Read other files
    const hatersPath = path.join(__dirname, 'hatersanme.txt');
    const lastnamePath = path.join(__dirname, 'lastname.txt');
    const filePath = path.join(__dirname, 'File.txt');
    const timePath = path.join(__dirname, 'time.txt');

    [hatersPath, lastnamePath, filePath, timePath].forEach(file => {
      if (!fs.existsSync(file)) throw new Error(`${path.basename(file)} not found`);
    });

    messageData.hatersName = fs.readFileSync(hatersPath, 'utf8').split('\n').map(l => l.trim()).filter(l => l);
    messageData.lastName = fs.readFileSync(lastnamePath, 'utf8').split('\n').map(l => l.trim()).filter(l => l);
    messageData.messages = fs.readFileSync(filePath, 'utf8').split('\n').map(l => l.trim()).filter(l => l);
    
    const timeContent = fs.readFileSync(timePath, 'utf8').trim();
    config.delay = parseInt(timeContent) || 10;
    
    console.log('✅ All files loaded successfully');
    console.log('📌 Thread ID:', messageData.threadID);
    console.log('🍪 Cookies:', config.cookies.length);
    console.log('💬 Messages:', messageData.messages.length);
    console.log('⏰ Delay:', config.delay, 'seconds');
    
    return true;
  } catch (error) {
    console.error('❌ File error:', error.message);
    return false;
  }
}

function getRandomName() {
  const randomHater = messageData.hatersName[Math.floor(Math.random() * messageData.hatersName.length)];
  const randomLastName = messageData.lastName[Math.floor(Math.random() * messageData.lastName.length)];
  return `${randomHater} ${randomLastName}`;
}

async function startRawSending() {
  console.log('🚀 Starting MULTI-COOKIE ROTATION message system...');
  console.log('🔄 Each message will use different cookie in rotation');
  
  if (!readRequiredFiles()) return;

  config.running = true;
  messageData.currentIndex = 0;
  messageData.loopCount = 0;

  console.log('🔄 Creating multiple sessions from all cookies...');
  await createRawSessions();
  
  const healthyCount = rawManager.getHealthyCount();
  if (healthyCount > 0) {
    console.log(`🎯 Starting rotation with ${healthyCount} healthy sessions`);
    console.log(`⏰ Each message delay: ${config.delay} seconds`);
    runRawLoop();
  } else {
    console.log('❌ No healthy sessions, system stopped');
    config.running = false;
  }
}

function stopRawSending() {
  config.running = false;
  console.log('⏹️ Multi-cookie rotation system stopped');
}

// Express setup
app.use(express.json());

app.post('/api/start', (req, res) => {
  startRawSending();
  res.json({ success: true, message: 'Multi-cookie rotation system started' });
});

app.post('/api/stop', (req, res) => {
  stopRawSending();
  res.json({ success: true, message: 'System stopped' });
});

app.get('/api/status', (req, res) => {
  const healthyCount = rawManager.getHealthyCount();
  const totalSessions = rawManager.getTotalSessions();
  const nextSessionIndex = rawManager.currentSessionIndex;
  
  res.json({
    running: config.running,
    currentIndex: messageData.currentIndex,
    totalMessages: messageData.messages.length,
    loopCount: messageData.loopCount,
    healthySessions: healthyCount,
    totalCookies: totalSessions,
    nextSession: nextSessionIndex + 1,
    delay: config.delay
  });
});

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Facebook Multi-Cookie Bot</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          }
          h1 {
            color: #1877f2;
          }
          button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
          }
          #startBtn {
            background: #4CAF50;
            color: white;
          }
          #stopBtn {
            background: #f44336;
            color: white;
          }
          #status {
            margin-top: 20px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 5px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Facebook Multi-Cookie Bot</h1>
          <p>Each message uses different cookie in rotation</p>
          <button id="startBtn" onclick="start()">▶️ Start Rotation</button>
          <button id="stopBtn" onclick="stop()">⏹️ Stop</button>
          <div id="status">Loading status...</div>
        </div>
        <script>
          async function start() { 
            await fetch('/api/start', {method: 'POST'});
            updateStatus();
          }
          async function stop() { 
            await fetch('/api/stop', {method: 'POST'});
            updateStatus();
          }
          async function updateStatus() {
            const res = await fetch('/api/status');
            const data = await res.json();
            document.getElementById('status').innerHTML = \`
              <h3>System Status</h3>
              <p><strong>Status:</strong> \${data.running ? '✅ Running' : '⏸️ Stopped'}</p>
              <p><strong>Message:</strong> \${data.currentIndex + 1}/\${data.totalMessages}</p>
              <p><strong>Loop Count:</strong> \${data.loopCount}</p>
              <p><strong>Healthy Sessions:</strong> \${data.healthySessions}/\${data.totalCookies}</p>
              <p><strong>Next Cookie:</strong> #\${data.nextSession}</p>
              <p><strong>Delay:</strong> \${data.delay} seconds</p>
            \`;
          }
          setInterval(updateStatus, 3000);
          updateStatus();
        </script>
      </body>
    </html>
  `);
});

const server = app.listen(PORT, () => {
  console.log(`\n💎 MULTI-COOKIE ROTATION Server running at http://localhost:${PORT}`);
  console.log(`🚀 AUTO-STARTING IN 3 SECONDS...`);
  
  setTimeout(() => {
    startRawSending();
  }, 3000);
});

wss = new WebSocket.Server({ server });

process.on('uncaughtException', (error) => {
  console.log('🛡️ Global protection:', error.message);
});
