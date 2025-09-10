"""
AI-powered services for intelligent communication and feedback system.
"""

import openai
import logging
import re
from typing import Dict, List, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from textblob import TextBlob
import requests
import json
from datetime import datetime, timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


class AIFeedbackService:
    """
    Service for AI-powered feedback generation and content assistance.
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        self.model = "gpt-3.5-turbo"
    
    def generate_forum_summary(self, forum_id: str) -> Dict[str, Any]:
        """
        Generate AI summary of forum discussions.
        
        Args:
            forum_id: ID of the forum to summarize
            
        Returns:
            Dict containing summary and insights
        """
        try:
            # In a real implementation, you'd fetch actual forum posts
            # For now, we'll simulate the process
            
            sample_posts = [
                "I'm having trouble understanding the concept of recursion in Python.",
                "Great explanation! The tree traversal example really helped.",
                "Can someone explain the time complexity of this algorithm?",
                "Here's a visual representation that might help with understanding.",
                "I think there might be an error in the sample code provided."
            ]
            
            prompt = f"""
            Please analyze the following forum discussion posts and provide:
            1. A concise summary of the main topics discussed
            2. Key insights about student understanding and engagement
            3. Suggestions for instructor follow-up
            
            Posts to analyze:
            {chr(10).join(f'- {post}' for post in sample_posts)}
            
            Format the response as JSON with keys: summary, insights, suggestions
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational AI assistant analyzing forum discussions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'summary': result.get('summary', ''),
                'key_insights': result.get('insights', []),
                'instructor_suggestions': result.get('suggestions', []),
                'engagement_metrics': {
                    'total_posts': len(sample_posts),
                    'unique_topics': 3,
                    'help_requests': 2,
                    'peer_responses': 2
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forum summary generation failed: {e}")
            return {
                'summary': 'Unable to generate summary at this time.',
                'key_insights': [],
                'instructor_suggestions': [],
                'error': str(e)
            }
    
    def generate_response_suggestions(self, post_content: str, topic_title: str, user) -> List[Dict[str, str]]:
        """
        Generate AI-suggested responses to forum posts.
        
        Args:
            post_content: Content of the post to respond to
            topic_title: Title of the forum topic
            user: User requesting suggestions
            
        Returns:
            List of suggested responses with different tones
        """
        try:
            prompt = f"""
            A student has posted the following in a forum about "{topic_title}":
            "{post_content}"
            
            Generate 3 different response suggestions:
            1. A helpful/supportive response
            2. A clarifying question response
            3. A resource-sharing response
            
            Each response should be appropriate for an educational context and encourage learning.
            Format as JSON array with objects containing 'type', 'content', and 'tone' fields.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational AI assistant helping with forum responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            
            suggestions = json.loads(response.choices[0].message.content)
            
            # Add metadata to each suggestion
            for suggestion in suggestions:
                suggestion['generated_at'] = datetime.now().isoformat()
                suggestion['confidence'] = 0.85  # Simulated confidence score
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Response suggestion generation failed: {e}")
            return [{
                'type': 'supportive',
                'content': 'Thank you for sharing your thoughts! This is an interesting point that others might also find helpful.',
                'tone': 'encouraging',
                'error': str(e)
            }]
    
    def suggest_message_improvements(self, message_content: str, context: Dict) -> Dict[str, Any]:
        """
        Suggest improvements for direct messages based on tone and context.
        
        Args:
            message_content: Content of the message
            context: Context including relationship, history, etc.
            
        Returns:
            Dict containing improvement suggestions
        """
        try:
            relationship = context.get('relationship', 'peer')
            
            prompt = f"""
            Analyze this message and suggest improvements for tone, clarity, and appropriateness:
            
            Message: "{message_content}"
            Relationship: {relationship}
            
            Provide suggestions for:
            1. Tone adjustment (if needed)
            2. Clarity improvements
            3. Professional appropriateness
            4. Overall effectiveness
            
            Format as JSON with 'tone_score', 'clarity_score', 'suggestions', and 'improved_version' fields.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a communication AI assistant helping improve message quality."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=300
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Message improvement suggestion failed: {e}")
            return {
                'tone_score': 7.0,
                'clarity_score': 7.5,
                'suggestions': ['Message appears clear and appropriate.'],
                'improved_version': message_content,
                'error': str(e)
            }
    
    def provide_composition_assistance(self, draft_content: str, message_type: str, recipient_id: Optional[str]) -> Dict[str, Any]:
        """
        Provide AI assistance for composing messages.
        
        Args:
            draft_content: Current draft of the message
            message_type: Type of message (formal, casual, academic, etc.)
            recipient_id: ID of message recipient for context
            
        Returns:
            Dict containing composition assistance
        """
        try:
            prompt = f"""
            Help improve this {message_type} message draft:
            
            Current draft: "{draft_content}"
            
            Provide:
            1. Structure suggestions
            2. Tone recommendations
            3. Content enhancements
            4. Professional language alternatives
            
            Format as JSON with 'structure', 'tone_advice', 'content_suggestions', and 'alternatives' fields.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a writing assistant helping compose effective messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Composition assistance failed: {e}")
            return {
                'structure': 'Your message structure looks good.',
                'tone_advice': 'Maintain a professional and friendly tone.',
                'content_suggestions': ['Consider adding more specific details.'],
                'alternatives': [],
                'error': str(e)
            }
    
    def generate_automated_response(self, original_message: str, response_type: str, context: Dict, user) -> Dict[str, Any]:
        """
        Generate fully automated responses for common inquiries.
        
        Args:
            original_message: The message to respond to
            response_type: Type of response needed
            context: Additional context
            user: User generating the response
            
        Returns:
            Dict containing the automated response
        """
        try:
            prompt = f"""
            Generate an automated {response_type} response to this message:
            
            Original message: "{original_message}"
            
            The response should be:
            - Professional and helpful
            - Concise but informative
            - Appropriate for an educational context
            
            Include follow-up suggestions if applicable.
            Format as JSON with 'response', 'follow_up_actions', and 'confidence_level' fields.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an educational AI assistant generating automated responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=250
            )
            
            result = json.loads(response.choices[0].message.content)
            result['generated_by'] = 'AI Assistant'
            result['generated_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Automated response generation failed: {e}")
            return {
                'response': 'Thank you for your message. We\'ll get back to you soon.',
                'follow_up_actions': ['Human review recommended'],
                'confidence_level': 0.5,
                'error': str(e)
            }


class SentimentAnalysisService:
    """
    Service for sentiment analysis and emotional intelligence in communications.
    """
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict containing sentiment analysis results
        """
        try:
            blob = TextBlob(text)
            
            # Extract key topics using simple keyword extraction
            words = blob.words
            key_topics = [word.lower() for word in words if len(word) > 4 and word.isalpha()][:5]
            
            return {
                'sentiment_score': blob.sentiment.polarity,  # -1 to 1
                'subjectivity': blob.sentiment.subjectivity,  # 0 to 1
                'key_topics': key_topics,
                'word_count': len(words),
                'emotional_indicators': self._extract_emotional_indicators(text),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                'sentiment_score': 0.0,
                'subjectivity': 0.5,
                'key_topics': [],
                'word_count': 0,
                'emotional_indicators': [],
                'error': str(e)
            }
    
    def analyze_forum_sentiment(self, posts) -> Dict[str, Any]:
        """
        Analyze sentiment across multiple forum posts.
        
        Args:
            posts: QuerySet or list of forum posts
            
        Returns:
            Dict containing aggregate sentiment analysis
        """
        try:
            sentiments = []
            topics = []
            emotional_indicators = []
            
            for post in posts:
                analysis = self.analyze_text(post.content)
                sentiments.append(analysis['sentiment_score'])
                topics.extend(analysis['key_topics'])
                emotional_indicators.extend(analysis['emotional_indicators'])
            
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Count topic frequencies
            topic_counts = {}
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'average_sentiment': avg_sentiment,
                'sentiment_distribution': self._categorize_sentiment(sentiments),
                'total_posts': len(posts),
                'top_topics': top_topics,
                'emotional_indicators': list(set(emotional_indicators)),
                'engagement_level': self._calculate_engagement_level(posts),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forum sentiment analysis failed: {e}")
            return {
                'average_sentiment': 0.0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'total_posts': 0,
                'top_topics': [],
                'emotional_indicators': [],
                'engagement_level': 'unknown',
                'error': str(e)
            }
    
    def analyze_chat_sentiment(self, messages) -> Dict[str, Any]:
        """
        Analyze real-time sentiment in chat messages.
        
        Args:
            messages: QuerySet or list of chat messages
            
        Returns:
            Dict containing real-time sentiment analysis
        """
        try:
            recent_sentiments = []
            message_velocities = []
            
            for message in messages:
                analysis = self.analyze_text(message.content)
                recent_sentiments.append({
                    'timestamp': message.sent_at.isoformat(),
                    'sentiment': analysis['sentiment_score'],
                    'sender': message.sender.username
                })
            
            # Calculate sentiment trend
            if len(recent_sentiments) >= 2:
                trend = recent_sentiments[-1]['sentiment'] - recent_sentiments[0]['sentiment']
            else:
                trend = 0
            
            return {
                'current_sentiment': recent_sentiments[-1]['sentiment'] if recent_sentiments else 0,
                'sentiment_trend': trend,
                'message_count': len(messages),
                'active_participants': len(set(msg.sender.username for msg in messages)),
                'sentiment_timeline': recent_sentiments,
                'conversation_health': self._assess_conversation_health(recent_sentiments),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat sentiment analysis failed: {e}")
            return {
                'current_sentiment': 0.0,
                'sentiment_trend': 0.0,
                'message_count': 0,
                'active_participants': 0,
                'sentiment_timeline': [],
                'conversation_health': 'unknown',
                'error': str(e)
            }
    
    def analyze_communication_tone(self, message_content: str) -> Dict[str, Any]:
        """
        Analyze tone of communication for message assistance.
        
        Args:
            message_content: Content to analyze
            
        Returns:
            Dict containing tone analysis
        """
        try:
            analysis = self.analyze_text(message_content)
            
            # Determine primary tone
            sentiment_score = analysis['sentiment_score']
            subjectivity = analysis['subjectivity']
            
            if sentiment_score > 0.3:
                primary_tone = 'positive'
            elif sentiment_score < -0.3:
                primary_tone = 'negative'
            else:
                primary_tone = 'neutral'
            
            # Determine communication style
            if subjectivity > 0.7:
                communication_style = 'subjective'
            elif subjectivity < 0.3:
                communication_style = 'objective'
            else:
                communication_style = 'balanced'
            
            return {
                'primary_tone': primary_tone,
                'communication_style': communication_style,
                'formality_level': self._assess_formality(message_content),
                'emotional_intensity': abs(sentiment_score),
                'suggestions': self._generate_tone_suggestions(primary_tone, communication_style),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Communication tone analysis failed: {e}")
            return {
                'primary_tone': 'neutral',
                'communication_style': 'balanced',
                'formality_level': 'moderate',
                'emotional_intensity': 0.0,
                'suggestions': [],
                'error': str(e)
            }
    
    def _extract_emotional_indicators(self, text: str) -> List[str]:
        """Extract emotional indicators from text."""
        emotional_words = {
            'positive': ['happy', 'excited', 'great', 'awesome', 'excellent', 'love', 'amazing'],
            'negative': ['sad', 'angry', 'frustrated', 'confused', 'difficult', 'hate', 'terrible'],
            'uncertainty': ['maybe', 'possibly', 'confused', 'unsure', 'think', 'might'],
            'urgency': ['urgent', 'asap', 'immediately', 'quickly', 'deadline', 'rush']
        }
        
        indicators = []
        text_lower = text.lower()
        
        for category, words in emotional_words.items():
            for word in words:
                if word in text_lower:
                    indicators.append(category)
                    break
        
        return indicators
    
    def _categorize_sentiment(self, sentiments: List[float]) -> Dict[str, int]:
        """Categorize sentiment scores into positive, neutral, negative."""
        categories = {'positive': 0, 'neutral': 0, 'negative': 0}
        
        for sentiment in sentiments:
            if sentiment > 0.1:
                categories['positive'] += 1
            elif sentiment < -0.1:
                categories['negative'] += 1
            else:
                categories['neutral'] += 1
        
        return categories
    
    def _calculate_engagement_level(self, posts) -> str:
        """Calculate overall engagement level of forum posts."""
        if not posts:
            return 'low'
        
        # Simple heuristic based on post count and recency
        recent_posts = [p for p in posts if p.created_at > datetime.now() - timedelta(days=7)]
        engagement_ratio = len(recent_posts) / len(posts) if posts else 0
        
        if engagement_ratio > 0.6:
            return 'high'
        elif engagement_ratio > 0.3:
            return 'moderate'
        else:
            return 'low'
    
    def _assess_conversation_health(self, sentiment_timeline: List[Dict]) -> str:
        """Assess overall health of conversation based on sentiment patterns."""
        if not sentiment_timeline:
            return 'unknown'
        
        avg_sentiment = sum(s['sentiment'] for s in sentiment_timeline) / len(sentiment_timeline)
        
        if avg_sentiment > 0.2:
            return 'healthy'
        elif avg_sentiment > -0.2:
            return 'neutral'
        else:
            return 'concerning'
    
    def _assess_formality(self, text: str) -> str:
        """Assess formality level of text."""
        informal_indicators = ['lol', 'btw', 'ur', 'pls', '😊', '!']
        formal_indicators = ['therefore', 'furthermore', 'consequently', 'sincerely']
        
        text_lower = text.lower()
        informal_count = sum(1 for indicator in informal_indicators if indicator in text_lower)
        formal_count = sum(1 for indicator in formal_indicators if indicator in text_lower)
        
        if formal_count > informal_count:
            return 'formal'
        elif informal_count > formal_count:
            return 'informal'
        else:
            return 'moderate'
    
    def _generate_tone_suggestions(self, tone: str, style: str) -> List[str]:
        """Generate suggestions based on tone and style analysis."""
        suggestions = []
        
        if tone == 'negative':
            suggestions.append('Consider using more positive language')
            suggestions.append('Try reframing concerns constructively')
        
        if style == 'subjective':
            suggestions.append('Consider adding objective facts to support your points')
        
        if style == 'objective':
            suggestions.append('Consider adding personal perspective for engagement')
        
        return suggestions


class EmailProcessingService:
    """
    Service for processing and analyzing incoming emails.
    """
    
    def __init__(self):
        self.sentiment_service = SentimentAnalysisService()
        self.ai_service = AIFeedbackService()
    
    def process_incoming_email(self, email_content: str, sender_email: str, subject: str) -> Dict[str, Any]:
        """
        Process incoming email with AI analysis and response generation.
        
        Args:
            email_content: Content of the email
            sender_email: Email address of sender
            subject: Subject line
            
        Returns:
            Dict containing processing results
        """
        try:
            # Analyze email content
            sentiment_analysis = self.sentiment_service.analyze_text(email_content)
            
            # Categorize email type
            email_category = self._categorize_email(subject, email_content)
            
            # Generate response suggestions
            response_suggestions = self._generate_email_responses(
                email_content, email_category, sentiment_analysis
            )
            
            # Extract action items
            action_items = self._extract_action_items(email_content)
            
            return {
                'sender_email': sender_email,
                'subject': subject,
                'category': email_category,
                'sentiment_analysis': sentiment_analysis,
                'response_suggestions': response_suggestions,
                'action_items': action_items,
                'priority_level': self._assess_priority(subject, email_content, sentiment_analysis),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email processing failed: {e}")
            return {
                'sender_email': sender_email,
                'subject': subject,
                'category': 'general',
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }
    
    def _categorize_email(self, subject: str, content: str) -> str:
        """Categorize email based on subject and content."""
        subject_lower = subject.lower()
        content_lower = content.lower()
        
        if any(word in subject_lower or word in content_lower for word in ['urgent', 'asap', 'deadline']):
            return 'urgent'
        elif any(word in subject_lower or word in content_lower for word in ['question', 'help', 'confused']):
            return 'support_request'
        elif any(word in subject_lower or word in content_lower for word in ['feedback', 'review', 'opinion']):
            return 'feedback'
        elif any(word in subject_lower or word in content_lower for word in ['assignment', 'homework', 'project']):
            return 'academic'
        else:
            return 'general'
    
    def _generate_email_responses(self, content: str, category: str, sentiment: Dict) -> List[Dict[str, str]]:
        """Generate appropriate email responses based on content and sentiment."""
        responses = []
        
        if category == 'urgent':
            responses.append({
                'type': 'acknowledgment',
                'content': 'Thank you for your urgent message. I understand the importance of this matter and will address it promptly.',
                'tone': 'professional'
            })
        
        if category == 'support_request':
            responses.append({
                'type': 'helpful',
                'content': 'Thank you for reaching out. I\'m happy to help you with this. Let me provide some guidance.',
                'tone': 'supportive'
            })
        
        if sentiment['sentiment_score'] < -0.3:  # Negative sentiment
            responses.append({
                'type': 'empathetic',
                'content': 'I understand your concerns and want to help resolve this issue. Your feedback is valuable.',
                'tone': 'empathetic'
            })
        
        return responses
    
    def _extract_action_items(self, content: str) -> List[str]:
        """Extract potential action items from email content."""
        action_indicators = ['need to', 'should', 'must', 'deadline', 'by', 'schedule', 'arrange']
        sentences = content.split('.')
        
        action_items = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in action_indicators):
                action_items.append(sentence.strip())
        
        return action_items[:5]  # Limit to top 5 action items
    
    def _assess_priority(self, subject: str, content: str, sentiment: Dict) -> str:
        """Assess priority level of email."""
        high_priority_indicators = ['urgent', 'asap', 'deadline', 'emergency']
        medium_priority_indicators = ['soon', 'important', 'need']
        
        combined_text = (subject + ' ' + content).lower()
        
        if any(indicator in combined_text for indicator in high_priority_indicators):
            return 'high'
        elif any(indicator in combined_text for indicator in medium_priority_indicators):
            return 'medium'
        elif sentiment['sentiment_score'] < -0.5:  # Very negative sentiment
            return 'medium'
        else:
            return 'low'


class AutoModerationService:
    """
    Service for automated content moderation using AI.
    """
    
    def moderate_content(self, content: str) -> Dict[str, Any]:
        """
        Moderate content for appropriateness and toxicity.
        
        Args:
            content: Content to moderate
            
        Returns:
            Dict containing moderation results
        """
        try:
            # Simple rule-based moderation (in production, use more sophisticated AI)
            flagged_words = ['spam', 'inappropriate', 'offensive']  # Simplified list
            
            content_lower = content.lower()
            toxicity_score = 0.0
            flags = []
            
            # Check for flagged words
            for word in flagged_words:
                if word in content_lower:
                    toxicity_score += 0.3
                    flags.append(f"Contains flagged word: {word}")
            
            # Check for excessive capitalization
            if sum(1 for c in content if c.isupper()) > len(content) * 0.7:
                toxicity_score += 0.2
                flags.append("Excessive capitalization")
            
            # Check for repetitive content
            words = content.split()
            if len(set(words)) < len(words) * 0.3:
                toxicity_score += 0.1
                flags.append("Repetitive content")
            
            requires_moderation = toxicity_score > 0.5
            
            return {
                'toxicity_score': min(toxicity_score, 1.0),
                'requires_moderation': requires_moderation,
                'flags': flags,
                'confidence': 0.8,
                'reason': '; '.join(flags) if flags else None,
                'moderated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content moderation failed: {e}")
            return {
                'toxicity_score': 0.0,
                'requires_moderation': False,
                'flags': [],
                'confidence': 0.0,
                'reason': None,
                'error': str(e)
            }
    
    def moderate_chat_conversation(self, messages) -> Dict[str, Any]:
        """
        Moderate entire chat conversation.
        
        Args:
            messages: QuerySet or list of chat messages
            
        Returns:
            Dict containing conversation moderation results
        """
        try:
            moderation_results = []
            total_toxicity = 0.0
            flagged_messages = 0
            
            for message in messages:
                result = self.moderate_content(message.content)
                if result['requires_moderation']:
                    moderation_results.append({
                        'message_id': str(message.id),
                        'sender': message.sender.username,
                        'moderation_result': result,
                        'timestamp': message.sent_at.isoformat()
                    })
                    flagged_messages += 1
                
                total_toxicity += result['toxicity_score']
            
            average_toxicity = total_toxicity / len(messages) if messages else 0
            
            return {
                'total_messages': len(messages),
                'flagged_messages': flagged_messages,
                'average_toxicity': average_toxicity,
                'flagged_content': moderation_results,
                'conversation_health': 'healthy' if average_toxicity < 0.3 else 'concerning',
                'recommendations': self._generate_moderation_recommendations(average_toxicity, flagged_messages),
                'moderated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Conversation moderation failed: {e}")
            return {
                'total_messages': 0,
                'flagged_messages': 0,
                'average_toxicity': 0.0,
                'flagged_content': [],
                'conversation_health': 'unknown',
                'recommendations': [],
                'error': str(e)
            }
    
    def _generate_moderation_recommendations(self, avg_toxicity: float, flagged_count: int) -> List[str]:
        """Generate recommendations based on moderation results."""
        recommendations = []
        
        if avg_toxicity > 0.7:
            recommendations.append("Consider implementing stricter moderation policies")
            recommendations.append("Review conversation guidelines with participants")
        
        if flagged_count > 5:
            recommendations.append("Increase moderator presence in this conversation")
            recommendations.append("Consider temporary restrictions for repeat offenders")
        
        if avg_toxicity > 0.5:
            recommendations.append("Provide positive communication training")
        
        return recommendations
