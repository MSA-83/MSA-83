"""Conversation templates service."""

import uuid
from datetime import UTC, datetime

from backend.models.conversation_template import ConversationTemplate
from backend.models.database import get_db

SYSTEM_TEMPLATES = [
    {
        "title": "Code Review",
        "description": "Get a thorough code review with best practices and improvement suggestions",
        "category": "development",
        "icon": "🔍",
        "system_prompt": "You are an expert code reviewer. Review the provided code for bugs, security issues, performance problems, and best practices. Provide specific, actionable feedback with code examples.",
        "starter_message": "Here's my code for review. Please analyze it thoroughly and provide constructive feedback.",
        "suggested_model": "llama-3.1-70b-versatile",
        "temperature": 0.3,
        "use_rag": False,
    },
    {
        "title": "Research Assistant",
        "description": "Deep research on any topic with citations and structured analysis",
        "category": "research",
        "icon": "🔬",
        "system_prompt": "You are a thorough research assistant. Provide well-structured analysis with evidence, multiple perspectives, and clear conclusions. Cite sources where possible.",
        "starter_message": "I'd like to research a topic. Help me explore it systematically.",
        "suggested_model": "llama-3.1-70b-versatile",
        "temperature": 0.5,
        "use_rag": True,
    },
    {
        "title": "Security Audit",
        "description": "Identify vulnerabilities and security weaknesses in code or systems",
        "category": "security",
        "icon": "🛡️",
        "system_prompt": "You are a security expert specializing in application security audits. Identify vulnerabilities, rate their severity, and provide remediation steps.",
        "starter_message": "Please perform a security audit on the following code/system.",
        "suggested_model": "llama-3.1-70b-versatile",
        "temperature": 0.2,
        "use_rag": True,
    },
    {
        "title": "Creative Writing",
        "description": "Brainstorm stories, poems, or creative content with AI collaboration",
        "category": "creative",
        "icon": "✍️",
        "system_prompt": "You are a creative writing partner. Help brainstorm ideas, develop characters, plot stories, and refine prose. Be imaginative and supportive.",
        "starter_message": "I'd like to work on a creative writing project. Let's brainstorm some ideas.",
        "suggested_model": "llama-3.1-8b-instant",
        "temperature": 0.9,
        "use_rag": False,
    },
    {
        "title": "Data Analysis",
        "description": "Analyze datasets, create visualizations, and extract insights",
        "category": "development",
        "icon": "📊",
        "system_prompt": "You are a data analysis expert. Help interpret data, suggest analysis approaches, write code for processing, and explain statistical results.",
        "starter_message": "I have some data I'd like to analyze. Here's what I'm working with:",
        "suggested_model": "llama-3.1-70b-versatile",
        "temperature": 0.3,
        "use_rag": False,
    },
    {
        "title": "Technical Documentation",
        "description": "Write clear, professional technical docs, READMEs, and API docs",
        "category": "development",
        "icon": "📝",
        "system_prompt": "You are a technical writing expert. Create clear, well-structured documentation that is easy to understand. Use appropriate formatting, examples, and diagrams.",
        "starter_message": "I need help writing technical documentation for:",
        "suggested_model": "llama-3.1-8b-instant",
        "temperature": 0.4,
        "use_rag": False,
    },
]


class TemplateService:
    """Service for managing conversation templates."""

    def ensure_system_templates(self) -> int:
        """Create system templates if they don't exist."""
        db = next(get_db())
        try:
            existing = db.query(ConversationTemplate).filter(ConversationTemplate.is_system == True).all()
            existing_titles = {t.title for t in existing}

            created = 0
            for tmpl in SYSTEM_TEMPLATES:
                if tmpl["title"] not in existing_titles:
                    template = ConversationTemplate(
                        id=str(uuid.uuid4()),
                        is_system=True,
                        created_at=datetime.now(UTC),
                        **tmpl,
                    )
                    db.add(template)
                    created += 1

            if created > 0:
                db.commit()
            return created
        finally:
            db.close()

    def get_all_templates(self, category: str | None = None) -> list[dict]:
        """Get all available templates, optionally filtered by category."""
        db = next(get_db())
        try:
            query = db.query(ConversationTemplate).order_by(
                ConversationTemplate.is_system.desc(),
                ConversationTemplate.usage_count.desc(),
            )
            if category:
                query = query.filter(ConversationTemplate.category == category)

            templates = query.all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "category": t.category,
                    "icon": t.icon,
                    "system_prompt": t.system_prompt,
                    "starter_message": t.starter_message,
                    "suggested_model": t.suggested_model,
                    "temperature": t.temperature,
                    "max_tokens": t.max_tokens,
                    "use_rag": t.use_rag,
                    "usage_count": t.usage_count,
                    "is_system": t.is_system,
                    "created_by": t.created_by,
                }
                for t in templates
            ]
        finally:
            db.close()

    def get_template(self, template_id: str) -> dict | None:
        """Get a single template by ID."""
        db = next(get_db())
        try:
            template = db.query(ConversationTemplate).filter(
                ConversationTemplate.id == template_id
            ).first()
            if not template:
                return None
            return {
                "id": template.id,
                "title": template.title,
                "description": template.description,
                "category": template.category,
                "icon": template.icon,
                "system_prompt": template.system_prompt,
                "starter_message": template.starter_message,
                "suggested_model": template.suggested_model,
                "temperature": template.temperature,
                "max_tokens": template.max_tokens,
                "use_rag": template.use_rag,
                "usage_count": template.usage_count,
                "is_system": template.is_system,
            }
        finally:
            db.close()

    def increment_usage(self, template_id: str) -> None:
        """Increment the usage count for a template."""
        db = next(get_db())
        try:
            db.query(ConversationTemplate).filter(
                ConversationTemplate.id == template_id
            ).update({"usage_count": ConversationTemplate.usage_count + 1})
            db.commit()
        finally:
            db.close()

    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a user-created template."""
        db = next(get_db())
        try:
            template = db.query(ConversationTemplate).filter(
                ConversationTemplate.id == template_id,
                ConversationTemplate.is_system == False,
                ConversationTemplate.created_by == user_id,
            ).first()
            if not template:
                return False
            db.delete(template)
            db.commit()
            return True
        finally:
            db.close()

    def get_categories(self) -> list[str]:
        """Get all template categories."""
        db = next(get_db())
        try:
            categories = db.query(ConversationTemplate.category).distinct().all()
            return [c[0] for c in categories]
        finally:
            db.close()


template_service = TemplateService()
