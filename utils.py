import re
from typing import List, Dict, Any
import streamlit as st
from difflib import SequenceMatcher
import hashlib
import os
from dotenv import dotenv_values, set_key
import json

def validate_markdown_file(uploaded_file) -> bool:
    """Validate that the uploaded file is a proper markdown file"""
    try:
        # Check file extension
        if not uploaded_file.name.lower().endswith('.md'):
            return False
        
        # Check file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error(f"File {uploaded_file.name} is too large (max 10MB)")
            return False
        
        # Try to read the file
        content = uploaded_file.read().decode('utf-8')
        uploaded_file.seek(0)  # Reset file pointer
        
        # Basic markdown validation - check for common markdown patterns
        markdown_patterns = [
            r'^#+ .+',  # Headers
            r'\*\*.+\*\*',  # Bold text
            r'\*.+\*',  # Italic text
            r'\[.+\]\(.+\)',  # Links
            r'^- .+',  # Unordered lists
            r'^\d+\. .+',  # Ordered lists
        ]
        
        # If it's a valid text file, accept it even if it doesn't have markdown patterns
        return True
        
    except Exception as e:
        st.error(f"Error validating file {uploaded_file.name}: {str(e)}")
        return False

def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def batch_similar_tasks(tasks: List[str], similarity_threshold: float = 0.6) -> List[List[str]]:
    """Group similar tasks together for batch processing"""
    if len(tasks) <= 1:
        return [[task] for task in tasks]
    
    batches = []
    used_indices = set()
    
    for i, task in enumerate(tasks):
        if i in used_indices:
            continue
        
        # Start a new batch with this task
        current_batch = [task]
        used_indices.add(i)
        
        # Find similar tasks
        for j, other_task in enumerate(tasks):
            if j in used_indices:
                continue
            
            if similarity(task, other_task) >= similarity_threshold:
                current_batch.append(other_task)
                used_indices.add(j)
        
        batches.append(current_batch)
    
    return batches

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text"""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'out', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'what', 'where', 'when', 'why', 'how',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'only', 'own', 'same', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'may', 'also', 'back', 'them', 'well', 'way'
    }
    
    keywords = [word for word in words if word not in stop_words]
    
    # Return unique keywords
    return list(set(keywords))

def categorize_task_type(task: str) -> str:
    """Categorize the type of task for better processing"""
    task_lower = task.lower()
    
    # Question patterns
    question_words = ['what', 'where', 'when', 'who', 'why', 'how', 'which']
    if any(word in task_lower for word in question_words) or task.strip().endswith('?'):
        return 'question'
    
    # Analysis patterns
    analysis_words = ['analyze', 'examine', 'evaluate', 'assess', 'review', 'compare']
    if any(word in task_lower for word in analysis_words):
        return 'analysis'
    
    # Summary patterns
    summary_words = ['summarize', 'summary', 'overview', 'brief', 'outline']
    if any(word in task_lower for word in summary_words):
        return 'summary'
    
    # Extraction patterns
    extract_words = ['extract', 'find', 'identify', 'locate', 'list', 'enumerate']
    if any(word in task_lower for word in extract_words):
        return 'extraction'
    
    # Creation patterns
    create_words = ['create', 'generate', 'develop', 'design', 'build', 'make']
    if any(word in task_lower for word in create_words):
        return 'creation'
    
    return 'general'

def estimate_task_complexity(task: str) -> str:
    """Estimate the complexity of a task"""
    task_length = len(task.split())
    
    # Simple heuristic based on length and keywords
    if task_length < 5:
        return 'simple'
    elif task_length < 15:
        complexity_indicators = ['analyze', 'compare', 'evaluate', 'complex', 'detailed', 'comprehensive']
        if any(word in task.lower() for word in complexity_indicators):
            return 'complex'
        return 'medium'
    else:
        return 'complex'

def format_task_results_for_export(results: List[Dict[str, Any]]) -> str:
    """Format task results for export (markdown format)"""
    export_content = "# Task Processing Results\n\n"
    export_content += f"Generated on: {st.session_state.get('export_timestamp', 'Unknown')}\n\n"
    
    for i, result in enumerate(results, 1):
        export_content += f"## Task {i}\n\n"
        export_content += f"**Question/Task:** {result['task']}\n\n"
        export_content += f"**Answer:**\n{result['answer']}\n\n"
        export_content += f"**Confidence:** {result.get('confidence', 0):.1%}\n\n"
        export_content += f"**Processing Time:** {result.get('processing_time', 0):.2f} seconds\n\n"
        
        if result.get('sources'):
            export_content += f"**Sources:**\n"
            for source in result['sources']:
                export_content += f"- {source}\n"
            export_content += "\n"
        
        if result.get('reasoning_steps'):
            export_content += f"**Reasoning Steps:**\n"
            for step in result['reasoning_steps']:
                export_content += f"- **{step['step']}:** {step['description']}\n"
            export_content += "\n"
        
        export_content += "---\n\n"
    
    return export_content

def generate_task_hash(task: str) -> str:
    """Generate a unique hash for a task to avoid duplication"""
    return hashlib.md5(task.encode()).hexdigest()[:8]

def optimize_context_for_task(context: str, task: str, max_length: int = 4000) -> str:
    """Optimize context by extracting relevant parts for a specific task"""
    if len(context) <= max_length:
        return context
    
    # Extract keywords from the task
    task_keywords = extract_keywords(task)
    
    # Split context into paragraphs
    paragraphs = context.split('\n\n')
    
    # Score paragraphs based on keyword relevance
    scored_paragraphs = []
    for paragraph in paragraphs:
        if len(paragraph.strip()) < 50:  # Skip very short paragraphs
            continue
        
        score = 0
        paragraph_lower = paragraph.lower()
        
        # Score based on keyword matches
        for keyword in task_keywords:
            if keyword in paragraph_lower:
                score += 1
        
        # Boost score for paragraphs with headers
        if paragraph.strip().startswith('#'):
            score += 2
        
        scored_paragraphs.append((score, paragraph))
    
    # Sort by score and select top paragraphs
    scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
    
    optimized_context = ""
    current_length = 0
    
    for score, paragraph in scored_paragraphs:
        if current_length + len(paragraph) > max_length:
            break
        optimized_context += paragraph + "\n\n"
        current_length += len(paragraph)
    
    return optimized_context if optimized_context else context[:max_length]

def validate_azure_config(api_key: str, endpoint: str, deployment_name: str) -> tuple[bool, str]:
    """Validate Azure OpenAI configuration"""
    if not api_key:
        return False, "API key is required"
    
    if not endpoint:
        return False, "Endpoint is required"
    
    if not deployment_name:
        return False, "Deployment name is required"
    
    # Basic URL validation for endpoint
    if not (endpoint.startswith('https://') and '.openai.azure.com' in endpoint):
        return False, "Endpoint should be a valid Azure OpenAI endpoint URL"
    
    if len(api_key) < 10:
        return False, "API key appears to be too short"
    
    return True, "Configuration is valid"

def clean_markdown_content(content: str) -> str:
    """Clean and normalize markdown content"""
    # Remove excessive whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Normalize headers
    content = re.sub(r'^#{7,}', '######', content, flags=re.MULTILINE)
    
    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    
    # Clean up code blocks
    content = re.sub(r'```(\w+)?\n\n+', r'```\1\n', content)
    
    return content.strip()

def get_file_info(uploaded_file) -> Dict[str, Any]:
    """Get information about uploaded file"""
    return {
        'name': uploaded_file.name,
        'size': uploaded_file.size,
        'type': uploaded_file.type,
        'size_mb': round(uploaded_file.size / (1024 * 1024), 2)
    }

def load_llm_config_from_json(json_path: str = "llm_config.json") -> Dict[str, str]:
    """Load LLM config from a JSON file in the project root. Returns a dict of config values."""
    if not os.path.isfile(json_path):
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_llm_config_to_json(config: Dict[str, str], json_path: str = "llm_config.json") -> None:
    """Save LLM config to a JSON file in the project root. Overwrites all keys."""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

# Deprecated: use JSON-based config instead
# def load_llm_config_from_env(env_path: str = ".env") -> Dict[str, str]: ...
# def save_llm_config_to_env(config: Dict[str, str], env_path: str = ".env") -> None: ...

def format_single_task_result_for_export(result: Dict[str, Any]) -> str:
    """Format a single task result for export (markdown format)"""
    export_content = f"# Task Report\n\n"
    export_content += f"**Question/Task:** {result['task']}\n\n"
    export_content += f"**Answer:**\n{result['answer']}\n\n"
    export_content += f"**Confidence:** {result.get('confidence', 0):.1%}\n\n"
    export_content += f"**Processing Time:** {result.get('processing_time', 0):.2f} seconds\n\n"
    if result.get('sources'):
        export_content += f"**Sources:**\n"
        for source in result['sources']:
            export_content += f"- {source}\n"
        export_content += "\n"
    if result.get('reasoning_steps'):
        export_content += f"**Reasoning Steps:**\n"
        for step in result['reasoning_steps']:
            export_content += f"- **{step['step']}:** {step['description']}\n"
        export_content += "\n"
    export_content += "---\n\n"
    return export_content