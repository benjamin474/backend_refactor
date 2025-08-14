from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
from service.rag_service import RAGService

# Create Blueprint for simple RAG routes (no authentication required)
simple_rag_bp = Blueprint('simple_rag', __name__)
rag_service = RAGService()

# In-memory chat sessions (in production, use Redis or database)
chat_sessions = {}

@simple_rag_bp.route('/chat', methods=['POST', 'OPTIONS'])
@cross_origin()
def chat():
    """Simple chat endpoint with conversation memory"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400
        
        user_message = data['message']
        use_ai = data.get('use_ai', True)
        n_results = data.get('n_results', 3)
        session_id = data.get('session_id', 'default')  # Client can provide session ID
        
        # Get or create chat history for this session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        chat_history = chat_sessions[session_id]
        
        # Add user message to history
        chat_history.append({"role": "user", "content": user_message})
        
        # Keep only last 10 messages to avoid token limits
        if len(chat_history) > 10:
            chat_history.pop(0)
        
        # Get RAG context
        search_result = rag_service.search_documents(user_message, n_results)
        
        if search_result['success'] and use_ai:
            # Prepare context from documents
            context_docs = [doc["content"] for doc in search_result["documents"]]
            rag_context = "\n\n--- Documents ---\n" + "\n".join(context_docs)
            
            # Create enhanced system prompt with conversation context
            system_prompt = f"""
You are a helpful assistant for federated learning research. You can answer based on the provided research data and also use your general knowledge about federated learning.

Current Research Data:
{rag_context}

Instructions:
- Answer the user's question using the research data when relevant
- Maintain conversation context from previous messages
- Be conversational and helpful
- If asked about previous conversation, refer to the chat history
"""
            
            # Prepare messages for OpenAI (system + history)
            messages = [{"role": "system", "content": system_prompt}] + chat_history
            
            # Call OpenAI API with conversation history
            from openai import OpenAI
            openai_client = OpenAI()
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            ai_response = response.choices[0].message.content
            
            # Add assistant response to history
            chat_history.append({"role": "assistant", "content": ai_response})
            
            return jsonify({
                "success": True,
                "message": ai_response,
                "sources": search_result.get('documents', []),
                "total_sources": search_result.get('total_found', 0),
                "query": user_message,
                "session_id": session_id,
                "conversation_length": len(chat_history)
            })
        else:
            # Return search results without AI processing
            return jsonify({
                "success": True,
                "message": "Here are the relevant documents I found:",
                "sources": search_result.get('documents', []),
                "total_sources": search_result.get('total_found', 0),
                "query": user_message,
                "session_id": session_id
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@simple_rag_bp.route('/chat/history', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_chat_history():
    """Get chat history for a session"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        session_id = request.args.get('session_id', 'default')
        
        if session_id in chat_sessions:
            return jsonify({
                "success": True,
                "session_id": session_id,
                "history": chat_sessions[session_id],
                "total_messages": len(chat_sessions[session_id])
            })
        else:
            return jsonify({
                "success": True,
                "session_id": session_id,
                "history": [],
                "total_messages": 0
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@simple_rag_bp.route('/chat/clear', methods=['POST', 'OPTIONS'])
@cross_origin()
def clear_chat_history():
    """Clear chat history for a session"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default') if data else 'default'
        
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        
        return jsonify({
            "success": True,
            "message": f"Chat history cleared for session {session_id}",
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@simple_rag_bp.route('/ask', methods=['POST', 'OPTIONS'])
@cross_origin()
def ask_question():
    """Ask a question and get AI-powered response (simple version without authentication)"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "message": "Query is required"
            }), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                "success": False,
                "message": "Query cannot be empty"
            }), 400
        
        n_results = data.get('n_results', 3)
        use_ai = data.get('use_ai', True)
        
        # Validate n_results
        if not isinstance(n_results, int) or n_results < 1 or n_results > 10:
            n_results = 3
        
        result = rag_service.ask_question(query, n_results, use_ai)
        
        return jsonify(result), 200 if result["success"] else 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@simple_rag_bp.route('/search', methods=['POST', 'OPTIONS'])
@cross_origin()
def search():
    """Simple search endpoint - returns documents without AI processing"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        query = data['query']
        n_results = data.get('n_results', 5)
        
        # Call RAG service for search only
        result = rag_service.search_documents(query, n_results)
        
        if result['success']:
            return jsonify({
                "success": True,
                "documents": result['documents'],
                "total_found": result['total_found'],
                "query": query
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('message', 'No documents found')
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@simple_rag_bp.route('/status', methods=['GET'])
@cross_origin()
def status():
    """Check RAG system status"""
    try:
        stats = rag_service.get_collection_stats()
        
        if stats['success']:
            return jsonify({
                "success": True,
                "status": "RAG system is running",
                "total_documents": stats['total_documents'],
                "collection_name": stats['collection_name']
            })
        else:
            return jsonify({
                "success": False,
                "error": "RAG system error"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"System error: {str(e)}"
        }), 500
