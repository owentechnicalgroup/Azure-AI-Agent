import os
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv
from chroma_client import ChromaDBClient

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
    """Initialize and return the Azure OpenAI and ChromaDB clients."""
    load_dotenv()
    
    openai_client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-15-preview"
    )
    
    chroma_client = ChromaDBClient()
    chroma_client.connect()
    
    return openai_client, chroma_client

def get_context(chroma_client, query):
    """Get relevant context from ChromaDB."""
    documents = chroma_client.search(query)
    return chroma_client.format_context(documents)

def chat_with_ai(openai_client, chroma_client, user_input, conversation_history):
    """Send a message to the AI and get its response."""
    try:
        # Get relevant context from ChromaDB
        context = get_context(chroma_client, user_input)
        logger.info(f"Retrieved context: {context}")
        
        # Start with the system message and conversation history
        messages = [
            {"role": "system", "content": """You are an AI assistant that provides bank customers with pricing for loans. You only price loans for products you are aware of. 
When you are asked about a price or a loan, you will look to your knowledge base to determine if you can determine the loan product. You will use this loan product to determine how to calculate the loan. 
If you cannot find the loan product in your knowledge base, you should politely describe to the customer what loans you are capable of pricing. 
If you cannot find details about the loan product type, do not elaborate. Just politely tell the user you do not know about that product.
If you do know about the product, you should try to determine the information needed to calculate the loan price by asking the loan price.
If you need more information to price the loan, you should ask the user for that information.
You should not ask the customer about their credit score as these are commercial loans.
Once you have everything you need to calculate the loan price, describe how the calculation works for that product. 
Market rates are provided in your knowledge base, so do not ask the customer for them.
Be succinct in your answers.
"""},
        ]
        
        # Add context if available
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    """Main function to run the chat application."""
    logger.info("Initializing Azure OpenAI Chat with ChromaDB integration...")
    openai_client, chroma_client = initialize_clients()
    
    # Console output for user interaction
    print("\nWelcome to Azure AI Chat!")
    print("Type 'exit' to end the conversation.\n")
    
    # Log the startup
    logger.info("Application started successfully")
    
    # Initialize conversation history
    conversation_history = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            print("\nGoodbye!")
            logger.info("User ended the session")
            break
        
        if user_input:
            ai_response = chat_with_ai(openai_client, chroma_client, user_input, conversation_history)
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
