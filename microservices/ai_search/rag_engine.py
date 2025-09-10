"""
RAG (Retrieval-Augmented Generation) Engine for Intelligent Search

This module implements the core RAG functionality for semantic search,
including document indexing, retrieval, and answer generation.
"""

import asyncio
import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

# AI/ML imports
import openai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from rank_bm25 import BM25Okapi

# Text processing
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Configuration
from pydantic import BaseSettings


class RAGConfig(BaseSettings):
    """Configuration for RAG engine."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-3-small"
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "lms_content"
    
    # Search Configuration
    max_retrieval_docs: int = 10
    similarity_threshold: float = 0.7
    bm25_weight: float = 0.3
    semantic_weight: float = 0.7
    
    # Text Processing
    max_chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"


class DocumentProcessor:
    """Process and chunk documents for indexing."""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self._ensure_nltk_data()
    
    def _ensure_nltk_data(self):
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        return text
    
    def chunk_text(self, text: str, max_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Chunk text into overlapping segments."""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > max_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'size': current_size,
                    'sentence_count': len(sent_tokenize(current_chunk))
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + " " + sentence
                current_size = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size = len(current_chunk)
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'size': current_size,
                'sentence_count': len(sent_tokenize(current_chunk))
            })
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of a chunk."""
        if len(text) <= overlap_size:
            return text
        
        # Try to break at sentence boundary
        sentences = sent_tokenize(text)
        overlap_text = ""
        
        for sentence in reversed(sentences):
            if len(overlap_text + sentence) <= overlap_size:
                overlap_text = sentence + " " + overlap_text
            else:
                break
        
        return overlap_text.strip()
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract keywords from text."""
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        
        # Filter tokens
        filtered_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token.isalnum() and token not in stop_words and len(token) > 2
        ]
        
        # Count frequency
        from collections import Counter
        word_freq = Counter(filtered_tokens)
        
        return [word for word, _ in word_freq.most_common(top_k)]


class VectorStore:
    """Vector database interface using ChromaDB."""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client = chromadb.PersistentClient(
            path=config.chroma_persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self._get_or_create_collection()
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logging.info(f"VectorStore initialized with collection: {config.chroma_collection_name}")
    
    def _get_or_create_collection(self):
        """Get or create ChromaDB collection."""
        try:
            return self.client.get_collection(name=self.config.chroma_collection_name)
        except Exception:
            return self.client.create_collection(
                name=self.config.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store."""
        try:
            texts = [doc['content'] for doc in documents]
            embeddings = self.embedding_model.encode(texts).tolist()
            
            ids = [doc['id'] for doc in documents]
            metadatas = [doc.get('metadata', {}) for doc in documents]
            
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logging.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logging.error(f"Error adding documents to vector store: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            documents = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    })
            
            return documents
            
        except Exception as e:
            logging.error(f"Error searching vector store: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        try:
            self.collection.delete(ids=[doc_id])
            logging.info(f"Deleted document {doc_id} from vector store")
            return True
        except Exception as e:
            logging.error(f"Error deleting document {doc_id}: {e}")
            return False


class KeywordSearcher:
    """BM25-based keyword searcher."""
    
    def __init__(self):
        self.corpus = []
        self.documents = []
        self.bm25 = None
        self.processor = DocumentProcessor()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to keyword index."""
        for doc in documents:
            self.documents.append(doc)
            tokenized_doc = word_tokenize(doc['content'].lower())
            self.corpus.append(tokenized_doc)
        
        # Rebuild BM25 index
        if self.corpus:
            self.bm25 = BM25Okapi(self.corpus)
            logging.info(f"Built BM25 index with {len(self.corpus)} documents")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using BM25 keyword matching."""
        if not self.bm25:
            return []
        
        tokenized_query = word_tokenize(query.lower())
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top results
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include docs with positive scores
                doc = self.documents[idx].copy()
                doc['bm25_score'] = float(scores[idx])
                results.append(doc)
        
        return results


class AnswerGenerator:
    """Generate answers using OpenAI GPT models."""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)
    
    def generate_answer(
        self, 
        query: str, 
        context_documents: List[Dict[str, Any]], 
        answer_length: str = "medium"
    ) -> Dict[str, Any]:
        """Generate an answer using retrieved context."""
        try:
            # Prepare context
            context = self._prepare_context(context_documents)
            
            # Create prompt based on answer length
            system_prompt = self._get_system_prompt(answer_length)
            user_prompt = f"""
Context information:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided above.
"""
            
            # Generate answer
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=self._get_max_tokens(answer_length)
            )
            
            answer = response.choices[0].message.content
            
            # Generate related questions
            related_questions = self._generate_related_questions(query, context)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(context_documents, query)
            
            return {
                'answer': answer,
                'confidence': confidence,
                'sources': context_documents,
                'related_questions': related_questions,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logging.error(f"Error generating answer: {e}")
            return {
                'answer': "I apologize, but I'm unable to generate an answer at this time. Please try rephrasing your question.",
                'confidence': 0.0,
                'sources': [],
                'related_questions': [],
                'error': str(e)
            }
    
    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(documents[:5], 1):  # Limit to top 5 docs
            title = doc.get('metadata', {}).get('title', f'Document {i}')
            content = doc['content'][:500]  # Limit content length
            
            context_parts.append(f"Source {i} - {title}:\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self, answer_length: str) -> str:
        """Get system prompt based on answer length."""
        base_prompt = """You are an intelligent educational assistant for a learning management system. 
Your role is to provide accurate, helpful, and educational responses based on the provided context.

Guidelines:
- Use only information from the provided context
- If the context doesn't contain sufficient information, acknowledge this
- Provide clear, well-structured answers
- Include relevant examples when helpful
- Maintain an educational and professional tone
"""
        
        if answer_length == "short":
            return base_prompt + "\n- Keep your response concise (1-2 paragraphs maximum)"
        elif answer_length == "long":
            return base_prompt + "\n- Provide a comprehensive, detailed response with examples and explanations"
        else:  # medium
            return base_prompt + "\n- Provide a balanced response that covers key points clearly"
    
    def _get_max_tokens(self, answer_length: str) -> int:
        """Get max tokens based on answer length."""
        token_limits = {
            'short': 200,
            'medium': 500,
            'long': 1000
        }
        return token_limits.get(answer_length, 500)
    
    def _generate_related_questions(self, original_query: str, context: str) -> List[str]:
        """Generate related questions based on the query and context."""
        try:
            prompt = f"""
Based on the original question "{original_query}" and the following context, 
generate 3 related questions that a student might also want to ask:

Context: {context[:300]}...

Related questions:"""
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": "Generate educational follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            questions_text = response.choices[0].message.content
            questions = [q.strip() for q in questions_text.split('\n') if q.strip() and not q.strip().startswith('-')]
            
            return questions[:3]  # Return max 3 questions
            
        except Exception as e:
            logging.error(f"Error generating related questions: {e}")
            return []
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]], query: str) -> float:
        """Calculate confidence score for the answer."""
        if not documents:
            return 0.0
        
        # Factors that affect confidence:
        # 1. Number of relevant documents
        # 2. Average similarity scores
        # 3. Content length/quality
        
        avg_similarity = np.mean([doc.get('similarity_score', 0) for doc in documents])
        doc_count_factor = min(len(documents) / 5, 1.0)  # Normalize to max 5 docs
        
        confidence = (avg_similarity * 0.7) + (doc_count_factor * 0.3)
        return round(confidence, 2)


class RAGEngine:
    """Main RAG engine that orchestrates retrieval and generation."""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore(self.config)
        self.keyword_searcher = KeywordSearcher()
        self.answer_generator = AnswerGenerator(self.config)
        
        logging.info("RAG Engine initialized successfully")
    
    def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Index a document for search and retrieval."""
        try:
            # Clean and process content
            cleaned_content = self.document_processor.clean_text(content)
            chunks = self.document_processor.chunk_text(
                cleaned_content, 
                self.config.max_chunk_size, 
                self.config.chunk_overlap
            )
            
            # Prepare documents for indexing
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                chunk_metadata = {
                    'original_id': doc_id,
                    'title': title,
                    'chunk_index': i,
                    'chunk_size': chunk['size'],
                    'created_at': datetime.now().isoformat(),
                    **(metadata or {})
                }
                
                documents.append({
                    'id': chunk_id,
                    'content': chunk['text'],
                    'metadata': chunk_metadata
                })
            
            # Index in vector store
            vector_success = self.vector_store.add_documents(documents)
            
            # Index in keyword searcher
            self.keyword_searcher.add_documents(documents)
            
            logging.info(f"Indexed document {doc_id} with {len(chunks)} chunks")
            return vector_success
            
        except Exception as e:
            logging.error(f"Error indexing document {doc_id}: {e}")
            return False
    
    def search(self, query: str, search_type: str = "hybrid", max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        results = []
        
        if search_type in ["semantic", "hybrid"]:
            # Vector search
            vector_results = self.vector_store.search_similar(query, max_results)
            results.extend(vector_results)
        
        if search_type in ["keyword", "hybrid"]:
            # Keyword search
            keyword_results = self.keyword_searcher.search(query, max_results)
            
            # Merge results for hybrid search
            if search_type == "hybrid":
                results = self._merge_search_results(results, keyword_results)
            else:
                results = keyword_results
        
        # Sort by combined score and limit results
        if search_type == "hybrid":
            results = self._calculate_hybrid_scores(results)
        
        results = sorted(results, key=lambda x: x.get('final_score', x.get('similarity_score', 0)), reverse=True)
        
        return results[:max_results]
    
    def generate_answer(self, query: str, context_ids: Optional[List[str]] = None, answer_length: str = "medium") -> Dict[str, Any]:
        """Generate an answer using RAG."""
        try:
            # Retrieve relevant documents
            if context_ids:
                # Use specific documents if provided
                context_documents = []
                # TODO: Implement retrieval by specific IDs
            else:
                # Search for relevant documents
                context_documents = self.search(query, "hybrid", self.config.max_retrieval_docs)
            
            # Filter by similarity threshold
            relevant_docs = [
                doc for doc in context_documents 
                if doc.get('similarity_score', 0) >= self.config.similarity_threshold
            ]
            
            if not relevant_docs:
                return {
                    'answer': "I don't have enough relevant information to answer your question. Please try rephrasing or ask about a different topic.",
                    'confidence': 0.0,
                    'sources': [],
                    'related_questions': []
                }
            
            # Generate answer
            result = self.answer_generator.generate_answer(query, relevant_docs, answer_length)
            
            return result
            
        except Exception as e:
            logging.error(f"Error in generate_answer: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question.",
                'confidence': 0.0,
                'sources': [],
                'related_questions': [],
                'error': str(e)
            }
    
    def find_similar_content(self, content_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Find content similar to a given document."""
        # TODO: Implement similarity search by document ID
        # This would retrieve the original document and find similar ones
        return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from all indices."""
        try:
            # Delete from vector store (all chunks)
            # TODO: Implement deletion of all chunks for a document
            success = True
            
            # TODO: Remove from keyword searcher
            # This is more complex as we need to rebuild the index
            
            logging.info(f"Deleted document {doc_id}")
            return success
            
        except Exception as e:
            logging.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def _merge_search_results(self, vector_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """Merge vector and keyword search results."""
        merged = {}
        
        # Add vector results
        for doc in vector_results:
            merged[doc['id']] = doc
        
        # Add keyword results
        for doc in keyword_results:
            if doc['id'] in merged:
                # Merge scores
                merged[doc['id']]['bm25_score'] = doc.get('bm25_score', 0)
            else:
                merged[doc['id']] = doc
        
        return list(merged.values())
    
    def _calculate_hybrid_scores(self, results: List[Dict]) -> List[Dict]:
        """Calculate hybrid scores combining semantic and keyword scores."""
        for doc in results:
            semantic_score = doc.get('similarity_score', 0)
            keyword_score = doc.get('bm25_score', 0)
            
            # Normalize BM25 score (rough approximation)
            normalized_bm25 = min(keyword_score / 10, 1.0) if keyword_score > 0 else 0
            
            # Calculate weighted final score
            final_score = (
                semantic_score * self.config.semantic_weight +
                normalized_bm25 * self.config.bm25_weight
            )
            
            doc['final_score'] = final_score
        
        return results


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global RAG engine instance
rag_engine = None

def get_rag_engine() -> RAGEngine:
    """Get or create the global RAG engine instance."""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine
