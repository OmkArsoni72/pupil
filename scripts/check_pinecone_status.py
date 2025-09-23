# check_pinecone_status.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Create Pinecone client instance
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# List all indexes
indexes = pc.list_indexes()
print("Pinecone Indexes:", indexes)
