import os
import logging
import threading
import time
from openai import AzureOpenAI
from dotenv import load_dotenv
from chroma_client import ChromaDBClient
from models import ChatRole
from db_manager import DatabaseManager

# Configure logging (file only, no console output)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log')
    ]
)
logger = logging.getLogger(__name__)

def initialize_clients():
    """Initialize and return the Azure OpenAI, ChromaDB, and Database clients."""
    load_dotenv()
    
    openai_client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-15-preview"
    )
    
    chroma_client = ChromaDBClient()
    chroma_client.connect()
    
    # Initialize database connection
    connection_string = DatabaseManager.get_connection_string()
    sqlalchemy_conn_string = f"mssql+pyodbc:///?odbc_connect={connection_string}"
    db_manager = DatabaseManager(sqlalchemy_conn_string, "Azure AI Chat")
    
    return openai_client, chroma_client, db_manager

def cleanup_thread(db_manager):
    """Background thread to periodically clean up old messages."""
    while True:
        try:
            deleted = db_manager.cleanup_old_messages()
            if deleted > 0:
                logger.info(f"Cleanup thread removed {deleted} old messages")
            time.sleep(86400)  # Run once per day
        except Exception as e:
            logger.error(f"Error in cleanup thread: {str(e)}")
            time.sleep(3600)  # Wait an hour before retrying on error

def get_context(chroma_client, query):
    """Get relevant context from ChromaDB."""
    documents = chroma_client.search(query)
    return chroma_client.format_context(documents)

def chat_with_ai(openai_client, chroma_client, db_manager, user_input, conversation_history, message_sequence):
    """Send a message to the AI and get its response."""
    try:
        # Get relevant context from ChromaDB
        context = get_context(chroma_client, user_input)
        logger.info(f"Retrieved context: {context}")
        
        # Start with the system message and conversation history
        system_message = """"###############   Context  ####################################################
You are an AI assistant that provides commercial loan customers with pricing for loans available through the Federal Home Loan Bank of Indianapolis. 
#################        Goal          ###############################################
Your goal is to provide the customer a price based off the Advance products they ask about. 
##################    Instructions    #############################################
When you are asked about a price or a loan, you will look to your knowledge base to determine if you can determine how to calculate the loan product. 
You only price loans for products you are aware of 
If you cannot find the loan product in your knowledge base, you should politely describe to the customer what loans you are capable of pricing. 
You can look to your internal knowledge base for a SOFR Rate and FHLB Cost of Funds
If you cannot find details about the loan product type, do not elaborate. Just politely tell the user you do not know about that product.
If you do know about the product, you should try to determine the information needed to calculate the loan price by asking the user about the maturity and amount of the loan.
If you need more information to price the loan, you should ask the user for that information.
You should not ask the customer about their credit score.
Once you have everything you need to calculate the loan price, describe how the calculation works for that product. 
Identify any unclear or ambiguous information in your response and rephrase it for clarity.
Try to argue against your own output and see if you can find any flaws. If so, address them. Walk me through the process
"""
        
        messages = [
            {"role": "system", "content": system_message},
        ]
        
        # Log system message to database
        db_manager.log_message(system_message, ChatRole.SYSTEM, message_sequence)
        print(f"Logged SYSTEM message: {system_message[:50]}...")
        message_sequence += 1
        
        # Add context if available
        if context:
            context_message = f"Context: {context}"
            messages.append({"role": "system", "content": context_message})
            db_manager.log_message(context_message, ChatRole.SYSTEM, message_sequence)
            print(f"Logged SYSTEM context message: {context_message[:50]}...")
            message_sequence += 1
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Log user message to database
        db_manager.log_message(user_input, ChatRole.USER, message_sequence)
        print(f"Logged USER message: {user_input[:50]}...")
        message_sequence += 1
        
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        
        ai_response = response.choices[0].message.content
        
        # Log AI response to database
        db_manager.log_message(ai_response, ChatRole.ASSISTANT, message_sequence + 1)
        
        return ai_response
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    """Main function to run the chat application."""
    logger.info("Initializing Azure OpenAI Chat with ChromaDB and SQL Server integration...")
    openai_client, chroma_client, db_manager = initialize_clients()
    
    # Start cleanup thread
    cleanup_thread_handle = threading.Thread(
        target=cleanup_thread,
        args=(db_manager,),
        daemon=True
    )
    cleanup_thread_handle.start()
    
    # Console output for user interaction
    print("\nWelcome to Azure AI Chat!")
    print("Type 'exit' to end the conversation.\n")
    
    # Log the startup
    logger.info("Application started successfully")
    
    # Initialize conversation history and message sequence
    conversation_history = []
    message_sequence = 0
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            print("\nGoodbye!")
            logger.info("User ended the session")
            break
        
        if user_input:
            ai_response = chat_with_ai(openai_client, chroma_client, db_manager, user_input, conversation_history, message_sequence)
            message_sequence += 2  # Increment by 2 to account for both user and AI messages
            print("\nAI:", ai_response)
            logger.info(f"AI response: {ai_response}")
            
            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep only the last 10 messages to prevent context window from getting too large
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
        else:
            print("Please enter a message.")
            logger.info("Empty message received")

if __name__ == "__main__":
    main()
