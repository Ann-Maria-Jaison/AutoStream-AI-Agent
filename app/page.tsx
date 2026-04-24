'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Sparkles, Zap, Shield, ChevronDown } from 'lucide-react'

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  deepest: '#091413',
  dark:    '#285A48',
  mid:     '#408A71',
  mint:    '#B0E4CC',
}

// ─── Types ────────────────────────────────────────────────────────────────────
interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}

// ─── Global keyframes (injected once) ────────────────────────────────────────
const STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: ${C.deepest};
    font-family: 'DM Sans', sans-serif;
    overflow: hidden;
  }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: ${C.dark}; border-radius: 99px; }

  @keyframes fadeUp   { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  @keyframes fadeIn   { from { opacity:0; } to { opacity:1; } }
  @keyframes popIn    { from { opacity:0; transform:scale(0.85); } to { opacity:1; transform:scale(1); } }
  @keyframes pulse    { 0%,100% { opacity:1; } 50% { opacity:.35; } }
  @keyframes spin     { to { transform:rotate(360deg); } }
  @keyframes shimmer  { from { background-position:200% center; } to { background-position:-200% center; } }
  @keyframes orb1     { 0%,100%{transform:translate(0,0) scale(1);}50%{transform:translate(60px,-40px) scale(1.15);} }
  @keyframes orb2     { 0%,100%{transform:translate(0,0) scale(1);}50%{transform:translate(-50px,30px) scale(1.1);} }
  @keyframes typing   {
    0%,80%,100% { transform:scale(0.6); opacity:.3; }
    40%          { transform:scale(1);   opacity:1;  }
  }
  @keyframes slideIn  {
    from { opacity:0; transform:translateX(20px) scale(0.97); }
    to   { opacity:1; transform:translateX(0)    scale(1);    }
  }
  @keyframes slideInL {
    from { opacity:0; transform:translateX(-20px) scale(0.97); }
    to   { opacity:1; transform:translateX(0)     scale(1);    }
  }
  @keyframes glow {
    0%,100% { box-shadow: 0 0 20px ${C.mid}55; }
    50%      { box-shadow: 0 0 40px ${C.mid}99, 0 0 80px ${C.mid}33; }
  }

  .msg-user   { animation: slideIn  0.3s cubic-bezier(.34,1.56,.64,1) both; }
  .msg-bot    { animation: slideInL 0.3s cubic-bezier(.34,1.56,.64,1) both; }
  .send-btn:hover  { transform: scale(1.07); }
  .send-btn:active { transform: scale(0.95); }
  .send-btn { transition: transform 0.15s, background 0.2s, box-shadow 0.2s; }

  .input-field {
    background: transparent;
    border: none;
    outline: none;
    color: ${C.mint};
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    width: 100%;
    resize: none;
  }
  .input-field::placeholder { color: ${C.mint}55; }

  .quick-chip {
    transition: all 0.18s;
    cursor: pointer;
  }
  .quick-chip:hover {
    background: ${C.mid}33 !important;
    border-color: ${C.mid} !important;
    transform: translateY(-1px);
  }
  .quick-chip:active { transform: scale(0.97); }

  .scroll-hint {
    animation: fadeIn 0.5s 1s both;
  }
`

// ─── Ambient background orbs ──────────────────────────────────────────────────
function AmbientBg() {
  return (
    <div style={{ position:'absolute', inset:0, overflow:'hidden', pointerEvents:'none', zIndex:0 }}>
      <div style={{
        position:'absolute', top:'-10%', left:'-5%',
        width:500, height:500, borderRadius:'50%',
        background:`radial-gradient(circle, ${C.dark}66 0%, transparent 70%)`,
        animation:'orb1 12s ease-in-out infinite',
        filter:'blur(2px)',
      }}/>
      <div style={{
        position:'absolute', bottom:'-10%', right:'-5%',
        width:600, height:600, borderRadius:'50%',
        background:`radial-gradient(circle, ${C.dark}44 0%, transparent 70%)`,
        animation:'orb2 15s ease-in-out infinite',
        filter:'blur(2px)',
      }}/>
      {/* Grid overlay */}
      <div style={{
        position:'absolute', inset:0,
        backgroundImage:`linear-gradient(${C.dark}18 1px, transparent 1px),
                         linear-gradient(90deg, ${C.dark}18 1px, transparent 1px)`,
        backgroundSize:'48px 48px',
      }}/>
    </div>
  )
}

// ─── Typing dots ──────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display:'flex', gap:5, padding:'4px 2px', alignItems:'center' }}>
      {[0,1,2].map(i => (
        <span key={i} style={{
          width:7, height:7, borderRadius:'50%', background:C.mid,
          display:'inline-block',
          animation:`typing 1.2s ${i*0.2}s ease-in-out infinite`,
        }}/>
      ))}
    </div>
  )
}

// ─── Message bubble ───────────────────────────────────────────────────────────
function Bubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  return (
    <div
      className={isUser ? 'msg-user' : 'msg-bot'}
      style={{
        display:'flex',
        gap:10,
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        alignItems:'flex-end',
        marginBottom:16,
      }}
    >
      {/* Bot avatar */}
      {!isUser && (
        <div style={{
          flexShrink:0, width:32, height:32, borderRadius:'50%',
          background:`linear-gradient(135deg, ${C.mid}, ${C.dark})`,
          border:`1px solid ${C.mid}66`,
          display:'flex', alignItems:'center', justifyContent:'center',
        }}>
          <Bot size={15} color={C.mint}/>
        </div>
      )}

      <div style={{ maxWidth:'72%', display:'flex', flexDirection:'column', gap:4, alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        {/* Bubble */}
        <div style={{
          padding:'12px 16px',
          borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
          background: isUser
            ? `linear-gradient(135deg, ${C.mid}, ${C.dark})`
            : `${C.dark}55`,
          border: isUser ? 'none' : `1px solid ${C.dark}99`,
          backdropFilter:'blur(8px)',
          color: C.mint,
          fontSize:14,
          lineHeight:1.65,
          whiteSpace:'pre-wrap',
          wordBreak:'break-word',
          boxShadow: isUser ? `0 4px 20px ${C.mid}33` : 'none',
        }}>
          {msg.content}
        </div>
        {/* Time */}
        <span style={{ fontSize:11, color:`${C.mint}44`, paddingInline:4 }}>
          {msg.timestamp.toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' })}
        </span>
      </div>

      {/* User avatar */}
      {isUser && (
        <div style={{
          flexShrink:0, width:32, height:32, borderRadius:'50%',
          background:`${C.dark}88`,
          border:`1px solid ${C.dark}`,
          display:'flex', alignItems:'center', justifyContent:'center',
        }}>
          <User size={15} color={C.mint}/>
        </div>
      )}
    </div>
  )
}

// ─── Empty state ──────────────────────────────────────────────────────────────
function EmptyState({ onQuick }: { onQuick: (t: string) => void }) {
  const chips = [
    "What's in the Basic plan?",
    "Tell me about Pro pricing",
    "I want to sign up for Pro",
    "Do you offer refunds?",
  ]
  return (
    <div style={{
      display:'flex', flexDirection:'column', alignItems:'center',
      justifyContent:'center', height:'100%', gap:24, padding:'0 24px',
      animation:'fadeUp 0.6s ease both',
    }}>
      {/* Orb icon */}
      <div style={{
        width:80, height:80, borderRadius:'50%',
        background:`radial-gradient(circle at 35% 35%, ${C.mid}, ${C.dark})`,
        display:'flex', alignItems:'center', justifyContent:'center',
        animation:'glow 3s ease-in-out infinite',
        boxShadow:`0 0 40px ${C.mid}55`,
      }}>
        <Bot size={36} color={C.mint}/>
      </div>

      <div style={{ textAlign:'center' }}>
        <h2 style={{
          fontFamily:"'Syne', sans-serif", fontWeight:800,
          fontSize:24, color:'#fff', marginBottom:8,
        }}>
          AutoStream AI
        </h2>
        <p style={{ color:`${C.mint}88`, fontSize:14, lineHeight:1.7, maxWidth:320 }}>
          Ask me about pricing, features, or anything AutoStream. I'm here to help you create amazing content.
        </p>
      </div>

      {/* Feature pills */}
      <div style={{ display:'flex', gap:10, flexWrap:'wrap', justifyContent:'center' }}>
        {[
          { icon:<Sparkles size={12}/>, label:'RAG-Powered' },
          { icon:<Zap size={12}/>, label:'Instant Replies' },
          { icon:<Shield size={12}/>, label:'Lead Capture' },
        ].map(({ icon, label }) => (
          <div key={label} style={{
            display:'flex', alignItems:'center', gap:6,
            background:`${C.dark}44`, border:`1px solid ${C.dark}`,
            borderRadius:999, padding:'5px 12px',
            color:C.mint, fontSize:12, fontWeight:500,
          }}>
            <span style={{ color:C.mid }}>{icon}</span> {label}
          </div>
        ))}
      </div>

      {/* Quick prompts */}
      <div style={{ width:'100%', maxWidth:480 }}>
        <p style={{ color:`${C.mint}44`, fontSize:11, fontWeight:600, letterSpacing:2, textAlign:'center', marginBottom:12 }}>
          TRY ASKING
        </p>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
          {chips.map(c => (
            <button
              key={c}
              className="quick-chip"
              onClick={() => onQuick(c)}
              style={{
                background:`${C.dark}22`, border:`1px solid ${C.dark}88`,
                borderRadius:10, padding:'10px 14px', textAlign:'left',
                color:C.mint, fontSize:13, lineHeight:1.4,
                cursor:'pointer', fontFamily:"'DM Sans', sans-serif",
              }}
            >
              {c}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Header ───────────────────────────────────────────────────────────────────
function Header({ msgCount }: { msgCount: number }) {
  return (
    <div style={{
      padding:'16px 20px',
      borderBottom:`1px solid ${C.dark}66`,
      display:'flex', alignItems:'center', gap:14,
      backdropFilter:'blur(12px)',
      background:`${C.deepest}cc`,
      flexShrink:0,
    }}>
      {/* Logo */}
      <div style={{
        width:40, height:40, borderRadius:12,
        background:`linear-gradient(135deg, ${C.mid}, ${C.dark})`,
        display:'flex', alignItems:'center', justifyContent:'center',
        boxShadow:`0 0 16px ${C.mid}44`,
        flexShrink:0,
      }}>
        <Bot size={20} color={C.mint}/>
      </div>

      <div style={{ flex:1, minWidth:0 }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <span style={{
            fontFamily:"'Syne', sans-serif", fontWeight:700,
            fontSize:17, color:'#fff', letterSpacing:'-0.3px',
          }}>
            AutoStream AI
          </span>
          {/* Online badge */}
          <span style={{
            display:'flex', alignItems:'center', gap:4,
            background:`${C.dark}66`, border:`1px solid ${C.mid}44`,
            borderRadius:999, padding:'2px 8px',
            color:C.mid, fontSize:10, fontWeight:600, letterSpacing:1,
          }}>
            <span style={{ width:5, height:5, borderRadius:'50%', background:C.mid, display:'inline-block', animation:'pulse 2s infinite' }}/>
            ONLINE
          </span>
        </div>
        <p style={{ color:`${C.mint}55`, fontSize:12, marginTop:2 }}>
          Powered by Inflx · {msgCount > 0 ? `${msgCount} message${msgCount!==1?'s':''}` : 'Ask anything'}
        </p>
      </div>

      {/* Session indicator */}
      <div style={{
        background:`${C.dark}44`, border:`1px solid ${C.dark}`,
        borderRadius:8, padding:'4px 10px',
        color:`${C.mint}55`, fontSize:11,
        display:'none',
      }}>
        Session active
      </div>
    </div>
  )
}

// ─── Input area ───────────────────────────────────────────────────────────────
function InputBar({
  value, onChange, onSend, onKeyDown, disabled,
}: {
  value: string
  onChange: (v: string) => void
  onSend: () => void
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void
  disabled: boolean
}) {
  const taRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = taRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }, [value])

  const canSend = value.trim().length > 0 && !disabled

  return (
    <div style={{
      padding:'12px 16px 16px',
      borderTop:`1px solid ${C.dark}55`,
      background:`${C.deepest}ee`,
      backdropFilter:'blur(12px)',
      flexShrink:0,
    }}>
      <div style={{
        display:'flex', gap:10, alignItems:'flex-end',
        background:`${C.dark}33`,
        border:`1px solid ${canSend ? C.mid+'66' : C.dark+'99'}`,
        borderRadius:16, padding:'10px 12px',
        transition:'border-color 0.25s',
      }}>
        <textarea
          ref={taRef}
          className="input-field"
          value={value}
          onChange={e => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message AutoStream AI…"
          disabled={disabled}
          rows={1}
          style={{
            background:'transparent', border:'none', outline:'none',
            color:C.mint, fontFamily:"'DM Sans', sans-serif",
            fontSize:15, resize:'none', width:'100%', lineHeight:1.5,
            minHeight:24, maxHeight:120, overflowY:'auto',
          }}
        />

        {/* Send button */}
        <button
          className="send-btn"
          onClick={onSend}
          disabled={!canSend}
          style={{
            flexShrink:0,
            width:38, height:38, borderRadius:12, border:'none',
            background: canSend ? C.mid : `${C.dark}66`,
            color: canSend ? C.mint : `${C.mint}44`,
            display:'flex', alignItems:'center', justifyContent:'center',
            cursor: canSend ? 'pointer' : 'not-allowed',
            boxShadow: canSend ? `0 0 20px ${C.mid}55` : 'none',
          }}
        >
          {disabled
            ? <div style={{ width:14, height:14, border:`2px solid ${C.mint}55`, borderTopColor:C.mint, borderRadius:'50%', animation:'spin 0.7s linear infinite' }}/>
            : <Send size={16}/>
          }
        </button>
      </div>

      <p style={{ fontSize:11, color:`${C.mint}33`, textAlign:'center', marginTop:8 }}>
        Press <kbd style={{ background:`${C.dark}44`, border:`1px solid ${C.dark}`, borderRadius:4, padding:'1px 5px', fontFamily:'monospace', fontSize:10, color:`${C.mint}55` }}>Enter</kbd> to send &nbsp;·&nbsp; <kbd style={{ background:`${C.dark}44`, border:`1px solid ${C.dark}`, borderRadius:4, padding:'1px 5px', fontFamily:'monospace', fontSize:10, color:`${C.mint}55` }}>Shift+Enter</kbd> for new line
      </p>
    </div>
  )
}

// ─── Scroll-to-bottom button ──────────────────────────────────────────────────
function ScrollToBottom({ onClick, visible }: { onClick: () => void; visible: boolean }) {
  return (
    <button
      onClick={onClick}
      style={{
        position:'absolute', bottom:16, left:'50%', transform:'translateX(-50%)',
        display:'flex', alignItems:'center', gap:6,
        background:`${C.dark}ee`, border:`1px solid ${C.mid}55`,
        borderRadius:999, padding:'6px 14px',
        color:C.mint, fontSize:12, cursor:'pointer',
        backdropFilter:'blur(8px)',
        opacity: visible ? 1 : 0,
        pointerEvents: visible ? 'auto' : 'none',
        transition:'opacity 0.25s',
        zIndex:10,
        boxShadow:`0 4px 16px ${C.deepest}cc`,
      }}
    >
      <ChevronDown size={14}/> Scroll to latest
    </button>
  )
}

// ─── Main chat interface ──────────────────────────────────────────────────────
export default function ChatInterface() {
  const [messages, setMessages]   = useState<Message[]>([])
  const [input, setInput]         = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId]               = useState(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const [showScroll, setShowScroll] = useState(false)

  const scrollRef  = useRef<HTMLDivElement>(null)
  const bottomRef  = useRef<HTMLDivElement>(null)

  // Auto-scroll
  const scrollToBottom = useCallback((smooth = true) => {
    bottomRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'instant' })
  }, [])

  useEffect(() => {
    if (messages.length) scrollToBottom()
  }, [messages, isLoading])

  // Show/hide scroll hint
  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60
    setShowScroll(!atBottom && messages.length > 0)
  }

  // Send message (same logic as original)
  const sendMessage = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim()
    if (!text || isLoading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      content: text,
      role: 'user',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        content: data.response || data.message || 'Sorry, I received an empty response.',
        role: 'assistant',
        timestamp: new Date(),
      }])
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        content: 'Connection error — please make sure the backend is running on localhost:8000.',
        role: 'assistant',
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: STYLES }}/>

      {/* Full-screen layout */}
      <div style={{
        width:'100vw', height:'100vh',
        background:C.deepest,
        display:'flex', alignItems:'center', justifyContent:'center',
        position:'relative',
        overflow:'hidden',
      }}>
        <AmbientBg/>

        {/* Chat card */}
        <div
          style={{
            position:'relative', zIndex:1,
            width:'100%', maxWidth:720,
            height:'100vh',
            display:'flex', flexDirection:'column',
            background:`${C.deepest}bb`,
            backdropFilter:'blur(20px)',
            borderLeft:`1px solid ${C.dark}55`,
            borderRight:`1px solid ${C.dark}55`,
            animation:'fadeIn 0.4s ease both',
          }}
        >
          {/* Header */}
          <Header msgCount={messages.length}/>

          {/* Messages area */}
          <div
            ref={scrollRef}
            onScroll={handleScroll}
            style={{
              flex:1, overflowY:'auto',
              padding:'16px 20px',
              display:'flex', flexDirection:'column',
              position:'relative',
            }}
          >
            {messages.length === 0 && !isLoading
              ? <EmptyState onQuick={t => sendMessage(t)}/>
              : (
                <div style={{ paddingBottom:8 }}>
                  {messages.map(m => <Bubble key={m.id} msg={m}/>)}

                  {/* Typing indicator */}
                  {isLoading && (
                    <div className="msg-bot" style={{ display:'flex', gap:10, alignItems:'flex-end', marginBottom:16 }}>
                      <div style={{
                        flexShrink:0, width:32, height:32, borderRadius:'50%',
                        background:`linear-gradient(135deg, ${C.mid}, ${C.dark})`,
                        border:`1px solid ${C.mid}66`,
                        display:'flex', alignItems:'center', justifyContent:'center',
                      }}>
                        <Bot size={15} color={C.mint}/>
                      </div>
                      <div style={{
                        padding:'12px 16px',
                        background:`${C.dark}55`, border:`1px solid ${C.dark}99`,
                        borderRadius:'20px 20px 20px 4px',
                      }}>
                        <TypingDots/>
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef}/>
                </div>
              )
            }

            <ScrollToBottom
              visible={showScroll}
              onClick={() => scrollToBottom()}
            />
          </div>

          {/* Input */}
          <InputBar
            value={input}
            onChange={setInput}
            onSend={() => sendMessage()}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
        </div>
      </div>
    </>
  )
}