"""
Azure AI Foundry Support Agent Client
- Calls the pre-deployed "supportagentt" agent from AI Foundry
- Submits customer issues and receives AI-powered resolutions
"""

import os
import logging
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# =====================================================
# LOGGING SETUP
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

class Config:
    """Configuration for AI Foundry agent"""
    
    # Azure AI Foundry
    AI_ENDPOINT = os.getenv(
        "AI_ENDPOINT",
        "https://aifsamplex.services.ai.azure.com/api/projects/proj-default"
    )
    
    # Agent details
    AGENT_NAME = os.getenv("AGENT_NAME", "supportagentt")
    AGENT_VERSION = os.getenv("AGENT_VERSION", "21")


# =====================================================
# AZURE AI FOUNDRY CLIENT
# =====================================================

def get_openai_client():
    """
    Initialize Azure AI Foundry and get OpenAI-compatible client
    
    Returns:
        OpenAI client configured for AI Foundry
    """
    try:
        logger.info("🤖 Connecting to Azure AI Foundry...")
        project_client = AIProjectClient(
            endpoint=Config.AI_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        logger.info("✅ Connected to AI Foundry")
        
        openai_client = project_client.get_openai_client()
        logger.info("✅ OpenAI client initialized")
        
        return openai_client
    except Exception as e:
        logger.error(f"❌ Failed to initialize client: {e}")
        raise


# =====================================================
# CALL DEPLOYED AGENT
# =====================================================

def call_support_agent(openai_client, user_message: str) -> str:
    """
    Call the deployed supportagentt agent
    
    Args:
        openai_client: OpenAI client from AI Foundry
        user_message: Customer issue or question
        
    Returns:
        str: Agent response
    """
    try:
        logger.info("🧠 Submitting request to supportagentt agent...")
        
        response = openai_client.responses.create(
            input=[{"role": "user", "content": user_message}],
            extra_body={
                "agent_reference": {
                    "name": Config.AGENT_NAME,
                    "version": Config.AGENT_VERSION,
                    "type": "agent_reference"
                }
            },
        )
        
        logger.info("✅ Response received from agent")
        return response.output_text
        
    except Exception as e:
        logger.error(f"❌ Agent call failed: {e}")
        raise


# =====================================================
# INTERACTIVE SESSION
# =====================================================

def get_user_input() -> str:
    """Get customer issue from user"""
    print("\n" + "="*60)
    print("    💼 SUPPORT AGENT (AI Foundry)")
    print(f"    Agent: {Config.AGENT_NAME} v{Config.AGENT_VERSION}")
    print("="*60)
    
    print("\n📝 Describe your issue or ask a question:")
    user_input = input("> ").strip()
    
    if not user_input:
        logger.warning("⚠️ No input provided")
        return None
    
    return user_input


def display_response(response: str):
    """Display agent response"""
    print("\n" + "="*60)
    print("       ✅ AGENT RESPONSE")
    print("="*60)
    print(f"\n{response}\n")
    print("="*60 + "\n")


# =====================================================
# MAIN EXECUTION
# =====================================================

def main():
    """Main execution flow"""
    try:
        # Initialize AI Foundry client
        openai_client = get_openai_client()
        
        while True:
            # Get user input
            user_message = get_user_input()
            
            if not user_message:
                print("❌ No input provided. Exiting.")
                break
            
            # Call the deployed agent
            response = call_support_agent(openai_client, user_message)
            
            # Display response
            display_response(response)
            
            # Ask if they want to continue
            print("Submit another question? (yes/no): ", end="")
            again = input().strip().lower()
            if again not in ['yes', 'y']:
                print("\n👋 Thank you for using Support Agent! Goodbye!\n")
                break
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
