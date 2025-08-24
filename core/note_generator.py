"""
AI-powered note generation for the Nabu application.
Analyzes conversations and generates both internal and user-facing notes.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

from utils.logger import get_logger
from data.database import DatabaseManager
from config import config


@dataclass
class ConversationAnalysis:
    """Analysis results from a conversation."""
    session_id: str
    language: str
    duration_minutes: float
    total_messages: int
    user_messages: int
    ai_messages: int
    topics_discussed: List[str]
    vocabulary_used: List[str]
    new_vocabulary: List[str]
    grammar_corrections: List[Dict[str, Any]]
    pronunciation_notes: List[str]
    cultural_insights: List[str]
    learning_progress: Dict[str, Any]
    difficulty_level: float
    engagement_score: float


@dataclass
class GeneratedNote:
    """A generated note for the user."""
    title: str
    content: str
    category: str
    priority: int  # 1=Low, 2=Medium, 3=High
    tags: str
    language: str
    session_id: str
    created_at: datetime


class NoteGenerator:
    """Generates notes from conversation analysis."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = get_logger(__name__)
    
    def analyze_conversation(self, session_id: str, messages: List[Dict[str, Any]], language: str) -> ConversationAnalysis:
        """Analyze a conversation and extract insights."""
        self.logger.info(f"Analyzing conversation for session: {session_id}")
        
        # Extract basic statistics
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.get('sender') == 'user'])
        ai_messages = len([m for m in messages if m.get('sender') == 'ai'])
        
        # Extract vocabulary and topics
        vocabulary_used = self._extract_vocabulary(messages, language)
        topics_discussed = self._extract_topics(messages)
        new_vocabulary = self._identify_new_vocabulary(vocabulary_used, language)
        grammar_corrections = self._extract_grammar_corrections(messages)
        pronunciation_notes = self._extract_pronunciation_notes(messages)
        cultural_insights = self._extract_cultural_insights(messages)
        
        # Calculate learning progress
        learning_progress = self._calculate_learning_progress(messages, vocabulary_used)
        
        # Estimate difficulty and engagement
        difficulty_level = self._estimate_difficulty_level(messages, vocabulary_used)
        engagement_score = self._calculate_engagement_score(messages)
        
        return ConversationAnalysis(
            session_id=session_id,
            language=language,
            duration_minutes=0.0,  # Will be set by caller
            total_messages=total_messages,
            user_messages=user_messages,
            ai_messages=ai_messages,
            topics_discussed=topics_discussed,
            vocabulary_used=vocabulary_used,
            new_vocabulary=new_vocabulary,
            grammar_corrections=grammar_corrections,
            pronunciation_notes=pronunciation_notes,
            cultural_insights=cultural_insights,
            learning_progress=learning_progress,
            difficulty_level=difficulty_level,
            engagement_score=engagement_score
        )
    
    def generate_notes(self, analysis: ConversationAnalysis) -> List[GeneratedNote]:
        """Generate user-facing notes from conversation analysis."""
        notes = []
        
        # Generate vocabulary note
        if analysis.new_vocabulary:
            vocab_note = self._generate_vocabulary_note(analysis)
            notes.append(vocab_note)
        
        # Generate grammar note
        if analysis.grammar_corrections:
            grammar_note = self._generate_grammar_note(analysis)
            notes.append(grammar_note)
        
        # Generate pronunciation note
        if analysis.pronunciation_notes:
            pronunciation_note = self._generate_pronunciation_note(analysis)
            notes.append(pronunciation_note)
        
        # Generate cultural note
        if analysis.cultural_insights:
            cultural_note = self._generate_cultural_note(analysis)
            notes.append(cultural_note)
        
        # Generate progress summary note
        progress_note = self._generate_progress_note(analysis)
        notes.append(progress_note)
        
        return notes
    
    def save_notes(self, notes: List[GeneratedNote]) -> None:
        """Save generated notes to the database."""
        for note in notes:
            try:
                self.db.insert('user_notes', {
                    'title': note.title,
                    'content': note.content,
                    'category': note.category,
                    'language': note.language,
                    'priority': note.priority,
                    'tags': note.tags,
                    'created_at': note.created_at.isoformat(),
                    'updated_at': note.created_at.isoformat(),
                    'archived': 0
                })
                self.logger.info(f"Saved note: {note.title}")
            except Exception as e:
                self.logger.error(f"Error saving note {note.title}: {e}")
    
    def _extract_vocabulary(self, messages: List[Dict[str, Any]], language: str) -> List[str]:
        """Extract vocabulary words from messages."""
        vocabulary = set()
        
        # Language-specific word extraction patterns
        if language == 'ru':
            # Russian word pattern (Cyrillic characters)
            pattern = r'\b[а-яё]+\b'
        elif language == 'es':
            # Spanish word pattern
            pattern = r'\b[a-záéíóúñü]+\b'
        elif language == 'fr':
            # French word pattern
            pattern = r'\b[a-zàâäéèêëïîôöùûüÿç]+\b'
        elif language == 'de':
            # German word pattern
            pattern = r'\b[a-zäöüß]+\b'
        elif language == 'ja':
            # Japanese word pattern (hiragana, katakana, kanji)
            pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'
        elif language == 'zh':
            # Chinese word pattern (simplified/traditional)
            pattern = r'[\u4E00-\u9FFF]+'
        else:
            # Default: English-like pattern
            pattern = r'\b[a-z]+\b'
        
        for message in messages:
            text = message.get('text', '').lower()
            words = re.findall(pattern, text)
            # Filter out common words and short words
            filtered_words = [word for word in words if len(word) > 2 and word not in self._get_common_words(language)]
            vocabulary.update(filtered_words)
        
        return list(vocabulary)
    
    def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract discussion topics from messages."""
        topics = []
        
        # Simple topic extraction based on keywords
        topic_keywords = {
            'food': ['food', 'eat', 'restaurant', 'cooking', 'meal', 'hungry'],
            'travel': ['travel', 'vacation', 'trip', 'visit', 'tourist', 'hotel'],
            'work': ['work', 'job', 'office', 'meeting', 'project', 'career'],
            'family': ['family', 'mother', 'father', 'sister', 'brother', 'parents'],
            'hobbies': ['hobby', 'sport', 'music', 'reading', 'painting', 'gaming'],
            'weather': ['weather', 'sunny', 'rainy', 'cold', 'hot', 'temperature'],
            'shopping': ['shop', 'buy', 'store', 'market', 'purchase', 'price']
        }
        
        all_text = ' '.join([m.get('text', '').lower() for m in messages])
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _identify_new_vocabulary(self, vocabulary: List[str], language: str) -> List[str]:
        """Identify new vocabulary words by checking against existing database."""
        try:
            # Get existing vocabulary from database
            query = "SELECT word FROM vocabulary WHERE language = ?"
            existing_words = {row[0].lower() for row in self.db.execute_query(query, (language,))}
            
            # Find new words
            new_words = [word for word in vocabulary if word.lower() not in existing_words]
            return new_words[:10]  # Limit to top 10 new words
        except Exception as e:
            self.logger.error(f"Error identifying new vocabulary: {e}")
            return vocabulary[:5]  # Return first 5 words as fallback
    
    def _extract_grammar_corrections(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract grammar corrections from AI messages."""
        corrections = []
        
        for message in messages:
            if message.get('sender') == 'ai':
                text = message.get('text', '')
                # Look for correction patterns
                if any(phrase in text.lower() for phrase in ['correction', 'should be', 'correct form', 'grammar']):
                    corrections.append({
                        'original': 'extracted_original',
                        'corrected': 'extracted_correction',
                        'explanation': text[:200]  # First 200 chars as explanation
                    })
        
        return corrections
    
    def _extract_pronunciation_notes(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract pronunciation notes from AI messages."""
        notes = []
        
        for message in messages:
            if message.get('sender') == 'ai':
                text = message.get('text', '')
                # Look for pronunciation-related content
                if any(phrase in text.lower() for phrase in ['pronunciation', 'sound', 'accent', 'stress']):
                    notes.append(text[:150])  # First 150 chars
        
        return notes
    
    def _extract_cultural_insights(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract cultural insights from AI messages."""
        insights = []
        
        for message in messages:
            if message.get('sender') == 'ai':
                text = message.get('text', '')
                # Look for cultural content
                if any(phrase in text.lower() for phrase in ['culture', 'tradition', 'custom', 'history', 'society']):
                    insights.append(text[:150])  # First 150 chars
        
        return insights
    
    def _calculate_learning_progress(self, messages: List[Dict[str, Any]], vocabulary: List[str]) -> Dict[str, Any]:
        """Calculate learning progress metrics."""
        return {
            'vocabulary_count': len(vocabulary),
            'conversation_length': len(messages),
            'interaction_ratio': len([m for m in messages if m.get('sender') == 'user']) / max(len(messages), 1),
            'complexity_score': self._calculate_complexity_score(messages)
        }
    
    def _estimate_difficulty_level(self, messages: List[Dict[str, Any]], vocabulary: List[str]) -> float:
        """Estimate the difficulty level of the conversation."""
        # Simple heuristic based on vocabulary size and message complexity
        vocab_score = min(len(vocabulary) / 10.0, 1.0)  # Normalize to 0-1
        complexity_score = self._calculate_complexity_score(messages)
        return (vocab_score + complexity_score) / 2.0
    
    def _calculate_engagement_score(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate engagement score based on conversation patterns."""
        if not messages:
            return 0.0
        
        user_messages = [m for m in messages if m.get('sender') == 'user']
        avg_user_length = sum(len(m.get('text', '')) for m in user_messages) / max(len(user_messages), 1)
        
        # Normalize engagement score (0-1)
        engagement = min(avg_user_length / 50.0, 1.0)  # Assume 50 chars is high engagement
        return engagement
    
    def _calculate_complexity_score(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate complexity score of messages."""
        if not messages:
            return 0.0
        
        total_length = sum(len(m.get('text', '')) for m in messages)
        avg_length = total_length / len(messages)
        
        # Normalize complexity score (0-1)
        complexity = min(avg_length / 100.0, 1.0)  # Assume 100 chars is high complexity
        return complexity
    
    def _get_common_words(self, language: str) -> set:
        """Get common words for a language to filter out."""
        common_words = {
            'ru': {'и', 'в', 'не', 'на', 'я', 'быть', 'он', 'что', 'это', 'как'},
            'es': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se'},
            'fr': {'le', 'la', 'de', 'et', 'à', 'un', 'être', 'etre', 'avoir', 'il'},
            'de': {'der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu', 'mit', 'sich'},
            'en': {'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that'}
        }
        return common_words.get(language, common_words['en'])
    
    def _generate_vocabulary_note(self, analysis: ConversationAnalysis) -> GeneratedNote:
        """Generate a vocabulary note."""
        new_words = ', '.join(analysis.new_vocabulary[:5])
        title = f"New {analysis.language.upper()} Vocabulary - Session {analysis.session_id[:8]}"
        content = f"""In this conversation, you encountered {len(analysis.new_vocabulary)} new vocabulary words.

New words to practice:
{new_words}

Try to use these words in your next conversation to reinforce your learning!"""
        
        return GeneratedNote(
            title=title,
            content=content,
            category="Vocabulary",
            priority=2,
            tags=f"{analysis.language},vocabulary,new-words",
            language=analysis.language,
            session_id=analysis.session_id,
            created_at=datetime.now()
        )
    
    def _generate_grammar_note(self, analysis: ConversationAnalysis) -> GeneratedNote:
        """Generate a grammar note."""
        title = f"{analysis.language.upper()} Grammar Focus - Session {analysis.session_id[:8]}"
        content = f"""Grammar corrections and improvements from this session:

{analysis.grammar_corrections[0]['explanation'] if analysis.grammar_corrections else 'No specific grammar corrections noted.'}

Remember to review these patterns in your future conversations."""
        
        return GeneratedNote(
            title=title,
            content=content,
            category="Grammar",
            priority=2,
            tags=f"{analysis.language},grammar,corrections",
            language=analysis.language,
            session_id=analysis.session_id,
            created_at=datetime.now()
        )
    
    def _generate_pronunciation_note(self, analysis: ConversationAnalysis) -> GeneratedNote:
        """Generate a pronunciation note."""
        title = f"{analysis.language.upper()} Pronunciation Tips - Session {analysis.session_id[:8]}"
        content = f"""Pronunciation focus from this session:

{analysis.pronunciation_notes[0] if analysis.pronunciation_notes else 'No specific pronunciation notes.'}

Practice these sounds to improve your accent!"""
        
        return GeneratedNote(
            title=title,
            content=content,
            category="Pronunciation",
            priority=1,
            tags=f"{analysis.language},pronunciation,accent",
            language=analysis.language,
            session_id=analysis.session_id,
            created_at=datetime.now()
        )
    
    def _generate_cultural_note(self, analysis: ConversationAnalysis) -> GeneratedNote:
        """Generate a cultural note."""
        title = f"{analysis.language.upper()} Cultural Insights - Session {analysis.session_id[:8]}"
        content = f"""Cultural insights from this conversation:

{analysis.cultural_insights[0] if analysis.cultural_insights else 'No specific cultural insights noted.'}

Understanding cultural context helps with language learning!"""
        
        return GeneratedNote(
            title=title,
            content=content,
            category="Culture",
            priority=1,
            tags=f"{analysis.language},culture,insights",
            language=analysis.language,
            session_id=analysis.session_id,
            created_at=datetime.now()
        )
    
    def _generate_progress_note(self, analysis: ConversationAnalysis) -> GeneratedNote:
        """Generate a progress summary note."""
        title = f"{analysis.language.upper()} Learning Progress - Session {analysis.session_id[:8]}"
        content = f"""Session Summary:
- Duration: {analysis.duration_minutes:.1f} minutes
- Messages exchanged: {analysis.total_messages}
- New vocabulary: {len(analysis.new_vocabulary)} words
- Topics discussed: {', '.join(analysis.topics_discussed) if analysis.topics_discussed else 'Various topics'}
- Engagement level: {'High' if analysis.engagement_score > 0.7 else 'Medium' if analysis.engagement_score > 0.4 else 'Low'}

Keep up the great work! Your consistent practice is building your language skills."""
        
        return GeneratedNote(
            title=title,
            content=content,
            category="Progress",
            priority=1,
            tags=f"{analysis.language},progress,summary",
            language=analysis.language,
            session_id=analysis.session_id,
            created_at=datetime.now()
        )
