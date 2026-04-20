"""
Chatbot Utilities for Vector Search and RAG
Implements simple vector similarity matching for prompt-SQL pairs
"""
import sqlite3
import re
import math
from collections import Counter

class VectorSearchEngine:
    """Simple TF-IDF based vector search engine for matching user queries to prompt templates"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _tokenize(self, text):
        """Simple tokenization - lowercase, remove punctuation, split by whitespace"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                      'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                      'through', 'during', 'before', 'after', 'above', 'below',
                      'between', 'under', 'and', 'but', 'or', 'yet', 'so', 'if',
                      'because', 'although', 'though', 'while', 'where', 'when',
                      'that', 'which', 'who', 'whom', 'whose', 'what', 'this',
                      'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our',
                      'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it',
                      'its', 'they', 'them', 'their', 'there', 'here', 'then'}
        return [t for t in tokens if t not in stop_words and len(t) > 1]
    
    def _compute_tf(self, tokens):
        """Compute term frequency"""
        token_count = Counter(tokens)
        total_tokens = len(tokens)
        if total_tokens == 0:
            return {}
        return {token: count / total_tokens for token, count in token_count.items()}
    
    def _compute_idf(self, all_documents):
        """Compute inverse document frequency"""
        N = len(all_documents)
        idf = {}
        all_tokens = set()
        for doc in all_documents:
            all_tokens.update(doc.keys())
        
        for token in all_tokens:
            doc_count = sum(1 for doc in all_documents if token in doc)
            idf[token] = math.log(N / (doc_count + 1)) + 1
        
        return idf
    
    def _compute_tf_idf(self, tf, idf):
        """Compute TF-IDF vector"""
        return {token: tf.get(token, 0) * idf.get(token, 0) for token in set(tf) | set(idf)}
    
    def _cosine_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors"""
        all_keys = set(vec1.keys()) | set(vec2.keys())
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
        magnitude1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        magnitude2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        return dot_product / (magnitude1 * magnitude2)
    
    def _extract_params(self, user_query, template):
        """Extract parameters from user query based on template pattern"""
        params = {}
        
        # Extract month (numeric or name)
        month_patterns = [
            r'(\d{1,2})\s*/\s*(\d{4})',  # MM/YYYY or MM/YY
            r'(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)[a-z]*\s+(\d{4})',  # Month name YYYY
        ]
        
        # Extract amount
        amount_pattern = r'(?:\$|₹|Rs\.?\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        
        # Try to find month/year
        for pattern in month_patterns:
            match = re.search(pattern, user_query, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2 and match.group(2):
                    params['month'] = int(match.group(1))
                    params['year'] = int(match.group(2))
                break
        
        # Try to find amount
        amount_match = re.search(amount_pattern, user_query, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            params['amount'] = float(amount_str)
        
        # Set defaults if not found
        if 'month' not in params:
            from datetime import datetime
            params['month'] = datetime.now().month
        if 'year' not in params:
            from datetime import datetime
            params['year'] = datetime.now().year
        
        return params
    
    def find_best_match(self, user_query, threshold=0.15):
        """
        Find the best matching prompt-SQL pair for a user query
        Uses multiple matching strategies: keyword overlap, template matching, and TF-IDF similarity
        Returns: (match_dict, params_dict, similarity_score) or (None, None, 0)
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get all prompt-SQL pairs
        cursor.execute("SELECT * FROM prompt_sql_pairs ORDER BY category, id")
        pairs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not pairs:
            return None, None, 0
        
        # Normalize user query
        user_query_lower = user_query.lower()
        user_tokens = self._tokenize(user_query)
        user_keyword_set = set(user_tokens)
        
        # Find best match using multiple strategies
        best_match = None
        best_score = 0
        
        for pair in pairs:
            scores = []
            
            # Strategy 1: Direct keyword overlap with prompt_keywords
            pair_keywords_tokens = self._tokenize(pair['prompt_keywords'])
            pair_keyword_set = set(pair_keywords_tokens)
            keyword_overlap = len(user_keyword_set & pair_keyword_set)
            if keyword_overlap > 0:
                scores.append(min(keyword_overlap * 0.25, 0.8))  # Boost for keyword matches, capped at 0.8
            
            # Strategy 2: Check against all template variations
            templates = pair['prompt_template'].split('|')
            template_scores = []
            for template in templates:
                template_lower = template.lower()
                template_tokens = self._tokenize(template)
                template_set = set(template_tokens)
                
                # Calculate overlap with template
                template_overlap = len(user_keyword_set & template_set)
                if template_overlap > 0:
                    template_scores.append(template_overlap / max(len(user_keyword_set), len(template_set)))
            
            if template_scores:
                scores.append(max(template_scores) * 0.9)  # High weight for template match
            
            # Strategy 3: Check for exact phrase matches in templates
            for template in templates:
                template_lower = template.lower()
                # Remove parameter placeholders for matching
                template_clean = re.sub(r'\{[^}]+\}', '', template_lower).strip()
                if template_clean and len(template_clean) > 5:
                    # Check if user's query contains significant parts of the template
                    template_parts = [p.strip() for p in template_clean.split('|')]
                    for part in template_parts:
                        if len(part) > 5 and part in user_query_lower:
                            scores.append(0.7)  # Strong match for phrase containment
                            break
            
            # Strategy 4: TF-IDF similarity (original approach, but lighter)
            if len(user_tokens) > 0 and len(pair_keywords_tokens) > 0:
                user_tf = self._compute_tf(user_tokens)
                doc_tf = self._compute_tf(pair_keywords_tokens)
                
                # Simple cosine similarity on raw TF (without IDF for speed)
                all_keys = set(user_tf.keys()) | set(doc_tf.keys())
                if all_keys:
                    dot_product = sum(user_tf.get(k, 0) * doc_tf.get(k, 0) for k in all_keys)
                    magnitude1 = math.sqrt(sum(v ** 2 for v in user_tf.values()))
                    magnitude2 = math.sqrt(sum(v ** 2 for v in doc_tf.values()))
                    if magnitude1 > 0 and magnitude2 > 0:
                        tf_similarity = dot_product / (magnitude1 * magnitude2)
                        scores.append(tf_similarity * 0.5)  # Lower weight for TF-IDF
            
            # Calculate final score (use max of all strategies, with small boost for multiple matches)
            if scores:
                final_score = max(scores) + (len([s for s in scores if s > 0.3]) * 0.05)
            else:
                final_score = 0
            
            if final_score > best_score:
                best_score = final_score
                best_match = pair
        
        if best_match and best_score >= threshold:
            # Extract parameters from user query
            params = self._extract_params(user_query, best_match['prompt_template'])
            return best_match, params, best_score
        
        return None, None, best_score
    
    def format_sql_query(self, sql_template, params):
        """Format SQL query with extracted parameters"""
        try:
            # Handle zero-padding for month
            if 'month' in params:
                params['month:02d'] = f"{params['month']:02d}"
            return sql_template.format(**params)
        except (KeyError, ValueError) as e:
            # If formatting fails, return template with available params
            result = sql_template
            for key, value in params.items():
                if ':02d' not in key:
                    result = result.replace(f'{{{key}}}', str(value))
            return result
    
    def get_all_prompts(self, category=None):
        """Get all available prompts, optionally filtered by category"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("SELECT * FROM prompt_sql_pairs WHERE category = ? ORDER BY category, id", (category,))
        else:
            cursor.execute("SELECT * FROM prompt_sql_pairs ORDER BY category, id")
        
        pairs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return pairs


def get_chat_history(db_path, user_id, session_id=None, limit=50):
    """Get chat history for a user, optionally filtered by session"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute('''
            SELECT * FROM chat_history 
            WHERE user_id = ? AND session_id = ? 
            ORDER BY timestamp ASC 
            LIMIT ?
        ''', (user_id, session_id, limit))
    else:
        # Get unique sessions
        cursor.execute('''
            SELECT DISTINCT session_id, MAX(timestamp) as last_message_time,
                   (SELECT message FROM chat_history WHERE session_id = ch.session_id ORDER BY timestamp DESC LIMIT 1) as last_message
            FROM chat_history ch
            WHERE user_id = ?
            GROUP BY session_id
            ORDER BY last_message_time DESC
        ''', (user_id,))
    
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


def save_chat_message(db_path, user_id, session_id, message_type, message, sql_query=None, query_results=None):
    """Save a chat message to history"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_history (user_id, session_id, message_type, message, sql_query, query_results)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, session_id, message_type, message, sql_query, 
          query_results if isinstance(query_results, str) else (str(query_results) if query_results else None)))
    
    conn.commit()
    conn.close()


def get_or_create_session(db_path, user_id, session_id=None):
    """Get existing session or create new one"""
    if session_id:
        # Verify session exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM chat_history WHERE user_id = ? AND session_id = ? LIMIT 1',
                      (user_id, session_id))
        exists = cursor.fetchone()
        conn.close()
        if exists:
            return session_id
    
    # Create new session
    import uuid
    return str(uuid.uuid4())[:8]
