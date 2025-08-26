# System Prompts Documentation

## Overview
This document outlines all the AI system prompts used in the Nabu AI Language Tutor application, their locations, and their purposes.

## 1. Conversation AI Prompt

**Location:** `audio/voice_loop.py` (lines 348-375)

**Purpose:** Main conversation prompt for the AI tutor during voice interactions

**Current Enhanced Prompt:**
```
You are Nabu, an advanced AI language tutor helping someone learn {target_language}. 

LEARNING CONTEXT:
- User's native language: {native_language}
- Current proficiency level: {proficiency_level}
- Learning style: {learning_style}
- Recent vocabulary focus: {recent_words}
- Areas of difficulty: {difficulties}
- Total vocabulary words: {vocab_count}

VOCABULARY CONTEXT:
Available vocabulary ({count} words): word1 (translation1), word2 (translation2), ... and {remaining} more words

TEACHING APPROACH:
- Respond primarily in {target_language} with occasional {native_language} explanations when needed
- Keep responses conversational and engaging (2-3 sentences max)
- Provide gentle, contextual corrections when appropriate
- Adapt difficulty based on user's responses
- Encourage active participation and questions
- Use real-world examples and cultural context when relevant

VOCABULARY INTEGRATION:
- Naturally introduce words from the user's vocabulary list above
- Prioritize words with lower mastery levels for reinforcement
- Reinforce recently learned words through repetition
- Provide context for new vocabulary usage
- Use vocabulary appropriate to the user's current level
- When introducing new words, provide brief translations in {native_language} if helpful

Remember: You are a supportive, patient tutor focused on building confidence and practical language skills.
```

**Context Sources:**
- User profile from database
- Recent session statistics
- Vocabulary usage patterns
- Engagement scores

**Vocabulary Context Mechanism:**
The AI model now receives comprehensive vocabulary context including:
- **Full vocabulary list**: All words the user has learned in the target language
- **Translations**: Native language translations for each word
- **Mastery levels**: How well the user knows each word (0.0-1.0)
- **Usage statistics**: Times seen and times used in conversations
- **Reinforcement needs**: Words that need more practice (mastery < 0.5)

This allows the AI to:
- Strategically introduce words from the user's vocabulary list
- Prioritize words that need reinforcement
- Provide appropriate translations when introducing new words
- Adapt conversation difficulty based on vocabulary mastery levels

**Tool Integration:**
The AI model now has access to dynamic tools that provide additional context based on user input:
- **Vocabulary Lookup Tool**: Searches user's vocabulary database for specific words
- **Media Recommendation Tool**: Suggests learning media based on user's level
- **Grammar Help Tool**: Provides targeted grammar assistance

Tools are automatically triggered based on keyword detection in user input, providing relevant information without requiring complex orchestration.

## 2. Conversation Analysis AI Prompt

**Location:** `core/note_generator.py` (lines 200-250)

**Purpose:** AI-powered analysis of conversations to extract insights

**Current Prompt:**
```
You are an expert language learning analyst. Analyze this {language} conversation and provide insights in JSON format.

CONVERSATION:
{conversation_text}

Please analyze and return a JSON object with the following structure:
{
    "topics": ["topic1", "topic2"],
    "grammar_corrections": [
        {
            "original": "incorrect phrase",
            "corrected": "correct phrase", 
            "explanation": "brief explanation"
        }
    ],
    "pronunciation_notes": ["note1", "note2"],
    "cultural_insights": ["insight1", "insight2"],
    "difficulty_level": 1.5,
    "engagement_score": 0.8,
    "learning_style_observations": "brief observations about the learner's style",
    "recommendations": ["recommendation1", "recommendation2"]
}

Focus on:
- Identifying key topics discussed
- Grammar patterns that need attention
- Pronunciation challenges
- Cultural context and insights
- Overall difficulty level (1.0-5.0)
- Engagement level (0.0-1.0)
- Personalized learning recommendations

Return only valid JSON.
```

## 3. Vocabulary Note Generation AI Prompt

**Location:** `core/note_generator.py` (lines 350-380)

**Purpose:** Generate personalized vocabulary learning notes

**Current Prompt:**
```
You are an expert language tutor creating a personalized vocabulary note for a {language} learner.

LEARNER CONTEXT:
- Proficiency level: {proficiency_level}
- Learning style: {learning_style}
- Total vocabulary words: {vocab_count}

NEW VOCABULARY FROM THIS SESSION:
{new_vocabulary_list}

CONVERSATION TOPICS:
{topics_discussed}

Create a personalized, encouraging vocabulary note that:
1. Celebrates the new words learned
2. Provides context for when to use each word
3. Includes memory tips or mnemonics
4. Suggests practice activities
5. Motivates continued learning

Keep it friendly, encouraging, and practical. Format it nicely with clear sections.
```

## 4. Note Generation System Prompts

**Location:** `core/note_generator.py` (various methods)

**Purposes:**
- Grammar note generation
- Pronunciation note generation
- Cultural insights note generation
- Progress summary note generation

**Current Approach:** Static templates with basic content extraction

**Recommended Enhancement:** Convert to AI-powered generation similar to vocabulary notes

## Context Integration

### User Learning Context
**Source:** Database queries in `_get_user_learning_context()` methods
- Proficiency level
- Learning style (based on engagement patterns)
- Total vocabulary count
- Session statistics
- Engagement scores

### Vocabulary Context
**Source:** Database queries in `_get_recent_vocabulary_context()` methods
- Recently learned words
- Words needing reinforcement
- Usage patterns
- Mastery levels

## Recommendations for Improvement

### 1. Enhanced Context Integration
- Add learning goals from user profile
- Include specific areas of difficulty
- Track preferred conversation topics
- Monitor pronunciation challenges

### 2. Dynamic Prompt Adaptation
- Adjust prompt complexity based on user level
- Include specific vocabulary focus areas
- Adapt teaching style based on learning preferences
- Incorporate cultural background information

### 3. AI-Powered Note Generation
- Convert all note generation to AI-powered
- Add personalized recommendations
- Include progress tracking insights
- Generate practice exercises

### 4. Conversation Memory
- Maintain conversation context across sessions
- Track recurring themes and topics
- Build on previous learning experiences
- Provide continuity in vocabulary introduction

### 5. Cultural Context Integration
- Include cultural background in prompts
- Adapt responses to cultural sensitivities
- Provide cultural explanations when relevant
- Use culturally appropriate examples

## Configuration

All prompts can be customized through the configuration system:
- `config.agent.system_prompt_template`
- `config.learning.target_language`
- `config.learning.native_language`
- `config.learning.test_mode`

## Testing and Validation

To test prompt effectiveness:
1. Monitor user engagement scores
2. Track vocabulary retention rates
3. Measure conversation quality
4. Collect user feedback on note quality
5. Analyze learning progress over time
