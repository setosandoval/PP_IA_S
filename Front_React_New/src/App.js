import React, { useState, useRef, useEffect } from "react";
import TextField from "@mui/material/TextField";
import "./App.css";

function App() {
  const [studentNumber, setStudentNumber] = useState("");
  const [password, setPassword] = useState("");
  const [connected, setConnected] = useState(false);

  const [responseStudent, setResponseStudent] = useState("");
  const [chatHistory, setChatHistory] = useState([[]]);
  const [currentChatHistory, setCurrentChatHistory] = useState({
    conversation: [],
    conversationIndex: -1,
  });

  const chatHistoryRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Opcional: HTML para un .tex completo
  const [latexHTML, setLatexHTML] = useState("");

  const handleError = (msg) => setError(msg);
  const handleClose = () => setError(null);

  function ErrorModal({ error, onClose }) {
    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={onClose}>
            &times;
          </span>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("/authConf.json");
      const authData = await res.json();
      const userExists = authData.users.some(
        (u) => u.studentNumber === studentNumber && u.password === password
      );
      if (userExists) {
        setConnected(true);
      } else {
        console.log("Usuario/contraseña incorrectos.");
      }
    } catch (err) {
      console.error("Error authConf.json:", err);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const res = await fetch("History.json");
      const data = await res.json();
      if (data[0].length === 0) {
        setChatHistory([]);
        setCurrentChatHistory({ conversationIndex: 0, conversation: [] });
      } else {
        setChatHistory(data);
        setCurrentChatHistory({
          conversationIndex: data.length - 1,
          conversation: data[data.length - 1],
        });
      }
    } catch (err) {
      console.error("Error fetching chat:", err);
    }
  };

  const inputHandler = (e) => {
    setResponseStudent(e.target.value);
  };

  const handleSubmit = () => {
    setLoading(true);
    const jsonData = {
      responseStudent,
      history: currentChatHistory.conversation,
    };

    fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jsonData),
    })
      .then((r) => r.json())
      .then((data) => {
        setLoading(false);
        if (data.message.responseChatbot === "reinit") {
          fetchChatHistory();
        } else {
          // Actualizar currentChatHistory
          setCurrentChatHistory((prev) => ({
            conversation: [
              ...(prev.conversation || []),
              {
                id: data.message.id,
                responseStudent,
                responseChatbot: data.message.responseChatbot,
              },
            ],
            conversationIndex: prev.conversationIndex,
          }));

          // Actualizar chatHistory global
          if (!currentChatHistory.conversation || currentChatHistory.conversation.length === 0) {
            setChatHistory([
              ...chatHistory,
              [
                {
                  id: data.message.id,
                  responseStudent,
                  responseChatbot: data.message.responseChatbot,
                },
              ],
            ]);
          } else {
            const updated = chatHistory.map((conv, idx) => {
              if (idx === currentChatHistory.conversationIndex) {
                return [
                  ...currentChatHistory.conversation,
                  {
                    id: data.message.id,
                    responseStudent,
                    responseChatbot: data.message.responseChatbot,
                  },
                ];
              }
              return conv;
            });
            setChatHistory(updated);
          }
          setResponseStudent("");
        }
      })
      .catch((err) => {
        console.error("Error query backend:", err);
        handleError("Ocurrió un error: revise su pregunta.");
        setLoading(false);
      });
  };

  const isImageUrl = (url) => {
    return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(url);
  };

  // Efectos
  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory]);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  // Carga opcional del .tex -> .html si usas /api/convert_latex
  useEffect(() => {
    fetch("/api/convert_latex")
      .then((r) => r.json())
      .then((data) => {
        setLatexHTML(data.html);
        // Forzar re-render de MathJax si lo usas
        if (window.MathJax && window.MathJax.typeset) {
          window.MathJax.typeset();
        }
      })
      .catch((err) => console.error("Error fetch /api/convert_latex:", err));
  }, []);

  // Re-ejecutar MathJax en cada actualización de chat
  useEffect(() => {
    if (window.MathJax && window.MathJax.typeset) {
      window.MathJax.typeset();
    }
  }, [currentChatHistory]);

  if (!connected) {
    return (
      <div className="container-form">
        <form id="msform">
          <fieldset>
            <h2>Por favor, autentíquese</h2>
            <p>
              <input
                type="text"
                value={studentNumber}
                onChange={(e) => setStudentNumber(e.target.value)}
                placeholder="Número estudiante"
              />
            </p>
            <p>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Contraseña"
              />
            </p>
            <button className="saveHistory-button" onClick={handleLogin}>
              Entrar
            </button>
          </fieldset>
        </form>
      </div>
    );
  }

  return (
    <div className="main">
      <h1>Robot PP</h1>
      <div className="border d-table w-100"></div>

      {/* Ejemplo: mostramos el HTML de Preguntas.tex convertido */}
      <div className="latex-container">
        <h2>Universidad de Los Andes</h2>
      </div>

      <div className="container">
        <div className="history-panel right">
          <div className="history-scroll" ref={chatHistoryRef}>
            <ul>
              {currentChatHistory.conversation.map((item, idx) => (
                <li className="messages" key={idx}>
                  {item.responseStudent && (
                    <p className="whatsapp-bubble send">{item.responseStudent}</p>
                  )}
                  {item.responseChatbot && (
                    isImageUrl(item.responseChatbot) ? (
                      <img
                        src={item.responseChatbot}
                        alt="Chatbot"
                        className="chatbot-image"
                      />
                    ) : (
                      <p
                        className="whatsapp-bubble received"
                        dangerouslySetInnerHTML={{ __html: item.responseChatbot }}
                      />
                    )
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="search">
        <TextField
          id="outlined-basic"
          value={responseStudent}
          onChange={inputHandler}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              handleSubmit();
            }
          }}
          variant="outlined"
          fullWidth
          label="Respuesta"
        />
        <button className="search-button" onClick={handleSubmit} disabled={loading}>
          {loading ? <div className="loading-spinner"></div> : "Enviar"}
        </button>
        {error && <ErrorModal error={error} onClose={handleClose} />}
      </div>
    </div>
  );
}

export default App;
