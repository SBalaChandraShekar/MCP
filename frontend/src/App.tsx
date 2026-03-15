import React, { useState, useEffect } from 'react';
import { Briefcase, Code, Server, Zap } from 'lucide-react';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import './App.css';

interface Experience {
    role: string;
    company: string;
    duration: string;
    description: string;
}

function App() {
    const [experience, setExperience] = useState<Experience[]>([]);
    const [skills, setSkills] = useState<string[]>([]);
    const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string }[]>([]);
    const [userInput, setUserInput] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const connectToMCP = async () => {
            try {
                const rawBackendUrl = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
                const backendUrl = rawBackendUrl.replace(/\/+$/, "");
                
                console.log("Attempting to connect to MCP at:", `${backendUrl}/sse`);
                const transport = new SSEClientTransport(new URL(`${backendUrl}/sse`));
                const client = new Client(
                    { name: "portfolio-frontend", version: "1.0.0" },
                    { capabilities: {} }
                );

                await client.connect(transport);
                console.log("Connected to MCP via SSE");
                setIsConnected(true);

                // Fetch Experience
                try {
                    const expResource = await client.readResource({ uri: "resume://experience" });
                    if (expResource.contents && expResource.contents.length > 0) {
                        const textContent = expResource.contents[0] as { text: string };
                        setExperience(JSON.parse(textContent.text));
                    }
                } catch (err: any) {
                    console.error("Error fetching experience resource:", err.message);
                }

                // Fetch Skills
                try {
                    const skillsResource = await client.readResource({ uri: "resume://skills" });
                    if (skillsResource.contents && skillsResource.contents.length > 0) {
                        const textContent = skillsResource.contents[0] as { text: string };
                        setSkills(JSON.parse(textContent.text));
                    }
                } catch (err: any) {
                    console.error("Error fetching skills resource:", err.message);
                }

            } catch (error) {
                console.error("Failed to connect to MCP server:", error);
            }
        };

        connectToMCP();
    }, []);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!userInput.trim() || isTyping) return;

        const userMsg = userInput.trim();
        setUserInput("");
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsTyping(true);

        try {
            const rawBackendUrl = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
            const backendUrl = rawBackendUrl.replace(/\/+$/, "");
            
            console.log("Sending chat message to:", `${backendUrl}/api/chat`);
            const response = await fetch(`${backendUrl}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMsg })
            });
            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I lost my connection to the backend. Please check if the server is running." }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="app-container">
            <header>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
                    <Server size={48} />
                    <Zap size={48} style={{ marginLeft: '-15px', color: 'var(--accent-secondary)' }} />
                </div>
                <h1 className="title">MCP Identity Server</h1>
                <p className="subtitle">
                    My professional portfolio, exposed as an AI-native interface through the Model Context Protocol.
                </p>
            </header>

            <main className="dashboard-grid">
                {/* Experience Resource Panel */}
                <section className="glass-panel">
                    <div className="panel-header">
                        <Briefcase className="panel-icon" />
                        <h2 className="panel-title">Resource: resume://experience</h2>
                    </div>
                    <div className="panel-content">
                        {!isConnected && <div style={{ padding: '1rem', color: '#888' }}>Connecting to MCP Backend...</div>}
                        {experience.map((exp, i) => (
                            <div key={i} className="data-item">
                                <div className="item-header">
                                    <div>
                                        <div className="item-role">{exp.role}</div>
                                        <div className="item-company">{exp.company}</div>
                                    </div>
                                    <span className="item-duration">{exp.duration}</span>
                                </div>
                                <p className="item-desc">{exp.description}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Skills Resource Panel */}
                <section className="glass-panel">
                    <div className="panel-header">
                        <Code className="panel-icon" />
                        <h2 className="panel-title">Resource: resume://skills</h2>
                    </div>
                    <div className="panel-content">
                        <div className="skills-container">
                            {!isConnected && <div style={{ padding: '1rem', color: '#888' }}>Connecting to MCP Backend...</div>}
                            {skills.map((skill, i) => (
                                <span key={i} className="skill-tag">
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Interactive AI Chat Panel */}
                <section className="glass-panel terminal-panel">
                    <div className="panel-header" style={{ borderBottom: 'none', padding: 15 }}>
                        <div className="terminal-header" style={{ width: '100%', display: 'flex', alignItems: 'center' }}>
                            <div className="term-dot red"></div>
                            <div className="term-dot yellow"></div>
                            <div className="term-dot green"></div>
                            <span style={{ marginLeft: '1rem', color: '#888', fontSize: '0.85rem' }}>AI Career Consultant</span>
                        </div>
                    </div>
                    <div className="chat-container">
                        <div className="chat-messages">
                            <div className="message assistant">
                                <div className="message-bubble">
                                    Hello! I'm your AI career consultant. I have real-time access to my developer's resume via the Model Context Protocol. What would you like to know?
                                </div>
                            </div>
                            {messages.map((msg, i) => (
                                <div key={i} className={`message ${msg.role}`}>
                                    <div className="message-bubble">{msg.content}</div>
                                </div>
                            ))}
                            {isTyping && (
                                <div className="message assistant">
                                    <div className="message-bubble typing">Thinking...</div>
                                </div>
                            )}
                        </div>
                        <form onSubmit={handleSendMessage} className="chat-input-area">
                            <input
                                type="text"
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                placeholder="Ask about my AI projects, fullstack experience..."
                                className="chat-input"
                            />
                            <button type="submit" className="send-button" disabled={isTyping}>
                                <Zap size={18} />
                            </button>
                        </form>
                    </div>
                </section>

            </main>
        </div>
    );
}

export default App;
