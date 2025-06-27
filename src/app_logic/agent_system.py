import time
from typing import List, Dict, Any, Optional
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from src.app_logic.llm_config import LLMConfig, LLMFactory

# Define Agent Specialties
AGENT_SPECIALTIES = {
    "General Analyst": {
        "system_prompt": "You are a General Analyst. Your goal is to provide comprehensive analysis and reasoned answers based on the provided context and tools. Use the context_retriever for information, analyze_content for deeper insights, and step_by_step_reasoning for complex problems.",
        "tools": ["context_retriever", "analyze_content", "step_by_step_reasoning"]
    },
    "Documentation Expert": {
        "system_prompt": "You are a Documentation Expert. Your primary function is to accurately extract and present information from the provided documents using the context_retriever tool. Focus on precision and citing sources if possible. If information is not found, state that clearly.",
        "tools": ["context_retriever"]
    },
    "Creative Writer": {
        "system_prompt": "You are a Creative Writer. Your primary goal is to generate novel and imaginative content, brainstorm unique ideas, write stories, poetry, or rephrase text in fresh and engaging ways. You may use the 'analyze_content' tool to understand the style or themes of existing text if you need inspiration, but your main focus is on creation.",
        "tools": ["analyze_content"] # Could also be an empty list for pure LLM generation, or specific creative tools in the future.
    },
    "Python Code Assistant": {
        "system_prompt": "You are a Python Code Assistant. Your role is to help users by writing, explaining, and debugging Python code. You can use the 'execute_python_code' tool to run simple Python snippets and see their output. Always ensure code is safe before suggesting execution. For complex data analysis or file manipulation, describe what the code would do rather than attempting direct execution via this simple tool.",
        "tools": ["execute_python_code", "context_retriever"] # context_retriever might be useful for code examples in docs
    }
    # Add more specialties here in the future
}


class AgentSystem:
    """Main agent system for processing tasks with context"""
    _history_store: Dict[str, InMemoryChatMessageHistory] = {}

    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = LLMFactory.create_llm(config)
        self.vectorstore = None
        self.retriever_tool = None # This will be created in _setup_context_retrieval
        self.available_tools = {} # To store all instantiated tools
        self.agent_executor = None # This will be created per task or specialty

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._history_store:
            self._history_store[session_id] = InMemoryChatMessageHistory()
        return self._history_store[session_id]

    def _setup_context_retrieval(self, context: str):
        """Setup vector store and retrieval for context"""
        try:
            # Split context into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )

            docs = text_splitter.create_documents([context])

            # Create embeddings
            embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version or "2024-02-01",
                azure_deployment="text-embedding-ada-002"  # Standard embedding model
            )

            # Create vector store
            self.vectorstore = FAISS.from_documents(docs, embeddings)

            # Create retriever tool
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )

            self.retriever_tool = create_retriever_tool(
                retriever,
                "context_retriever",
                "Searches and returns relevant information from the uploaded context documents. Use this tool to find specific information needed to answer questions."
            )

        except Exception as e:
            print(f"Warning: Could not setup context retrieval: {str(e)}")
            # Fallback: create a simple context tool
            self.retriever_tool = Tool(
                name="context_search",
                description="Access the uploaded context content",
                func=lambda query: context[:2000]  # Return first 2000 chars as fallback
            )
        # Add the retriever tool to available_tools dictionary
        if self.retriever_tool:
            self.available_tools["context_retriever"] = self.retriever_tool

    def _initialize_available_tools(self):
        """Initializes all statically defined tools and adds them to self.available_tools."""
        # Analysis tool
        if "analyze_content" not in self.available_tools:
            analysis_tool = Tool(
                name="analyze_content",
                description="Use this tool to deeply analyze a given piece of text. It will break down the content into key themes, main points, important insights, observed patterns, and provide a summary of critical information. Useful for deconstructing and understanding text before generating new content or analysis.",
                func=self._analyze_content
            )
            self.available_tools["analyze_content"] = analysis_tool

        # Reasoning tool
        if "step_by_step_reasoning" not in self.available_tools:
            reasoning_tool = Tool(
                name="step_by_step_reasoning",
                description="Break down complex problems or questions into logical steps and provide detailed reasoning for each step. Use this for tasks requiring multi-step thinking.",
                func=self._step_by_step_reasoning
            )
            self.available_tools["step_by_step_reasoning"] = reasoning_tool

        # Python execution tool (mock)
        if "execute_python_code" not in self.available_tools:
            python_tool = Tool(
                name="execute_python_code",
                description="Executes a given snippet of Python code and returns its stdout, stderr, or an error message. Use for simple, safe, and stateless code execution. Do not use for code that has side effects like file system access or network calls. For complex tasks, describe the code instead of executing it.",
                func=self._execute_python_code_mock
            )
            self.available_tools["execute_python_code"] = python_tool

        # Add other tools here if needed

    def _execute_python_code_mock(self, code_snippet: str) -> str:
        """
        Mock Python execution tool.
        In a real scenario, this would use a sandboxed environment.
        For now, it will have very limited capabilities or just describe execution.
        """
        try:
            # VERY IMPORTANT: `exec` is dangerous. This is a MOCK.
            # A real implementation needs a secure sandbox (e.g., Docker container, restricted interpreter).
            # For this mock, we'll restrict heavily what it can even pretend to do.

            restricted_keywords = ["import os", "import subprocess", "open(", "eval(", "exec("] # exec( is self-referential for safety here
            # Allow basic math, print, list/dict operations for the mock.

            for keyword in restricted_keywords:
                if keyword in code_snippet:
                    return "Execution Error: Code contains restricted keywords. This mock tool cannot execute it for safety reasons."

            if "__" in code_snippet: # Avoid dunder methods
                 return "Execution Error: Code contains dunder methods which are restricted in this mock tool."

            # Simple "mock execution" for print statements or basic expressions
            if code_snippet.strip().startswith("print("):
                # Simulate capturing print output
                printed_value = code_snippet.strip()[len("print("):-1]
                # Try to evaluate simple expressions if they are inside print
                try:
                    # Attempt to eval if it's a very simple, safe expression (e.g. numbers, strings)
                    # This is still risky, so keep it minimal for a mock.
                    # A better mock would just parse the string.
                    if all(c in "0123456789+-*/(). '\"" for c in printed_value): # Basic check
                        res = str(eval(printed_value))
                        return f"Mock Output: {res}"
                    else:
                        return f"Mock Output: (Simulated print of) {printed_value}"
                except Exception as e_eval:
                    return f"Mock Output: (Simulated print of) {printed_value}"

            elif any(op in code_snippet for op in ['+', '-', '*', '/']):
                 # For very simple arithmetic expressions not in print
                try:
                    if all(c in "0123456789+-*/(). " for c in code_snippet): # Basic check
                        res = str(eval(code_snippet))
                        return f"Mock Result: {res}"
                    else:
                        return "Mock Execution: Code snippet is too complex for direct mock evaluation. Describes as non-executable by this simple tool."
                except Exception as e_eval_expr:
                    return f"Mock Execution Error: Could not evaluate simple expression: {str(e_eval_expr)}"

            return "Mock Execution: Code snippet received. In a real tool, this would be executed in a sandbox. For this mock, if it's not a simple print or arithmetic, no output is generated, assume it ran 'successfully' if no restricted keywords."

        except Exception as e:
            return f"Mock Execution Error: {str(e)}"

    def _get_tools_for_specialty(self, specialty_name: str) -> List[Tool]:
        """Get the actual tool objects for a given specialty."""
        specialty_config = AGENT_SPECIALTIES.get(specialty_name)
        if not specialty_config:
            # Fallback to General Analyst if specialty not found or not configured
            specialty_config = AGENT_SPECIALTIES.get("General Analyst")
            print(f"Warning: Specialty '{specialty_name}' not found. Falling back to 'General Analyst'.")

        selected_tool_names = specialty_config.get("tools", [])

        # Ensure all available tools are initialized
        if not self.available_tools: # Or check if specific tools are missing
             self._initialize_available_tools() # This ensures tools are ready
             # The retriever tool is setup separately in _setup_context_retrieval
             # so it should already be in self.available_tools if context is provided.

        selected_tools = []
        for tool_name in selected_tool_names:
            tool = self.available_tools.get(tool_name)
            if tool:
                selected_tools.append(tool)
            else:
                print(f"Warning: Tool '{tool_name}' for specialty '{specialty_name}' not found in available tools.")

        # If context_retriever is requested but not available (e.g. no context uploaded),
        # it won't be added. The agent should handle this gracefully.
        # The agent prompt should guide it.
        return selected_tools

    def _analyze_content(self, content: str) -> str:
        """Tool for content analysis"""
        analysis_prompt = f"""
        Analyze the following content and provide:
        1. Key themes and main points
        2. Important insights or findings
        3. Any patterns or trends
        4. Summary of critical information

        Content: {content}
        """

        try:
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            return response.content
        except Exception as e:
            print(f"Error in _analyze_content: {e}")
            return f"Analysis failed: {str(e)}"

    def _step_by_step_reasoning(self, problem: str) -> str:
        """Tool for step-by-step reasoning"""
        reasoning_prompt = f"""
        Break down this problem/question into logical steps and provide reasoning for each:

        Problem: {problem}

        Provide your response in this format:
        Step 1: [Description]
        Reasoning: [Your reasoning]

        Step 2: [Description]
        Reasoning: [Your reasoning]

        Continue for all necessary steps...
        """

        try:
            response = self.llm.invoke([HumanMessage(content=reasoning_prompt)])
            return response.content
        except Exception as e:
            print(f"Error in _step_by_step_reasoning: {e}")
            return f"Reasoning failed: {str(e)}"

    def _create_agent(self, specialty_name: str, custom_system_prompt: Optional[str] = None) -> AgentExecutor:
        """Create the LangChain agent based on specialty and an optional custom system prompt."""

        specialty_config = AGENT_SPECIALTIES.get(specialty_name, AGENT_SPECIALTIES["General Analyst"])

        # Determine the system prompt
        if custom_system_prompt:
            system_message_content = custom_system_prompt
        else:
            system_message_content = specialty_config["system_prompt"]

        # Get tools for the specialty
        tools = self._get_tools_for_specialty(specialty_name)

        if not tools and specialty_name != "Creative Writer": # Creative writer might have no tools by design
            print(f"Warning: No tools selected for specialty '{specialty_name}'. The agent might be limited.")

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message_content),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        try:
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
        except Exception as e:
            print(f"Error creating OpenAI functions agent: {e}")
            # Fallback or re-raise, depending on desired behavior
            raise ValueError(f"Could not create agent for specialty {specialty_name}: {e}")

        # Wrap agent with RunnableWithMessageHistory
        agent_with_history = RunnableWithMessageHistory(
            agent,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent_with_history,
            tools=tools,
            verbose=True, # Good for debugging
            handle_parsing_errors=True, # Important for robustness
            max_iterations=10,
            early_stopping_method="generate" # "generate" can sometimes be too aggressive. Consider "force" or None.
        )

        return agent_executor

    def process_tasks(self, tasks: List[str], context: str, specialty_name: str = "General Analyst", session_id: str = "default", custom_system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a list of tasks with the given context, specialty, session ID,
        and an optional custom system prompt that overrides the specialty's default.
        """
        if not context and any(tool_name in AGENT_SPECIALTIES.get(specialty_name, {}).get("tools", []) for tool_name in ["context_retriever"]):
            # If context is required by the specialty's tools but not provided,
            # we should probably warn or handle this.
            # For now, _setup_context_retrieval will create a fallback tool if context is empty.
            print("Warning: Processing tasks that may require context, but no context was provided.")

        self.available_tools = {} # Reset available tools for this run
        self._setup_context_retrieval(context) # Sets up retriever_tool and adds to available_tools
        self._initialize_available_tools()   # Sets up other static tools and adds them

        # Create the agent executor for this processing run
        try:
            self.agent_executor = self._create_agent(specialty_name, custom_system_prompt)
        except ValueError as e:
            # If agent creation fails, return error for all tasks
            results = []
            for task in tasks:
                results.append({
                    'task': task,
                    'answer': f"Error creating agent: {str(e)}",
                    'confidence': 0.0, 'tokens_used': 0, 'processing_time': 0,
                    'sources': [], 'reasoning_steps': []
                })
            return results

        results = []
        for task in tasks:
            start_time = time.time()
            try:
                response = self.agent_executor.invoke({
                    "input": f"Task: {task}\n\nPlease complete this task using the available context and tools. Provide a comprehensive answer with reasoning."
                }, config={"configurable": {"session_id": session_id}})
                processing_time = time.time() - start_time
                answer = response.get('output', 'No response generated')

                # Basic check for common error messages from LLM or tools
                if "error" in answer.lower() or "failed" in answer.lower():
                    # This could be a soft error reported by the LLM itself
                    print(f"Potential error in LLM response for task '{task}': {answer[:200]}")

                confidence = self._calculate_confidence(answer, task)
                # Crude token estimation, consider tiktoken for accuracy if needed
                tokens_used = len(str(answer).split()) * 1.3
                result = {
                    'task': task,
                    'answer': str(answer), # Ensure answer is string
                    'confidence': confidence,
                    'tokens_used': int(tokens_used),
                    'processing_time': processing_time,
                    'sources': self._extract_sources(str(answer)),
                    'reasoning_steps': self._extract_reasoning_steps(str(answer))
                }
                results.append(result)
            except Exception as e:
                processing_time = time.time() - start_time
                error_message = f"Error processing task '{task}': {type(e).__name__} - {str(e)}"
                print(error_message) # Log to console for debugging
                result = {
                    'task': task,
                    'answer': error_message,
                    'confidence': 0.0,
                    'tokens_used': 0,
                    'processing_time': processing_time,
                    'sources': [],
                    'reasoning_steps': []
                }
                results.append(result)
        return results

    def _calculate_confidence(self, answer: str, task: str) -> float:
        """Calculate confidence score for the answer (simplified heuristic)"""
        # This is a simplified confidence calculation
        # In a real implementation, you might use more sophisticated methods

        confidence = 0.5  # Base confidence

        # Increase confidence for longer, more detailed answers
        if len(answer) > 200:
            confidence += 0.2

        # Increase confidence if answer contains specific indicators
        confidence_indicators = ['specifically', 'according to', 'based on', 'evidence', 'data shows']
        for indicator in confidence_indicators:
            if indicator in answer.lower():
                confidence += 0.1

        # Decrease confidence for uncertainty indicators
        uncertainty_indicators = ['might', 'possibly', 'unclear', 'not sure', 'cannot determine']
        for indicator in uncertainty_indicators:
            if indicator in answer.lower():
                confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _extract_sources(self, answer: str) -> List[str]:
        """Extract sources mentioned in the answer"""
        # Simple extraction - look for common source patterns
        sources = []

        # Look for patterns like "according to X" or "from Y"
        import re
        patterns = [
            r'according to ([^,.!?]+)',
            r'from ([^,.!?]+)',
            r'based on ([^,.!?]+)',
            r'as mentioned in ([^,.!?]+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            sources.extend(matches)

        return list(set(sources))  # Remove duplicates

    def _extract_reasoning_steps(self, answer: str) -> List[Dict[str, str]]:
        """Extract reasoning steps from the answer"""
        steps = []

        # Look for step patterns
        import re
        step_pattern = r'Step (\d+):?\s*([^.!?]+[.!?])'
        matches = re.findall(step_pattern, answer, re.IGNORECASE | re.MULTILINE)

        for step_num, description in matches:
            steps.append({
                'step': f"Step {step_num}",
                'description': description.strip()
            })

        return steps