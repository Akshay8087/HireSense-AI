"""
Skills taxonomy.

A curated, extensible list of skills/technologies grouped by domain.
This acts as the controlled vocabulary that the skill-extraction
service matches against job descriptions and resumes. It is
intentionally a plain Python data structure (not a model) so it can be
edited or extended by non-ML engineers without touching service code.
"""
from __future__ import annotations

SKILLS_TAXONOMY: dict[str, list[str]] = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
        "sql", "bash", "shell scripting", "html", "css",
    ],
    "data_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "data science", "data analysis", "data engineering",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        "bert", "transformers", "sentence transformers", "faiss", "huggingface",
        "llm", "large language models", "generative ai", "statistics",
        "predictive modeling", "feature engineering", "a/b testing",
        "data visualization", "tableau", "power bi", "looker",
    ],
    "web_frameworks": [
        "flask", "django", "fastapi", "react", "angular", "vue", "node.js",
        "express.js", "next.js", "spring boot", "asp.net", "rails",
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
        "elasticsearch", "cassandra", "dynamodb", "firebase", "neo4j",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "terraform", "ansible", "jenkins", "ci/cd", "github actions",
        "gitlab ci", "cloudformation", "serverless", "lambda", "ec2", "s3",
    ],
    "tools_general": [
        "git", "github", "jira", "confluence", "agile", "scrum", "kanban",
        "linux", "rest api", "graphql", "microservices", "unit testing",
        "selenium", "postman", "figma", "excel", "powerpoint", "salesforce",
        "sap", "quickbooks", "tally",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "time management", "stakeholder management",
        "negotiation", "public speaking", "mentoring", "conflict resolution",
        "critical thinking", "adaptability", "collaboration",
    ],
    "business_finance": [
        "financial modeling", "budgeting", "forecasting", "accounting",
        "bookkeeping", "auditing", "tax preparation", "risk management",
        "compliance", "underwriting", "portfolio management", "valuation",
        "gaap", "ifrs", "p&l management",
    ],
    "healthcare": [
        "patient care", "clinical documentation", "ehr", "emr", "hipaa",
        "medical billing", "medical coding", "icd-10", "cpt coding",
        "phlebotomy", "triage", "case management",
    ],
    "sales_marketing": [
        "lead generation", "crm", "account management", "b2b sales",
        "b2c sales", "digital marketing", "seo", "sem", "content marketing",
        "social media marketing", "email marketing", "brand management",
        "market research", "customer relationship management",
    ],
    "design": [
        "ui/ux", "user research", "wireframing", "prototyping",
        "adobe photoshop", "adobe illustrator", "sketch", "figma",
        "design systems", "typography", "graphic design",
    ],
    "engineering_construction": [
        "autocad", "solidworks", "civil engineering", "mechanical engineering",
        "electrical engineering", "project estimation", "blueprint reading",
        "osha", "structural analysis", "quality control",
    ],
    "education": [
        "curriculum development", "lesson planning", "classroom management",
        "student assessment", "iep", "differentiated instruction",
        "educational technology",
    ],
}


def flatten_taxonomy() -> set[str]:
    """Return every skill in the taxonomy as a flat lowercase set."""
    flat: set[str] = set()
    for skills in SKILLS_TAXONOMY.values():
        flat.update(s.lower() for s in skills)
    return flat


ALL_SKILLS: set[str] = flatten_taxonomy()
