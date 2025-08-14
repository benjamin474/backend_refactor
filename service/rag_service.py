import chromadb
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        # Set up paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.rag_dir = os.path.join(os.path.dirname(self.script_dir), 'RAG')
        self.chroma_path = os.path.join(self.rag_dir, "chroma_db")
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(name="federated_analysis")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI()
    
    def search_documents(self, query, n_results=3):
        """Search for relevant documents without AI response"""
        try:
            # Try to determine the analysis type from the query
            query_lower = query.lower()
            analysis_type_filters = {}
            
            if any(keyword in query_lower for keyword in ['keyword', 'top keyword', 'most keyword']):
                analysis_type_filters = {"analysis_type": "keyword_occurence"}
            elif any(keyword in query_lower for keyword in ['author', 'top author', 'most author', 'researcher']):
                analysis_type_filters = {"analysis_type": "author_year"}
            elif any(keyword in query_lower for keyword in ['reference', 'citation', 'paper', 'most cited']):
                analysis_type_filters = {"analysis_type": "reference"}
            elif any(keyword in query_lower for keyword in ['field', 'research field', 'domain']):
                analysis_type_filters = {"analysis_type": "field_occurence"}
            
            # Search with optional filtering
            if analysis_type_filters:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=analysis_type_filters
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            
            if not results['documents'][0]:
                return {
                    "success": False,
                    "message": "No relevant documents found",
                    "documents": []
                }
            
            # Format the results
            formatted_docs = []
            for i, doc in enumerate(results['documents'][0]):
                formatted_docs.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            
            return {
                "success": True,
                "query": query,
                "documents": formatted_docs,
                "total_found": len(formatted_docs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Search error: {str(e)}",
                "documents": []
            }
    
    def ask_question(self, query, n_results=3, use_ai=True):
        """Ask a question and get AI-powered response"""
        try:
            print(f"RAG Service - Received query: {query}")
            print(f"RAG Service - use_ai: {use_ai}, n_results: {n_results}")
            
            # First search for relevant documents
            search_result = self.search_documents(query, n_results)
            
            if not search_result["success"]:
                print(f"RAG Service - Search failed: {search_result}")
                return search_result
            
            print(f"RAG Service - Found {len(search_result['documents'])} documents")
            
            # If AI is disabled, just return search results
            if not use_ai:
                return search_result
            
            # Prepare context for AI
            context_docs = [doc["content"] for doc in search_result["documents"]]
            print(f"RAG Service - Context docs length: {len(context_docs)}")
            
            system_prompt = f"""
You are a helpful assistant. You answer questions about federated learning analysis and research data.
But you only answer based on knowledge I'm providing you. You don't use your internal 
knowledge and you don't make things up.

If you don't know the answer, just say: I don't know

--------------------

The data:

{str(context_docs)}

"""
            
            print("RAG Service - Calling OpenAI API...")
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )
            
            ai_response = response.choices[0].message.content
            print(f"RAG Service - AI response: {ai_response}")
            
            return {
                "success": True,
                "query": query,
                "response": ai_response,  # 修改字段名稱為前端期望的 response
                "ai_response": ai_response,  # 保持向後兼容
                "source_documents": search_result["documents"],
                "total_sources": len(search_result["documents"])
            }
            
        except Exception as e:
            print(f"RAG Service - Error: {str(e)}")
            return {
                "success": False,
                "message": f"RAG error: {str(e)}",
                "query": query
            }
    
    def get_collection_stats(self):
        """Get statistics about the RAG database"""
        try:
            count = self.collection.count()
            return {
                "success": True,
                "total_documents": count,
                "collection_name": "federated_analysis"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Stats error: {str(e)}"
            }
