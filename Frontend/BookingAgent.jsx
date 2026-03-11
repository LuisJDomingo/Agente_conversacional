import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, X, Send, Check } from "lucide-react";

export default function FloatingBookingAgent({ businessId }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "bot", text: "Soy experto en atencion al cliente.¿Cómo puedo ayudarte hoy?" }
  ]);
  const [userInput, setUserInput] = useState("");
  const [isImageExpanded, setIsImageExpanded] = useState(false);
  const [isClosingImage, setIsClosingImage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Generar ID de sesión único por carga de página para evitar conflictos
  const sessionId = useRef("web-" + Math.random().toString(36).substr(2, 9));

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    if (open && !isLoading) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open, isLoading]);

  const sendMessage = async () => {
  if (!userInput.trim() || isLoading) return;
  
  const messageToSend = userInput;
  const newUserMessage = {
    id: Date.now(),
    from: "user",
    text: messageToSend,
    status: "sent" // Estado inicial: enviado
  };
  setMessages(prev => [...prev, newUserMessage]);
  setUserInput("");
  setIsLoading(true);
  
  try {
    const res = await fetch("/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        business_id: businessId,
        session_id: sessionId.current,
        message: messageToSend
      })
    });

    const data = await res.json();

    // Cuando el bot responde, marcamos todos los mensajes del usuario como leídos
    setMessages(prev => prev.map(msg => 
      (msg.from === 'user' && msg.status !== 'read') ? { ...msg, status: 'read' } : msg
    ));

    const fullReply = data.reply || "⚠️ El servidor no respondió correctamente.";

    // Dividir respuesta en oraciones para mostrar paso a paso
    const sentences = fullReply.match(/[^.?!]+[.?!]+["']?|.+/g) || [fullReply];
    
    setIsLoading(false);

    for (let i = 0; i < sentences.length; i++) {
      const text = sentences[i].trim();
      if (text) {
        if (i > 0) {
          // Pausa dinámica basada en la longitud del texto para simular escritura
          await new Promise(resolve => setTimeout(resolve, text.length * 20 + 300));
        }
        setMessages(prev => [...prev, { from: "bot", text }]);
      }
    }
  } catch (err) {
    console.error(err);
    setIsLoading(false);
    setMessages(prev => [
      ...prev,
      { from: "bot", text: "⚠️ Ahora mismo no puedo responder." }
    ]);
  } 
};

  const handleCloseImage = () => {
    setIsClosingImage(true);
    setTimeout(() => {
      setIsImageExpanded(false);
      setIsClosingImage(false);
    }, 300);
  };

  const ReadReceipt = ({ status }) => {
    const readColor = '#4fc3f7';
    const sentColor = 'rgba(0, 0, 0, 0.4)';
    const color = status === 'read' ? readColor : sentColor;

    return (
      <div style={{ position: 'relative', width: '20px', height: '16px' }}>
        <Check
          size={16}
          color={color}
          style={{
            position: 'absolute',
            right: '5px',
            transition: 'color 0.4s ease'
          }}
        />
        {status === 'read' && (
          <Check
            size={16}
            color={color}
            style={{
              position: 'absolute',
              right: '0px',
              animation: 'secondCheckIn 0.5s ease-out forwards',
              opacity: 0
            }}
          />
        )}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <style>{`
        @keyframes popIn {
          0% { transform: scale(0.5); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes popOut {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(0.5); opacity: 0; }
        }
        @keyframes secondCheckIn {
          from { transform: translateX(-6px); opacity: 0; }
          to { transform: translateX(0px); opacity: 1; }
        }
        @keyframes messageAppear {
          from { opacity: 0; transform: translateY(10px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
      {isImageExpanded && (
        <>
          <div style={styles.overlay} onClick={handleCloseImage} />
          <img 
            src="/images/martin.png" 
            style={{
              ...styles.popupImage,
              animation: isClosingImage 
                ? "popOut 0.3s cubic-bezier(0.6, -0.28, 0.735, 0.045) forwards" 
                : "popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards"
            }} 
            alt="Martín ampliado" 
            onClick={handleCloseImage} 
          />
        </>
      )}

      <div style={{ ...styles.chatWindow, ...(open ? styles.chatWindowOpen : {}) }}>
        
        {/* Header del Chat */}
        <div style={styles.header}>
            <div style={styles.headerInfo}>
                {/* REEMPLAZA ESTA URL POR LA FOTO REAL DE LA PERSONA */}
                <img 
                  src="/images/martin.png" 
                  alt="Martín" 
                  style={{ ...styles.avatar, cursor: "pointer" }}
                  onClick={() => setIsImageExpanded(true)}
                />
                <span style={styles.headerTitle}>Hola, soy Martín</span>
            </div>
            <button onClick={() => setOpen(false)} style={styles.closeBtn}>
                <X size={18} />
            </button>
        </div>

        <div style={styles.messages}>
          {messages.map((m, i) => (
            <div
              key={m.id || i}
              style={{
                ...styles.message,
                ...(m.from === "user" ? styles.user : styles.bot)
              }}
            >
              {m.text}
              {m.from === 'user' && (
                <div style={styles.receiptContainer}>
                  {/* Aquí podría ir también la hora del mensaje */}
                  <ReadReceipt status={m.status} />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
             <div style={{ ...styles.message, ...styles.bot }}>
                <span style={{ fontStyle: "italic", opacity: 0.7 }}>Escribiendo...</span>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={styles.inputContainer}>
          <input
            ref={inputRef}
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && sendMessage()}
            placeholder="Escribe tu mensaje…"
            style={styles.input}
            disabled={isLoading}
          />
          <button 
            onClick={sendMessage} 
            style={{...styles.send, opacity: (!userInput.trim() || isLoading) ? 0.5 : 1}}
            disabled={!userInput.trim() || isLoading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      <button onClick={() => setOpen(!open)} style={styles.fab} aria-label="Abrir chat">
        {open ? <X color="white" /> : <MessageSquare color="white" />}
      </button>
    </div>
  );
}

const styles = {
  container: { position: "fixed", bottom: 20, right: 20, zIndex: 1000, fontFamily: "'Inter', sans-serif" },
  fab: {
    width: 60,
    height: 60,
    borderRadius: "50%",
    background: "#d4af37",
    border: "none",
    cursor: "pointer",
    boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "transform 0.2s"
  },
  chatWindow: {
    position: "absolute",
    bottom: 80,
    right: 0,
    width: 350,
    height: 500,
    background: "#1a1a1a",
    borderRadius: 16,
    opacity: 0,
    pointerEvents: "none",
    transform: "translateY(20px) scale(0.95)",
    transition: "all .3s cubic-bezier(0.19, 1, 0.22, 1)",
    boxShadow: "0 10px 40px rgba(0,0,0,0.4)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    border: "1px solid #333"
  },
  chatWindowOpen: {
    opacity: 1,
    pointerEvents: "auto",
    transform: "translateY(0) scale(1)"
  },
  header: {
    padding: "16px",
    background: "#222",
    borderBottom: "1px solid #333",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    color: "white"
  },
  headerInfo: { display: "flex", alignItems: "center", gap: "10px" },
  avatar: { width: 40, height: 40, borderRadius: "50%", objectFit: "cover", border: "2px solid #d4af37" },
  headerTitle: { fontWeight: "600", fontSize: "16px" },
  closeBtn: { background: "none", border: "none", color: "#888", cursor: "pointer", padding: 4 },
  messages: { flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 10 },
  message: { 
    padding: "10px 14px", 
    borderRadius: 14, 
    maxWidth: "80%", 
    lineHeight: "1.4", 
    fontSize: "14px",
    animation: "messageAppear 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) forwards",
    position: 'relative',
  },
  user: { 
    background: "#d4af37", 
    color: "#000", 
    alignSelf: "flex-end", 
    borderBottomRightRadius: 2,
    paddingBottom: '22px' // Espacio para el doble check
  },
  bot: { background: "#333", color: "#fff", alignSelf: "flex-start", borderBottomLeftRadius: 2 },
  inputContainer: { display: "flex", padding: 12, borderTop: "1px solid #333", background: "#222" },
  input: { flex: 1, borderRadius: 20, padding: "10px 16px", background: "#333", border: "1px solid #444", color: "white", outline: "none" },
  send: { marginLeft: 8, background: "#d4af37", border: "none", borderRadius: "50%", width: 40, height: 40, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "#000", transition: "opacity 0.2s" },
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100vw",
    height: "100vh",
    zIndex: 2000,
  },
  popupImage: { 
    position: "absolute",
    bottom: "480px",
    right: "280px",
    width: "180px", 
    height: "180px", 
    borderRadius: "50%", 
    objectFit: "cover", 
    boxShadow: "0 15px 40px rgba(0,0,0,0.4)", 
    border: "4px solid #d4af37",
    zIndex: 2001,
    animation: "popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards",
    cursor: "pointer",
    maxWidth: "none"
  },
  receiptContainer: {
    position: 'absolute',
    bottom: '6px',
    right: '10px',
  }
};
