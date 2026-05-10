import { useState, useRef, useEffect } from 'react';
import './index.css';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      text: 'السلام عليكم ورحمة الله وبركاته. مرحباً بك في واجهة سؤال وجواب للسيرة النبوية العطرة. تفضل بسؤالك عن النبي محمد صلى الله عليه وسلم.',
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: inputValue.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Connect to the FastAPI backend global search endpoint
      const response = await fetch('http://127.0.0.1:8000/api/v1/nlp/index/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: userMessage.text,
          limit: 3
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        text: data.answer || "عذراً، لم أتمكن من العثور على إجابة وافية. يرجى إعادة صياغة السؤال.",
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error fetching answer:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        text: "حدث خطأ في الاتصال بالخادم. تأكد من تشغيل خادم FastAPI.",
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1 className="header-title">السيرة النبوية</h1>
        <p className="header-subtitle">سؤال وجواب في سيرة الرسول ﷺ</p>
      </header>

      <div className="chat-container">
        <div className="messages-area">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-bubble ${msg.type}`}>
              <div className="message-content">{msg.text}</div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message-bubble ai">
              <div className="loading-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="input-area" onSubmit={handleSendMessage}>
          <input
            type="text"
            className="input-field"
            placeholder="اكتب سؤالك هنا..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            dir="rtl"
          />
          <button type="submit" className="send-btn" disabled={isLoading || !inputValue.trim()}>
            {/* SVG Send Icon (RTL compatible) */}
            <svg viewBox="0 0 24 24" style={{ transform: 'rotate(180deg)' }}>
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
