from typing import Annotated, Optional, Type
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os
import getpass
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_community import GoogleSearchAPIWrapper
import json
from langchain_core.messages import ToolMessage
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Try to import python-dotenv, install if not available
try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

class GoogleSearchInput(BaseModel):
    query: str = Field(description="The search query to Google")

class GoogleSearchTool(BaseTool):
    name: str = "google_search"
    description: str = "Search Google for current information. Use this when you need to find recent or real-time information."
    args_schema: Type[BaseModel] = GoogleSearchInput
    search_wrapper: GoogleSearchAPIWrapper = Field(default_factory=GoogleSearchAPIWrapper)
    summarizer_llm: ChatGoogleGenerativeAI = Field(
        default_factory=lambda: ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.2,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    )

    def _run(self, query: str) -> str:
        try: 
            # Get raw search results
            raw_results = self.search_wrapper.run(query)
            
            # Summarize the results to remove redundancy and verbosity
            summary_prompt = f"""Please summarize the following Google search results for the query "{query}". 
            Remove redundant information, irrelevant details, and repetitive content. 
            Provide a clear, concise answer that directly addresses the user's question and doesn't include any other information.
            
            Search Results:
            {raw_results}
            
            Summary:"""
            
            summary_message = HumanMessage(content=summary_prompt) 
            summary_response = self.summarizer_llm.invoke([summary_message])
            
            return summary_response.content
            
        except Exception as e:
            return f"Error searching Google: {str(e)}"

    def _arun(self, query: str) -> str:
        return self._run(query)

def create_chatbot_with_memory():
    """Create a chatbot with memory using LangGraph and Google GenAI"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up Google API key
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")
    
    # Set up Google CSE ID
    if "GOOGLE_CSE_ID" not in os.environ:
        os.environ["GOOGLE_CSE_ID"] = getpass.getpass("Enter your Google CSE ID: ")
 
    # Add LangSmith tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if "LANGCHAIN_API_KEY" not in os.environ:
        os.environ["LANGCHAIN_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")
    # Set project name
    if "LANGCHAIN_PROJECT" not in os.environ:
        os.environ["LANGCHAIN_PROJECT"] = "Chatbot with Tools"

    # Set up Google Search as a tool
    google_search_tool = GoogleSearchTool()
    tools = [google_search_tool]

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.2,  # Slightly higher for more conversational responses
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    # Bind tools to the LLM
    llm = llm.bind_tools(tools)
    
    def chatbot(state: State):
        """Chatbot agent that maintains conversation memory"""
        # Get all messages in the conversation
        messages = state["messages"]
        
        # Create system message for context
        system_message = SystemMessage(content="""You are a helpful AI assistant. You have memory of the entire conversation history. 
        Use this context to provide more relevant and personalized responses. 
        Be conversational and engaging while maintaining helpfulness.""")

        # Combine system message with conversation history
        full_messages = [system_message] + messages
        
        # Get response from LLM
        response = llm.invoke(full_messages)
        
        # Return the response (it will be added to the conversation history)
        return {"messages": [response]}

    # Build the graph
    graph_builder = StateGraph(State)
    
    # Add the chatbot node
    graph_builder.add_node("chatbot", chatbot)
    
    # Add the tool node
    tool_node = BasicToolNode(tools=[google_search_tool])
    graph_builder.add_node("tools", tool_node)

    # Add tool edge
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        {"tools": "tools", END: END},
    )
    
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    
    # Set the entry point
    graph_builder.add_edge(START, "chatbot")
    
    # Add edges
    graph_builder.add_edge("chatbot", END)
    
    # Compile the graph
    graph = graph_builder.compile()
    
    return graph


def run_interactive_chatbot():
    """Run the chatbot in interactive mode with memory"""
    print("🤖 AI Assistant with Memory")
    print("=" * 40)
    print("I remember our entire conversation!")
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("Type 'clear' to clear conversation memory")
    print("Type 'history' to see conversation history")
    print()
    
    # Create the chatbot
    chatbot = create_chatbot_with_memory()
    
    # Initialize conversation state
    conversation_state = {"messages": []}
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! It was nice chatting with you! 👋")
                break
            
            if user_input.lower() == 'clear':
                conversation_state = {"messages": []}
                print("Conversation memory cleared! 🧹")
                continue
            
            if user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                print("-" * 30)
                for i, msg in enumerate(conversation_state["messages"], 1):
                    role = "You" if isinstance(msg, HumanMessage) else "Assistant"
                    content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    print(f"{i}. {role}: {content}")
                print("-" * 30)
                continue
            
            if not user_input:
                continue
            
            # Create human message
            human_message = HumanMessage(content=user_input)
            
            # Add user message to conversation state
            conversation_state["messages"].append(human_message)
            
            print("Assistant:", end=" ", flush=True)
            for event in chatbot.stream(conversation_state):
                for value in event.values():
                    ai_message = value["messages"][-1]
                    print(ai_message.content, end="", flush=True)
                    # Add AI response to conversation state
                    conversation_state["messages"].append(ai_message)
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")


def run_single_response(text: str):
    """Run a single response (for testing)"""
    chatbot = create_chatbot_with_memory()
    human_message = HumanMessage(content=text)
    result = chatbot.invoke({"messages": [human_message]})
    ai_message = result["messages"][-1]
    return ai_message.content


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # If text is provided as command line argument, do single response
        text = " ".join(sys.argv[1:])
        print(f"User: {text}")
        response = run_single_response(text)
        print(f"Assistant: {response}")
    else:
        # Run interactive mode
        run_interactive_chatbot()