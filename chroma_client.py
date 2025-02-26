import os
import requests
import logging
from dotenv import load_dotenv

# Get the logger configured in azure_ai_chat.py
logger = logging.getLogger(__name__)

class ChromaDBClient:
    def __init__(self):
        """Initialize ChromaDB client with connection details from environment variables."""
        load_dotenv()
        self.host = os.getenv("CHROMA_SERVICE_HOST", "http://localhost")
        self.port = int(os.getenv("CHROMA_SERVICE_PORT", "8000"))
        self.base_url = f"{self.host}:{self.port}"

    def connect(self):
        """Test connection to ChromaDB instance."""
        try:
            logger.debug(f"Attempting to connect to ChromaDB at {self.base_url}")
            
            # Get collections to test connection
            response = requests.get(f"{self.base_url}/collections")
            if response.status_code == 200:
                logger.debug("ChromaDB connection successful")
                collections = response.json()
                logger.debug(f"Available ChromaDB collections: {collections}")
                return True
            else:
                logger.error(f"Failed to connect to ChromaDB: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {str(e)}")
            return False

    def search(self, query, n_results=3):
        """
        Search documents using the query endpoint.
        
        Args:
            query (str): The search query
            n_results (int): Number of results to return
            
        Returns:
            list: List of relevant documents
        """
        try:
            params = {
                "collection_name": "loandocuments",
                "query_text": query,
                "n_results": n_results
            }
            
            logger.debug(f"Sending query to ChromaDB: {params}")
            response = requests.post(f"{self.base_url}/query", params=params)
            logger.debug(f"ChromaDB response status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                logger.debug(f"Raw ChromaDB results: {results}")
                
                if isinstance(results, list) and results:
                    documents = [doc.get("content", "") for doc in results]
                    logger.debug(f"Extracted documents: {documents}")
                    return documents
                else:
                    logger.debug("No documents found in results")
                    return []
            else:
                logger.error(f"Error searching ChromaDB: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []

    def format_context(self, documents):
        """
        Format the retrieved documents into a context string.
        
        Args:
            documents (list): List of relevant documents
            
        Returns:
            str: Formatted context string
        """
        if not documents:
            return ""
        
        context = "Based on internal knowledge:\n\n"
        for doc in documents:
            context += f"{doc}\n\n"
        
        return context.strip()
