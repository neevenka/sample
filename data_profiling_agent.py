"""
Azure AI Foundry Data Profiling Agent
- Analyzes raw data quality using AI
- Secure credential handling
- Comprehensive error handling
"""

import os
import json
import logging
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
import pymssql

# =====================================================
# LOGGING SETUP
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION (USE ENVIRONMENT VARIABLES)
# =====================================================

class Config:
    """Configuration management with environment variables"""
    
    # Azure AI Foundry
    AI_ENDPOINT = os.getenv(
        "AI_ENDPOINT",
        "https://aifsamplex.services.ai.azure.com/api/projects/proj-default"
    )
    AI_MODEL = os.getenv("AI_MODEL", "gpt-5.1")
    
    # SQL Server
    DB_SERVER = os.getenv("DB_SERVER", "testaiagent2.database.windows.net")
    DB_USER = os.getenv("DB_USER", "neevenka")
    DB_PASSWORD = os.getenv("DB_PASSWORD")  # ⚠️ Set via environment variable!
    DB_NAME = os.getenv("DB_NAME", "testdbaiagent")
    DB_PORT = int(os.getenv("DB_PORT", "1433"))
    
    # Query
    QUERY_LIMIT = int(os.getenv("QUERY_LIMIT", "200"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.DB_PASSWORD:
            logger.error("❌ DB_PASSWORD environment variable not set!")
            return False
        return True


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_database_connection():
    """
    Establish secure SQL Server connection
    
    Returns:
        pymssql.Connection: Database connection
    """
    try:
        logger.info("🔗 Connecting to SQL Server...")
        conn = pymssql.connect(
            server=Config.DB_SERVER,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
            timeout=30
        )
        logger.info("✅ SQL Server connection successful")
        return conn
    except pymssql.Error as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


def fetch_raw_data(conn) -> str:
    """
    Fetch raw data from database
    
    Args:
        conn: Database connection
        
    Returns:
        str: Concatenated raw data
    """
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT TOP {Config.QUERY_LIMIT} payload
        FROM stg_raw_data
        """
        logger.info(f"📊 Executing query (LIMIT: {Config.QUERY_LIMIT})...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("⚠️ No data found in database")
            return ""
        
        data = "\n".join([r[0] for r in rows if r[0]])
        logger.info(f"✅ Fetched {len(rows)} rows ({len(data)} characters)")
        return data
        
    except pymssql.Error as e:
        logger.error(f"❌ Query execution failed: {e}")
        raise
    finally:
        cursor.close()


# =====================================================
# AZURE AI CLIENT
# =====================================================

def get_ai_client() -> AIProjectClient:
    """
    Initialize Azure AI Foundry client
    
    Returns:
        AIProjectClient: Authenticated AI project client
    """
    try:
        logger.info("🤖 Initializing Azure AI Foundry client...")
        client = AIProjectClient(
            endpoint=Config.AI_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        logger.info("✅ AI Foundry client initialized")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI client: {e}")
        raise


# =====================================================
# DATA PROFILING PROMPT
# =====================================================

def build_profiling_prompt(data: str) -> str:
    """Build the data profiling prompt"""
    return f"""
You are a Senior Data Quality & Data Intelligence Agent.

Analyze this raw dataset:

---------------------
{data}
---------------------

Provide a JSON response with:

1. **data_domain**: Type of data (finance, logs, SQL scripts, social, etc.)
2. **description**: What this data represents
3. **quality_score**: 0-100 score
4. **noise_level**: Low/Medium/High
5. **has_structure**: Yes/No with schema suggestion
6. **key_patterns**: List of identified patterns
7. **data_issues**: List of issues found
8. **business_insights**: Key insights
9. **recommendations**: Action items

Return ONLY valid JSON, no markdown formatting.
"""


# =====================================================
# CALL AI AGENT
# =====================================================

def analyze_data_with_ai(openai_client, prompt: str) -> Optional[dict]:
    """
    Call AI model for data profiling analysis
    
    Args:
        openai_client: OpenAI-compatible client
        prompt: Profiling prompt
        
    Returns:
        dict: Parsed AI response
    """
    try:
        logger.info("🧠 Calling AI model for data analysis...")
        
        response = openai_client.chat.completions.create(
            model=Config.AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a data quality expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        logger.info("✅ AI analysis complete")
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            logger.warning("⚠️ Could not parse AI response as JSON")
            return {"raw_response": response_text}
            
    except Exception as e:
        logger.error(f"❌ AI model call failed: {e}")
        raise


# =====================================================
# MAIN EXECUTION
# =====================================================

def main():
    """Main execution flow"""
    
    # Validate configuration
    if not Config.validate():
        raise ValueError("Invalid configuration")
    
    conn = None
    try:
        # 1. Connect to database
        conn = get_database_connection()
        
        # 2. Fetch data
        data = fetch_raw_data(conn)
        if not data:
            logger.warning("No data to analyze")
            return
        
        # 3. Initialize AI client
        ai_client = get_ai_client()
        openai_client = ai_client.get_openai_client()
        
        # 4. Build profiling prompt
        prompt = build_profiling_prompt(data)
        
        # 5. Analyze with AI
        insights = analyze_data_with_ai(openai_client, prompt)
        
        # 6. Display results
        print("\n" + "="*60)
        print("       🎯 AI DATA PROFILING INSIGHTS")
        print("="*60 + "\n")
        print(json.dumps(insights, indent=2))
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
    finally:
        # Clean up database connection
        if conn:
            conn.close()
            logger.info("🔌 Database connection closed")


if __name__ == "__main__":
    main()
