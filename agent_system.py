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

from llm_config import LLMConfig, LLMFactory

class AgentSystem:
    """Main agent system for processing tasks with context"""
    _history_store: Dict[str, InMemoryChatMessageHistory] = {}
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = LLMFactory.create_llm(config)
        self.vectorstore = None
        self.retriever_tool = None
        self.agent_executor = None
    
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
    
    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        tools = []
        
        # Add retriever tool if available
        if self.retriever_tool:
            tools.append(self.retriever_tool)
        
        # Add analysis tool
        analysis_tool = Tool(
            name="analyze_content",
            description="Analyze and summarize content, extract key insights, identify patterns, and provide detailed explanations",
            func=self._analyze_content
        )
        tools.append(analysis_tool)
        
        # Add reasoning tool
        reasoning_tool = Tool(
            name="step_by_step_reasoning",
            description="Break down complex problems into steps and provide detailed reasoning for each step",
            func=self._step_by_step_reasoning
        )
        tools.append(reasoning_tool)
        
        return tools
    
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
            return f"Reasoning failed: {str(e)}"
    
    def _create_agent(self, system_prompt: str = None) -> AgentExecutor:
        """Create the LangChain agent, optionally with a custom system prompt"""
        # Create tools
        tools = self._create_tools()
        # Use custom system prompt if provided
        system_message = system_prompt or "You are an intelligent assistant that helps users complete tasks using the provided context.\n\nYou have access to tools that can:\n- Search and retrieve relevant information from uploaded documents\n- Analyze content and extract insights\n- Perform step-by-step reasoning for complex problems\n\nGuidelines:\n1. Always use the context_retriever tool first to find relevant information\n2. Be thorough and accurate in your responses\n3. If you need to break down complex problems, use the step_by_step_reasoning tool\n4. Provide confidence levels for your answers when possible\n5. Cite specific parts of the context when relevant\n6. If information is not available in the context, clearly state that\n\nCurrent task context: The user has uploaded documents and wants you to answer questions or complete tasks based on that content."
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # Wrap agent with RunnableWithMessageHistory
        agent_with_history = RunnableWithMessageHistory(
            agent,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent_with_history,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
        
        return agent_executor
    
    def process_tasks(self, tasks: List[str], context: str, session_id: str = "default", system_prompt: str = None) -> List[Dict[str, Any]]:
        """Process a list of tasks with the given context and session ID, with optional system prompt"""
        self._setup_context_retrieval(context)
        # Always create a new agent for each run to allow custom system prompt
        self.agent_executor = self._create_agent(system_prompt=system_prompt)
        results = []
        for task in tasks:
            start_time = time.time()
            try:
                response = self.agent_executor.invoke({
                    "input": f"Task: {task}\n\nPlease complete this task using the available context and tools. Provide a comprehensive answer with reasoning."
                }, config={"configurable": {"session_id": session_id}})
                processing_time = time.time() - start_time
                answer = response.get('output', 'No response generated')
                confidence = self._calculate_confidence(answer, task)
                tokens_used = len(answer.split()) * 1.3
                result = {
                    'task': task,
                    'answer': answer,
                    'confidence': confidence,
                    'tokens_used': int(tokens_used),
                    'processing_time': processing_time,
                    'sources': self._extract_sources(answer),
                    'reasoning_steps': self._extract_reasoning_steps(answer)
                }
                results.append(result)
            except Exception as e:
                processing_time = time.time() - start_time
                result = {
                    'task': task,
                    'answer': f"Error processing task: {str(e)}",
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