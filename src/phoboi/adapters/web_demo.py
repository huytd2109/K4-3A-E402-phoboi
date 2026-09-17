"""Local web demo using the Figma Make interaction model.

The server intentionally uses only the Python standard library so the demo can
run offline. The browser UI talks to the real Pipeline through /api/process.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("APP_ENV", "demo")

from phoboi.config import Config
from phoboi.pipeline import Pipeline

logger = logging.getLogger(__name__)

HTML_CONTENT = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Phoboi - Trợ lý logistics</title>
  <style>
    :root {
      --rail:#1e1f22; --sidebar:#2b2d31; --panel:#232428; --chat:#313338;
      --input:#383a40; --hover:#35373c; --line:#3f4147; --text:#dcddde;
      --muted:#949ba4; --dim:#6d6f78; --heading:#f2f3f5; --brand:#5865f2;
      --brand-2:#7289da; --green:#23a559; --green-hi:#57f287;
      --amber:#f0b232; --red:#ed4245; --radius:6px;
    }
    * { box-sizing:border-box; }
    html, body { height:100%; margin:0; overflow:hidden; }
    body { background:var(--rail); color:var(--text); font:14px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
    button, input { font:inherit; }
    button { border:0; }
    .app { display:grid; grid-template-columns:72px 260px minmax(0,1fr); height:100vh; height:100dvh; min-height:0; overflow:hidden; }
    .rail { background:var(--rail); padding:12px 0; display:flex; flex-direction:column; align-items:center; gap:9px; }
    .server { width:46px; height:46px; border-radius:16px; display:grid; place-items:center; background:var(--chat); color:var(--muted); font-weight:800; cursor:pointer; position:relative; transition:.16s; }
    .server:hover,.server.active { border-radius:12px; background:var(--brand); color:white; }
    .server.active::before { content:""; position:absolute; left:-13px; width:4px; height:30px; background:white; border-radius:0 4px 4px 0; }
    .rail-sep { width:32px; height:1px; background:var(--line); }
    .rail-user { margin-top:auto; width:34px; height:34px; border-radius:50%; display:grid; place-items:center; background:#3498db; color:white; font-weight:700; }
    .sidebar { background:var(--sidebar); min-width:0; display:flex; flex-direction:column; }
    .workspace { height:49px; padding:0 14px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--rail); color:var(--heading); font-weight:700; }
    .side-scroll { padding:8px; overflow:auto; flex:1; }
    .side-label { padding:12px 8px 6px; color:var(--dim); font:600 10px/1.2 ui-monospace, SFMono-Regular, Consolas, monospace; text-transform:uppercase; letter-spacing:.08em; }
    .channel { width:100%; display:flex; align-items:center; gap:9px; color:var(--muted); background:transparent; padding:7px 8px; border-radius:4px; text-align:left; cursor:pointer; }
    .channel:hover,.channel.active { background:var(--hover); color:var(--heading); }
    .channel-icon { width:20px; color:var(--dim); font-size:17px; text-align:center; }
    .suggestion-list { display:grid; gap:7px; padding:2px 8px; }
    .suggestion-item { color:var(--muted); border-left:2px solid var(--line); padding:5px 8px; font-size:11px; overflow-wrap:anywhere; }
    .suggestion-item small { display:block; margin-top:2px; color:var(--dim); font:9px ui-monospace,monospace; }
    .badge { display:inline-flex; align-items:center; min-height:20px; border:1px solid currentColor; border-radius:4px; padding:2px 7px; font:600 10px/1 ui-monospace, SFMono-Regular, Consolas, monospace; letter-spacing:.04em; white-space:nowrap; }
    .badge.green { color:var(--green-hi); background:#173e2b; }
    .badge.amber { color:var(--amber); background:#49340f; }
    .badge.red { color:#ff7779; background:#491416; }
    .badge.brand { color:#a5b4fc; background:#34385f; }
    .badge.gray { color:#b5bac1; background:#383a40; }
    .profile { height:54px; background:var(--panel); padding:8px; display:flex; align-items:center; gap:9px; }
    .profile-avatar,.avatar { border-radius:50%; display:grid; place-items:center; color:white; font-weight:700; flex:0 0 auto; }
    .profile-avatar { width:34px; height:34px; background:#3498db; position:relative; }
    .profile-avatar::after { content:""; position:absolute; right:-1px; bottom:-1px; width:10px; height:10px; border:2px solid var(--panel); background:var(--green); border-radius:50%; }
    .profile-copy { min-width:0; flex:1; }
    .profile-copy strong { color:var(--heading); display:block; font-size:12px; }
    .profile-copy span { color:var(--dim); font:10px ui-monospace,monospace; }
    .chat-shell { min-width:0; min-height:0; height:100%; display:flex; flex-direction:column; overflow:hidden; background:var(--chat); }
    .topbar { height:49px; flex:0 0 49px; padding:0 16px; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--rail); box-shadow:0 1px 0 #1e1f2266; }
    .hash { color:var(--muted); font-size:20px; font-weight:700; }
    .top-title { min-width:0; flex:1; overflow:hidden; }
    .top-title strong { color:var(--heading); display:block; line-height:1.1; }
    .top-title span { color:var(--dim); font:10px ui-monospace,monospace; display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .top-actions { margin-left:auto; display:flex; align-items:center; gap:10px; color:var(--muted); flex:0 0 auto; }
    .icon-btn { width:30px; height:30px; border-radius:4px; background:transparent; color:var(--muted); cursor:pointer; font-size:16px; }
    .icon-btn:hover { background:var(--hover); color:var(--heading); }
    .demo-state { color:var(--amber); border-color:#f0b23266; background:#4a3410; }
    .chat-layout { flex:1; min-width:0; min-height:0; display:flex; overflow:hidden; }
    .conversation { flex:1 1 auto; min-width:0; min-height:0; height:100%; display:flex; flex-direction:column; overflow:hidden; }
    .messages { flex:1 1 auto; min-width:0; min-height:0; max-width:100%; overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain; scrollbar-gutter:stable; touch-action:pan-y; -webkit-overflow-scrolling:touch; padding:10px 16px 18px; scroll-behavior:smooth; }
    .date-rule { display:flex; align-items:center; gap:12px; color:var(--dim); font:10px ui-monospace,monospace; text-transform:uppercase; margin:5px 0 16px; }
    .date-rule::before,.date-rule::after { content:""; height:1px; background:var(--line); flex:1; }
    .message { display:flex; gap:12px; width:100%; padding:6px 8px; border-radius:4px; max-width:980px; margin:0 auto 7px; animation:enter .2s ease-out; }
    .message:hover { background:#2e3035; }
    .avatar { width:40px; height:40px; background:#3498db; font-size:13px; }
    .avatar.bot { background:linear-gradient(135deg,var(--brand),var(--brand-2)); }
    .message-body { min-width:0; flex:1; }
    .meta { display:flex; align-items:baseline; flex-wrap:wrap; gap:7px; margin-bottom:3px; }
    .name { color:var(--heading); font-weight:650; }
    .message.bot .name { color:#a5b4fc; }
    .bot-tag { color:white; background:var(--brand); border-radius:3px; padding:1px 5px; font:600 9px ui-monospace,monospace; }
    .time { color:var(--dim); font:10px ui-monospace,monospace; }
    .message-text { color:var(--text); white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word; }
    .message-text strong { color:var(--green-hi); }
    .message-text a,.source-link { color:#8ea1ff; text-decoration:none; }
    .message-text a:hover,.source-link:hover { text-decoration:underline; }
    .mention { color:#c2c9ff; background:#3d416f; border-radius:3px; padding:0 4px; }
    .decision { margin-top:10px; border-left:3px solid var(--brand); background:var(--panel); border-radius:var(--radius); padding:12px; }
    .decision.answer { border-left-color:var(--green); background:#1f382c; }
    .decision.clarify { border-left-color:var(--amber); background:#3b301e; }
    .decision.handoff,.decision.restrict { border-left-color:var(--red); background:#3b2426; }
    .decision.route { border-left-color:var(--brand-2); }
    .decision-head { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:7px; }
    .decision-head strong { color:var(--heading); }
    .decision-reason { color:var(--muted); font-size:12px; }
    .source-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:8px; margin-top:9px; }
    .source { background:#1e1f22; border-left:2px solid var(--brand); border-radius:4px; padding:10px; min-width:0; }
    .source.conflict { border-left-color:var(--amber); }
    .source-top { display:flex; align-items:center; gap:7px; margin-bottom:7px; }
    .source-top small { margin-left:auto; color:var(--dim); font:9px ui-monospace,monospace; }
    .source-title { color:var(--heading); font-weight:650; font-size:12px; }
    .source-grid { display:grid; grid-template-columns:auto 1fr; gap:4px 10px; color:var(--muted); font-size:11px; margin:7px 0; }
    .source-grid b { color:var(--text); font-weight:500; overflow-wrap:anywhere; }
    .source-actions { display:flex; gap:7px; margin-top:10px; }
    .action { min-height:30px; padding:6px 10px; border-radius:4px; background:#4e5058; color:var(--heading); cursor:pointer; font-size:12px; font-weight:600; }
    .action:hover { background:#62646d; }
    .action.primary { background:var(--brand); }
    .action.primary:hover { background:#4752c4; }
    .security { margin-top:8px; color:var(--amber); font:10px ui-monospace,monospace; }
    .typing { display:flex; gap:5px; align-items:center; height:22px; }
    .typing i { width:7px; height:7px; border-radius:50%; background:var(--muted); animation:bounce 1.2s infinite; }
    .typing i:nth-child(2) { animation-delay:.15s; } .typing i:nth-child(3) { animation-delay:.3s; }
    .composer { flex:0 0 auto; padding:10px 16px 16px; }
    .quick-row { display:flex; gap:7px; overflow:auto; margin-bottom:8px; }
    .quick-row button { flex:0 0 auto; border:1px solid var(--line); background:var(--panel); color:var(--muted); padding:6px 10px; border-radius:4px; cursor:pointer; font-size:12px; }
    .quick-row button:hover { color:var(--heading); border-color:var(--brand); }
    .input-wrap { max-width:980px; margin:auto; display:flex; align-items:center; gap:9px; background:var(--input); border-radius:8px; padding:5px 7px 5px 14px; }
    .input-wrap:focus-within { outline:1px solid #5865f288; }
    .input-wrap input { flex:1; min-width:0; color:var(--heading); background:transparent; border:0; outline:0; padding:8px 0; }
    .input-wrap input::placeholder { color:var(--dim); }
    .send { width:34px; height:34px; border-radius:4px; display:grid; place-items:center; background:var(--brand); color:white; cursor:pointer; font-size:17px; }
    .send:hover { background:#4752c4; }
    .send:disabled { opacity:.55; cursor:wait; }
    .drawer { width:min(330px,88vw); min-height:0; flex:0 0 auto; background:var(--sidebar); border-left:1px solid var(--rail); display:none; flex-direction:column; overflow:hidden; }
    .drawer.open { display:flex; }
    .drawer-head { height:49px; display:flex; align-items:center; justify-content:space-between; padding:0 14px; border-bottom:1px solid var(--rail); }
    .drawer-head strong { color:var(--heading); font:650 11px ui-monospace,monospace; text-transform:uppercase; }
    .drawer-body { min-height:0; padding:14px; overflow:auto; }
    .empty { color:var(--muted); font-size:12px; }
    @keyframes enter { from { opacity:0; transform:translateY(3px); } }
    @keyframes bounce { 0%,70%,100% { transform:translateY(0); opacity:.45; } 35% { transform:translateY(-4px); opacity:1; } }
    @media (max-width: 920px) {
      .app { grid-template-columns:64px 220px minmax(0,1fr); }
      .drawer { position:fixed; right:0; top:0; bottom:0; z-index:5; box-shadow:-12px 0 30px #0008; }
    }
    @media (max-width: 720px) {
      .app { grid-template-columns:1fr; }
      .rail,.sidebar { display:none; }
      .topbar { padding:0 12px; }
      .top-actions { gap:4px; }
      .demo-state { font-size:0; padding:2px 5px; }
      .demo-state::after { content:"DEMO"; font-size:9px; }
      .messages { padding-left:7px; padding-right:7px; }
      .message { gap:9px; }
      .avatar { width:34px; height:34px; }
      .source-list { grid-template-columns:1fr; }
      .composer { padding:8px; }
    }
    @media (prefers-reduced-motion:reduce) { * { animation:none!important; scroll-behavior:auto!important; transition:none!important; } }
  </style>
</head>
<body>
<div class="app">
  <nav class="rail" aria-label="Máy chủ">
    <button class="server active" title="Khóa AI">AI</button>
    <div class="rail-sep"></div>
    <button class="server" title="Code">&lt;/&gt;</button>
    <button class="server" title="Dự án">P</button>
    <div class="rail-user">A</div>
  </nav>
  <aside class="sidebar">
    <div class="workspace"><span>Khóa AI 2026</span><span>⌄</span></div>
    <div class="side-scroll">
      <div class="side-label">Kênh văn bản</div>
      <button class="channel"><span class="channel-icon">#</span><span>general</span></button>
      <button class="channel"><span class="channel-icon">#</span><span>thông-báo</span></button>
      <button class="channel"><span class="channel-icon">#</span><span>nộp-lab</span></button>
      <button class="channel active"><span class="channel-icon">#</span><span>hỏi-trợ-lý</span></button>
      <button class="channel"><span class="channel-icon">#</span><span>hỗ-trợ</span></button>
      <div class="side-label">Gợi ý câu hỏi</div>
      <div class="suggestion-list" id="suggestionList"></div>
    </div>
    <div class="profile"><div class="profile-avatar">A</div><div class="profile-copy"><strong>Văn An</strong><span>Học viên</span></div><button class="icon-btn" title="Cài đặt">⚙</button></div>
  </aside>
  <main class="chat-shell">
    <header class="topbar">
      <span class="hash">#</span>
      <div class="top-title"><strong>hỏi-trợ-lý</strong><span id="headerStatus">Verified-only logistics assistant</span></div>
      <div class="top-actions"><span class="badge gray" id="llmState">ROUTER...</span><span class="badge gray" id="packState">PACK...</span><span class="badge demo-state">DEMO FIXTURE</span><button class="icon-btn" id="sourceToggle" title="Nguồn chính thức">ⓘ</button></div>
    </header>
    <div class="chat-layout">
      <section class="conversation" aria-label="Hội thoại">
        <div class="messages" id="messages"><div class="date-rule">Hôm nay</div></div>
        <div class="composer">
          <div class="quick-row" id="quickRow"></div>
          <form class="input-wrap" id="chatForm"><span class="hash">+</span><input id="userInput" maxlength="2000" autocomplete="off" placeholder="Nhắn tin vào #hỏi-trợ-lý" aria-label="Tin nhắn"><button class="send" id="sendButton" title="Gửi" aria-label="Gửi">➤</button></form>
        </div>
      </section>
      <aside class="drawer" id="drawer" aria-label="Nguồn chính thức"><div class="drawer-head"><strong>Nguồn chính thức</strong><button class="icon-btn" id="drawerClose" title="Đóng">×</button></div><div class="drawer-body" id="drawerBody"><p class="empty">Chưa có nguồn nào được chọn.</p></div></aside>
    </div>
  </main>
</div>
<script>
const suggestions = [
  {id:'M07416', label:'Hạn nộp Lab02 là khi nào?', message:'Hạn nộp Lab02 là khi nào?'},
  {id:'M40677', label:'Nộp đúng giờ nhưng commit lên muộn?', message:'Tôi nộp codelab trên VLearn đúng giờ deadline nhưng commit trên máy bị lỗi và đẩy lên sau đó thì có được tính là nộp đúng hạn không?'},
  {id:'M65121', label:'Daily standup nộp theo nhóm hay cá nhân?', message:'Quy cách nộp daily standup: một người nộp cho cả nhóm hay mỗi cá nhân đều phải nộp?'},
  {id:'M84993', label:'Kiểm tra trạng thái đã nộp codelab', message:'Kiểm tra xem tôi đã nộp bài codelab chưa.'},
];
const outcomes = {
  ANSWER_VERIFIED:['Đã xác minh','answer','green'], CLARIFY:['Cần làm rõ','clarify','amber'],
  HANDOFF_NO_SOURCE:['Đã chuyển TA','handoff','red'], HANDOFF_CONFLICT:['Xung đột nguồn','handoff','red'],
  HANDOFF_LOW_CONFIDENCE:['Đã chuyển TA','handoff','red'], RESTRICT_PERSONAL:['Ngoài phạm vi','restrict','red'],
  ANSWER_GREETING:['Chào hỏi','route','brand'], ROUTE_LEARNING:['Chuyển hướng học tập','route','brand'], OUT_OF_SCOPE:['Ngoài phạm vi','route','gray']
};
const messages = document.getElementById('messages'), input = document.getElementById('userInput'), sendButton = document.getElementById('sendButton'), drawer = document.getElementById('drawer'), drawerBody = document.getElementById('drawerBody');
let lastSources = [];
function escapeHTML(value='') { return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function richText(value='') { let text=escapeHTML(value); text=text.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>'); return text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noreferrer">$1 ↗</a>'); }
function now() { return new Date().toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'}); }
function scrollBottom() { messages.scrollTop=messages.scrollHeight; }
function addMessage(kind,body,name) { const row=document.createElement('article'); row.className=`message ${kind}`; row.innerHTML=`<div class="avatar ${kind==='bot'?'bot':''}">${kind==='bot'?'P':'A'}</div><div class="message-body"><div class="meta"><span class="name">${escapeHTML(name)}</span>${kind==='bot'?'<span class="bot-tag">BOT</span>':''}<span class="time">${now()}</span></div>${body}</div>`; messages.appendChild(row); scrollBottom(); return row; }
function addStudent(text) { addMessage('student',`<div class="message-text"><span class="mention">@Trợ lý</span> ${escapeHTML(text)}</div>`,'Học viên'); }
function addTyping() { const row=addMessage('bot','<div class="typing"><i></i><i></i><i></i><span class="decision-reason">Đang phân loại và kiểm tra nguồn chính thức...</span></div>','Phoboi'); row.id='typing'; }
function sourceCard(source,conflict=false,index=0) { const deadline=source.deadline?new Intl.DateTimeFormat('vi-VN',{dateStyle:'short',timeStyle:'short',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date(source.deadline))+' (UTC+7)':'Không có'; return `<div class="source ${conflict?'conflict':''}"><div class="source-top"><span class="badge ${conflict?'amber':'brand'}">OFFICIAL SOURCE</span><small>${escapeHTML(source.source_id)}</small></div><div class="source-title">${escapeHTML(source.task_id)}</div><div class="source-grid"><span>Deadline</span><b>${escapeHTML(deadline)}</b><span>Phạm vi</span><b>${escapeHTML([source.cohort,source.class_scope].filter(Boolean).join(' · ')||'Chung')}</b><span>Vai trò</span><b>${escapeHTML(source.published_by_role||'N/A')}</b></div><div class="source-actions"><button class="action" onclick="showSource(${index})">Xem nguồn</button><a class="action primary source-link" href="${escapeHTML(source.source_url)}" target="_blank" rel="noreferrer">Mở tin gốc ↗</a></div></div>`; }
function renderDecision(decision,offset) { const config=outcomes[decision.outcome]||[decision.outcome,'route','gray']; const sources=decision.source?[decision.source]:(decision.sources_considered||[]); const sourceHtml=sources.length?`<div class="source-list">${sources.map((s,i)=>sourceCard(s,decision.outcome==='HANDOFF_CONFLICT',offset+i)).join('')}</div>`:''; const missing=decision.missing_fields?.length?`<div class="decision-reason">Thiếu: ${escapeHTML(decision.missing_fields.join(', '))}</div>`:''; return `<section class="decision ${config[1]}"><div class="decision-head"><span class="badge ${config[2]}">${escapeHTML(decision.outcome)}</span><strong>${escapeHTML(config[0])}</strong><span class="badge gray">${escapeHTML(decision.intent)}</span></div>${missing}<div class="decision-reason">${escapeHTML(decision.reason||'')}</div>${sourceHtml}</section>`; }
function addBot(data) { lastSources=[]; for(const d of data.decisions||[]) d.source?lastSources.push(d.source):lastSources.push(...(d.sources_considered||[])); let offset=0; const blocks=(data.decisions||[]).map(d=>{const html=renderDecision(d,offset);offset+=d.source?1:(d.sources_considered||[]).length;return html;}).join(''); const flags=(data.security_flags||[]).length?`<div class="security">Security: ${escapeHTML(data.security_flags.join(' · '))}</div>`:''; const r=data.routing||{}; const live=r.provider==='gemini'&&!r.used_fallback; const context=data.data_context||{}; const ids=context.matched_message_ids||[]; const pack=ids.length?`<span class="badge gray">PACK CONTEXT ${ids.length}</span> ${escapeHTML(ids.join(' · '))}`:'<span class="badge gray">PACK CONTEXT 0</span>'; const trace=`<div class="decision-reason"><span class="badge ${live?'brand':'amber'}">${live?'GEMINI LIVE':'RULE FALLBACK'}</span> ${escapeHTML(r.model||r.provider||'router')} ${Number.isInteger(r.latency_ms)?`· ${r.latency_ms} ms`:''} ${pack}</div>`; addMessage('bot',`<div class="message-text">${richText(data.rendered_text)}</div>${trace}${blocks}${flags}`,'Phoboi'); document.getElementById('llmState').className=`badge ${live?'brand':'amber'}`; document.getElementById('llmState').textContent=live?'GEMINI LIVE':'RULE FALLBACK'; document.getElementById('headerStatus').textContent=(data.decisions||[]).map(d=>d.outcome).join(' · ')||'Đã xử lý'; }
function showSource(index) { const s=lastSources[index]; if(!s)return; const rows=[['Source ID',s.source_id],['Task',s.task_id],['Cohort',s.cohort],['Class',s.class_scope||'Tất cả'],['Channel',s.channel_id],['Message',s.message_id],['Vai trò',s.published_by_role],['Trạng thái',s.status]]; drawerBody.innerHTML=`<span class="badge brand">OFFICIAL SOURCE</span><div class="source" style="margin-top:12px"><div class="source-title">${escapeHTML(s.task_id)}</div><div class="source-grid">${rows.map(([k,v])=>`<span>${escapeHTML(k)}</span><b>${escapeHTML(v||'N/A')}</b>`).join('')}</div><a class="action primary source-link" href="${escapeHTML(s.source_url)}" target="_blank" rel="noreferrer">Mở tin nhắn gốc ↗</a></div><p class="empty">Nguồn fixture chỉ dùng trong demo/test.</p>`; drawer.classList.add('open'); }
async function sendMessage(message) { const text=(message??input.value).trim(); if(!text||sendButton.disabled)return; input.value='';addStudent(text);addTyping();sendButton.disabled=true; try { const response=await fetch('/api/process',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})}); const data=await response.json();document.getElementById('typing')?.remove();if(!response.ok||data.error)throw new Error();addBot(data); } catch(_) { document.getElementById('typing')?.remove();addMessage('bot','<div class="decision handoff"><div class="decision-head"><span class="badge red">ERROR</span><strong>Không thể xử lý yêu cầu</strong></div><div class="decision-reason">Vui lòng thử lại sau.</div></div>','Phoboi'); } finally {sendButton.disabled=false;input.focus();} }
function buildSuggestions() { const side=document.getElementById('suggestionList'),quick=document.getElementById('quickRow'); suggestions.forEach(s=>{const item=document.createElement('div');item.className='suggestion-item';item.innerHTML=`${escapeHTML(s.label)}<small>${escapeHTML(s.id)} · Discord pack</small>`;side.appendChild(item);const q=document.createElement('button');q.type='button';q.textContent=s.label;q.title=`Điền câu hỏi từ ${s.id}`;q.onclick=()=>{input.value=s.message;input.focus();};quick.appendChild(q);}); }
document.getElementById('chatForm').addEventListener('submit',e=>{e.preventDefault();sendMessage();}); document.getElementById('sourceToggle').onclick=()=>drawer.classList.toggle('open'); document.getElementById('drawerClose').onclick=()=>drawer.classList.remove('open'); window.showSource=showSource; buildSuggestions(); addMessage('bot','<div class="message-text">Chào bạn! Mình chỉ trả lời thông tin logistics khi có nguồn chính thức còn hiệu lực. Bạn cần kiểm tra deadline, link hay cách nộp bài?</div><div class="decision route"><div class="decision-head"><span class="badge brand">VERIFIED ONLY</span><strong>Không đoán deadline</strong></div></div>','Phoboi');
fetch('/api/health').then(r=>r.json()).then(data=>{const el=document.getElementById('llmState');const configured=data.provider==='gemini'&&data.api_key_configured;el.className=`badge ${configured?'brand':'amber'}`;el.textContent=configured?'GEMINI READY':'RULE ROUTER';document.getElementById('packState').textContent=`PACK ${data.discord_pack_loaded||0}`;}).catch(()=>{});
</script>
</body>
</html>
"""


class PhoboiHandler(BaseHTTPRequestHandler):
    """HTTP adapter for the local demo."""

    pipeline: Pipeline
    max_body_bytes = 16_384

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            config = self.pipeline._config
            self._send_json(200, {
                "status": "ok",
                "provider": config.llm_provider,
                "model": config.llm_model,
                "api_key_configured": bool(config.llm_api_key),
                "source_mode": "fixture" if config.allows_fixtures else "production",
                "discord_pack_loaded": self.pipeline._discord_pack.count,
            })
            return
        if self.path != "/":
            self.send_error(404)
            return
        body = HTML_CONTENT.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/process":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "invalid_request"})
            return
        if content_length <= 0 or content_length > self.max_body_bytes:
            self._send_json(413, {"error": "request_too_large"})
            return
        try:
            data = json.loads(self.rfile.read(content_length).decode("utf-8"))
            message = data.get("message") if isinstance(data, dict) else None
            if not isinstance(message, str) or not message.strip():
                self._send_json(400, {"error": "message_required"})
                return
            result = self.pipeline.process(message)
            decisions = []
            for decision in result.decisions:
                decisions.append({
                    "outcome": decision.outcome.value,
                    "intent": decision.intent.value,
                    "reason": decision.reason,
                    "missing_fields": decision.missing_fields,
                    "source": decision.source.model_dump(mode="json") if decision.source else None,
                    "sources_considered": [source.model_dump(mode="json") for source in decision.sources_considered],
                })
            self._send_json(200, {
                "rendered_text": result.rendered_text,
                "is_fixture_data": result.is_fixture_data,
                "decisions": decisions,
                "handoffs": [handoff.model_dump(mode="json") for handoff in result.handoffs],
                "security_flags": result.audit.security_flags if result.audit else [],
                "routing": {
                    "provider": result.audit.router_provider if result.audit else "unknown",
                    "model": result.audit.router_model if result.audit else None,
                    "used_fallback": result.audit.router_used_fallback if result.audit else False,
                    "latency_ms": result.audit.router_latency_ms if result.audit else None,
                    "fallback_reason": result.audit.router_fallback_reason if result.audit else None,
                },
                "data_context": {
                    "kind": "anonymized_discord_history_non_authoritative",
                    "loaded_messages": result.audit.discord_pack_total if result.audit else 0,
                    "matched_message_ids": result.audit.discord_pack_message_ids if result.audit else [],
                    "used_for_official_answer": False,
                },
            })
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid_json"})
        except Exception:
            logger.exception("Web demo request failed")
            self._send_json(500, {"error": "internal_error"})

    def log_message(self, format: str, *args: object) -> None:
        logger.info("web_demo %s", format % args)


def run_web_demo() -> None:
    """Run the local-only web demo."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    parser = argparse.ArgumentParser(description="Phoboi web demo server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    config = Config()
    PhoboiHandler.pipeline = Pipeline(config=config)
    server = ThreadingHTTPServer((args.host, args.port), PhoboiHandler)
    print(f"Phoboi web demo: http://{args.host}:{args.port}")
    print(f"APP_ENV={config.app_env}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_web_demo()
