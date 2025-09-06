const http = require('http');
const express = require('express');
const cors = require('cors');
const { WebSocketServer } = require('ws');
const os = require('os');
const pty = require('node-pty');

const app = express();
app.use(cors());
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/term" });

wss.on("connection", (socket) => {
  let shell = os.platform() === "win32" ? "powershell.exe" : process.env.SHELL || "bash";
  let cols = 80, rows = 24;
  let p = null;
  socket.on("message", (raw) => {
    try {
      const msg = JSON.parse(raw.toString());
      if (msg.type === "spawn") {
        if (msg.shell && msg.shell !== "auto") shell = msg.shell;
        cols = msg.cols || cols; rows = msg.rows || rows;
        p = pty.spawn(shell, [], { name: "xterm-color", cols, rows, cwd: process.cwd(), env: process.env });
        p.onData((d) => socket.send(Buffer.from(d)));
        p.onExit(({ exitCode }) => socket.send(JSON.stringify({ type: "exit", code: exitCode })));
      } else if (msg.type === "input" && p) { p.write(msg.data); }
      else if (msg.type === "resize" && p) { p.resize(msg.cols, msg.rows); socket.send(JSON.stringify({ type: "resize", cols: msg.cols, rows: msg.rows })); }
    } catch {}
  });
  socket.on("close", () => { if (p) try { p.kill(); } catch {} });
});
const PORT = process.env.KYROS_DAEMON_PORT || 8787;
server.listen(PORT, () => console.log(`[kyros-daemon] ws://localhost:${PORT}/term`));