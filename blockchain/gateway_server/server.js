// blockchain/gateway_server/server.js

const express = require('express');
const cors = require('cors');
const morgan = require('morgan');

const app   = express();
const PORT  = process.env.PORT   || 8099;
const AI_API = process.env.AI_API || 'http://localhost:5051';

app.use(morgan('dev'));
app.use(express.json());

// CORS — allow both http://127.0.0.1:5500 and http://localhost:5500
app.use(cors({
  origin: (origin, cb) => {
    // allow null (file://), localhost, and 127.0.0.1
    if (!origin) return cb(null, true);
    try {
      const u = new URL(origin);
      const ok = (u.hostname === 'localhost' || u.hostname === '127.0.0.1');
      return cb(null, ok);
    } catch {
      return cb(null, false);
    }
  },
  methods: ['GET','POST','OPTIONS'],
  allowedHeaders: ['Content-Type','Authorization']
}));
app.options('*', cors()); // preflight

// health
app.get('/health', (req,res) => res.json({ok:true, gateway:'up'}));

// gateway ⇄ flask health passthrough
app.get('/health/flask', async (req,res) => {
  try {
    const r = await fetch(`${AI_API}/health`);
    const j = await r.json();
    res.json({ok:true, flask:j});
  } catch (e) {
    res.status(502).json({ok:false, error:'flask_unreachable', detail: String(e)});
  }
});

// proxy verify
app.post('/verify', async (req,res) => {
  try {
    const r = await fetch(`${AI_API}/predict`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(req.body || {})
    });
    const j = await r.json();
    res.status(r.status).json(j);
  } catch (e) {
    res.status(502).json({ok:false, error:'flask_down', detail: String(e)});
  }
});

// tiny text logs (optional)
app.get('/logs', (req,res) => {
  res.type('text/plain').send(`gateway: up\nAI_API -> ${AI_API}\n`);
});

app.listen(PORT, () => {
  console.log(`Gateway server listening on :${PORT}`);
  console.log(`Forwarding to Flask at ${AI_API}`);
});


