EXPERIENCE = [
    {
        "role": "Senior AI Engineer",
        "company": "Tech Innovators Inc.",
        "duration": "2023 - Present",
        "description": "Architected and implemented enterprise-scale LLM integrations. Designed secure, multi-tenant agent ic architectures."
    },
    {
        "role": "Software Developer",
        "company": "Data Driven Solutions",
        "duration": "2020 - 2023",
        "description": "Developed high-throughput data processing pipelines. Migrated legacy monolith systems to cost-effective microservices."
    }
]

SKILLS = [
    "Python", "TypeScript", "Go",
    "FastAPI", "Express", "React",
    "PostgreSQL", "Redis", "MongoDB",
    "Docker", "Kubernetes", "AWS",
    "LLM Integration", "RAG Systems", "Prompt Engineering"
]

PROJECTS = [
    {
        "name": "MCP Portfolio",
        "description": "An interactive portfolio powered by the Model Context Protocol, allowing AI assistants to query professional experience.",
        "technologies": ["Python", "TypeScript", "React", "MCP"],
        "link": "https://github.com/myusername/mcp-portfolio"
    },
    {
        "name": "AutoData Pipeline",
        "description": "A self-healing automated data ingestion service handling terabytes of analytics events daily.",
        "technologies": ["Go", "Kafka", "PostgreSQL"],
        "link": "Company Confidential"
    }
]

def get_projects_by_skill(skill: str) -> list:
    """Return projects that utilize a specific skill/technology (case-insensitive)."""
    search_term = skill.lower()
    return [p for p in PROJECTS if search_term in [tech.lower() for tech in p['technologies']]]

def get_contact_info() -> dict:
    """Returns protected contact information."""
    return {
        "email": "contact@example.com",
        "github": "https://github.com/myusername",
        "linkedin": "https://linkedin.com/in/myusername"
    }
