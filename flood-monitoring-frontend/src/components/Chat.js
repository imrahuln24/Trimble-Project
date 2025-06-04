// frontend/src/components/Chat.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getToken } from '../services/authService';
import { fetchChatMessages } from '../services/chatService';
import './Chat.css';

export default function Chat({ currentUser }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const ws = useRef(null);
  const messagesEndRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false); // Track WebSocket connection status

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = useCallback(() => {
    if (!currentUser) return; // Don't load if no current user
    fetchChatMessages()
      .then(response => {
        setMessages(response.data);
      })
      .catch(error => console.error("Error fetching chat messages:", error));
  }, [currentUser]); // Depend on currentUser

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    const token = getToken();
    // Ensure currentUser and its username are available.
    if (!token || !currentUser || !currentUser.username) {
        console.log("Chat WebSocket: currentUser or token not ready. currentUser:", currentUser);
        setIsConnected(false); // Ensure disconnected state if prerequisites fail
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.close(); // Close if open but currentUser became invalid
        }
        return;
    }

    // Construct WebSocket URL with token for authentication
    // Make sure the prefix in main.py for chat router is /chat
    // and the WebSocket path is /ws. So full path is /chat/ws
    const wsUrl = `ws://127.0.0.1:8000/chat/ws?token=${encodeURIComponent(token)}`;
    console.log("Attempting to connect to Chat WebSocket:", wsUrl);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('Chat WebSocket connected');
      setIsConnected(true);
    };

    ws.current.onmessage = (event) => {
      try {
        const messageData = JSON.parse(event.data);
        if (messageData.error) {
            console.error("WebSocket message error from server:", messageData.error, messageData.details);
            return;
        }
        if (messageData.type === 'new_message' && messageData.data) {
          // Ensure the received message.data has a username field
          console.log("New chat message received:", messageData.data);
          setMessages(prevMessages => [...prevMessages, messageData.data]);
        } else {
          console.log("Received unhandled WebSocket message:", messageData);
        }
      } catch (e) {
        console.error("Error parsing WebSocket message:", e, "Data:", event.data);
      }
    };

    ws.current.onclose = (event) => {
      console.log('Chat WebSocket disconnected:', event.reason, event.code);
      setIsConnected(false);
      // Optional: implement reconnect logic here if desired for chat
    };

    ws.current.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      if (ws.current) {
        console.log("Closing Chat WebSocket on component unmount or currentUser change.");
        ws.current.close();
      }
      setIsConnected(false); // Reset connection state on cleanup
    };
  }, [currentUser]); // Re-run if currentUser changes (e.g. on login, logout)

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ content: newMessage }));
      setNewMessage('');
    } else {
        console.warn("Cannot send message. New message empty or WebSocket not open. State:", ws.current?.readyState);
    }
  };

  if (!currentUser) {
    return <div className="chat-container card shadow-sm p-3"><p>Loading user information for chat...</p></div>;
  }

  return (
    <div className="chat-container card shadow-sm">
      <div className="card-header">Live Chat ({currentUser.username}) {isConnected ? <span className="badge bg-success ms-2">Connected</span> : <span className="badge bg-danger ms-2">Disconnected</span>}</div>
      <div className="chat-messages card-body">
        {messages.map((msg, index) => (
          <div key={msg.id || `msg-${index}-${msg.timestamp}`} className={`message ${msg.username === currentUser.username ? 'sent' : 'received'}`}>
            <div className="message-bubble">
              <strong className="message-sender">{msg.username === currentUser.username ? 'You' : msg.username}:</strong>
              <p className="message-content">{msg.content}</p>
              <small className="message-timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</small>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="card-footer chat-input">
        <form onSubmit={handleSendMessage} className="d-flex">
          <input
            type="text"
            className="form-control me-2"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            disabled={!isConnected} // Disable if not connected
          />
          <button type="submit" className="btn btn-primary" disabled={!isConnected || !newMessage.trim()}>Send</button>
        </form>
      </div>
    </div>
  );
}
/*
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getToken } from '../services/authService';
import { fetchChatMessages } from '../services/chatService';
import './Chat.css'; // Create this CSS file for styling

export default function Chat({ currentUser }) { // currentUser: { username, role }
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const ws = useRef(null);
  const messagesEndRef = useRef(null); // For auto-scrolling

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = useCallback(() => {
    fetchChatMessages()
      .then(response => {
        setMessages(response.data);
      })
      .catch(error => console.error("Error fetching chat messages:", error));
  }, []);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);
  
  useEffect(scrollToBottom, [messages]);


  useEffect(() => {
    const token = getToken();
    if (!token) return;

    // Construct WebSocket URL with token for authentication
    // Ensure your WebSocket server can handle token in query param for auth
    const wsUrl = `ws://127.0.0.1:8000/ws/chat?token=${encodeURIComponent(token)}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('Chat WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      const messageData = JSON.parse(event.data);
      if (messageData.type === 'new_chat_message') {
        setMessages(prevMessages => [...prevMessages, messageData.payload]);
      }
    };

    ws.current.onclose = () => {
      console.log('Chat WebSocket disconnected');
    };

    ws.current.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []); // Reconnect if token changes, though usually it won't during a session

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ content: newMessage }));
      setNewMessage('');
    }
  };

  if (!currentUser) {
    return <p>Loading user information...</p>;
  }

  return (
    <div className="chat-container card shadow-sm">
      <div className="card-header">Live Chat</div>
      <div className="chat-messages card-body">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.username === currentUser.username ? 'sent' : 'received'}`}>
            <div className="message-bubble">
              <strong className="message-sender">{msg.username === currentUser.username ? 'You' : msg.username}:</strong>
              <p className="message-content">{msg.content}</p>
              <small className="message-timestamp">{new Date(msg.timestamp).toLocaleTimeString()}</small>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="card-footer chat-input">
        <form onSubmit={handleSendMessage} className="d-flex">
          <input
            type="text"
            className="form-control me-2"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
          />
          <button type="submit" className="btn btn-primary">Send</button>
        </form>
      </div>
    </div>
  );
}*/