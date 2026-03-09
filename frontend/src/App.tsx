import React, { useState, useEffect } from 'react';
import { Briefcase, Code, Terminal, Server, Zap } from 'lucide-react';
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
    const [isConnected, setIsConnected] = useState(false);
    const [activeCommand, setActiveCommand] = useState<string>("mcp call-tool query_skill --skill=MCP");
    const [terminalOutput, setTerminalOutput] = useState<string>(
        "[\n  {\n    \"name\": \"MCP Portfolio\",\n    \"description\": \"An interactive portfolio powered by the Model Context Protocol\",\n    \"technologies\": [\"Python\", \"TypeScript\", \"React\", \"MCP\"]\n  }\n]"
    );

    useEffect(() => {
        const connectToMCP = async () => {
            try {
                const transport = new SSEClientTransport(new URL("http://localhost:8000/sse"));
                const client = new Client(
                    { name: "portfolio-frontend", version: "1.0.0" },
                    { capabilities: {} }
                );

                await client.connect(transport);
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

                {/* Interactive Terminal Demo Panel */}
                <section className="glass-panel terminal-panel">
                    <div className="panel-header" style={{ borderBottom: 'none', padding: 0 }}>
                        <div className="terminal-header" style={{ width: '100%', display: 'flex', alignItems: 'center' }}>
                            <div className="term-dot red"></div>
                            <div className="term-dot yellow"></div>
                            <div className="term-dot green"></div>
                            <span style={{ marginLeft: '1rem', color: '#888', fontSize: '0.85rem' }}>AI Agent Simulation</span>
                        </div>
                    </div>
                    <div className="terminal-text">
                        <div className="terminal-command">
                            <Terminal size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} />
                            <span style={{ color: '#fff' }}>$ {activeCommand}</span>
                        </div>
                        <div className="terminal-output">
                            {terminalOutput}
                        </div>
                    </div>
                </section>

            </main>
        </div>
    );
}

export default App;
