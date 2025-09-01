# BrainyPal AI Service - Updated for Hugging Face and IntaSend
# ai_service.py

import requests
import json
import re
import time
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
from transformers import pipeline
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """Main AI service for content generation using Hugging Face"""
    
    def __init__(self):
        """Initialize AI service with Hugging Face API"""
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY', 'hf_your_api_key_here')
        
        # Hugging Face API endpoints
        self.hf_base_url = "https://api-inference.huggingface.co/models"
        self.models = {
            'text_generation': 'microsoft/DialoGPT-medium',
            'question_generation': 'valhalla/t5-base-qg-hl',
            'summarization': 'facebook/bart-large-cnn',
            'classification': 'cardiffnlp/twitter-roberta-base-emotion',
            'text2text': 'google/flan-t5-large'  # Better for educational content
        }
        
        # Initialize NLP tools
        self.initialize_nlp_tools()
        
        # Rate limiting for Hugging Face API
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_delay = 2  # seconds between requests for free tier
    
    def initialize_nlp_tools(self):
        """Initialize NLP tools and download required data"""
        try:
            # Download NLTK data if available
            if HAS_NLTK:
                try:
                    nltk.download('punkt', quiet=True)
                    nltk.download('stopwords', quiet=True)
                    nltk.download('averaged_perceptron_tagger', quiet=True)
                    self.stop_words = set(stopwords.words('english'))
                except Exception as e:
                    logger.warning(f"NLTK download failed: {e}")
                    self.stop_words = set()
            else:
                self.stop_words = set()
            
            # Load spaCy model for better NLP processing
            if HAS_SPACY:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    logger.warning("spaCy model not found. Using fallback methods.")
                    self.nlp = None
            else:
                self.nlp = None
            
            logger.info("NLP tools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP tools: {e}")
            self.nlp = None
            self.stop_words = set()
    
    def rate_limit_check(self):
        """Check and enforce rate limiting for Hugging Face"""
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - (current_time - self.last_request_time)
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def generate_flashcards(self, content: str, topic: str, difficulty: str = 'intermediate', count: int = 10) -> List[Dict]:
        """Generate flashcards from content using Hugging Face AI"""
        try:
            logger.info(f"Generating {count} flashcards for topic: {topic}")
            
            # Preprocess content
            processed_content = self.preprocess_content(content)
            key_concepts = self.extract_key_concepts(processed_content)
            
            # Generate using Hugging Face
            if self.huggingface_api_key and self.huggingface_api_key != 'hf_your_api_key_here':
                flashcards = self.generate_flashcards_huggingface(processed_content, topic, difficulty, count)
            else:
                logger.warning("Hugging Face API key not configured, using fallback generation")
                flashcards = self.generate_flashcards_fallback(processed_content, topic, difficulty, count, key_concepts)
            
            # Post-process and validate flashcards
            flashcards = self.validate_flashcards(flashcards, difficulty)
            
            logger.info(f"Successfully generated {len(flashcards)} flashcards")
            return flashcards[:count]  # Ensure we don't exceed requested count
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            return self.generate_flashcards_fallback(content, topic, difficulty, count)
    
    def generate_questions(self, content: str, topic: str, difficulty: str = 'intermediate', count: int = 5) -> List[Dict]:
        """Generate quiz questions from content using Hugging Face AI"""
        try:
            logger.info(f"Generating {count} quiz questions for topic: {topic}")
            
            # Preprocess content
            processed_content = self.preprocess_content(content)
            
            # Generate using Hugging Face
            if self.huggingface_api_key and self.huggingface_api_key != 'hf_your_api_key_here':
                questions = self.generate_questions_huggingface(processed_content, topic, difficulty, count)
            else:
                logger.warning("Hugging Face API key not configured, using fallback generation")
                questions = self.generate_questions_fallback(processed_content, topic, difficulty, count)
            
            # Validate questions
            questions = self.validate_questions(questions, difficulty)
            
            logger.info(f"Successfully generated {len(questions)} quiz questions")
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self.generate_questions_fallback(content, topic, difficulty, count)
    
    def generate_flashcards_huggingface(self, content: str, topic: str, difficulty: str, count: int) -> List[Dict]:
        """Generate flashcards using Hugging Face API"""
        self.rate_limit_check()
        
        prompt = self.build_flashcard_prompt(content, topic, difficulty, count)
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 800,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            # Use text2text generation model for better educational content
            response = requests.post(
                f"{self.hf_base_url}/{self.models['text2text']}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    generated_text = result.get('generated_text', '')
                else:
                    generated_text = str(result)
                
                flashcards = self.parse_flashcards_response(generated_text)
                
                if flashcards:
                    return flashcards
                else:
                    logger.warning("No flashcards parsed from AI response, using fallback")
                    raise Exception("Failed to parse AI response")
            
            elif response.status_code == 503:
                logger.warning("Hugging Face model is loading, waiting and retrying...")
                time.sleep(10)
                return self.generate_flashcards_huggingface(content, topic, difficulty, count)
            
            else:
                logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                raise Exception(f"API returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Hugging Face request failed: {e}")
            raise e
    
    def generate_questions_huggingface(self, content: str, topic: str, difficulty: str, count: int) -> List[Dict]:
        """Generate quiz questions using Hugging Face API"""
        self.rate_limit_check()
        
        prompt = self.build_question_prompt(content, topic, difficulty, count)
        
        headers = {
            "Authorization": f"Bearer {self.huggingface_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 600,
                "temperature": 0.6,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(
                f"{self.hf_base_url}/{self.models['text2text']}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    generated_text = result.get('generated_text', '')
                else:
                    generated_text = str(result)
                
                questions = self.parse_questions_response(generated_text)
                
                if questions:
                    return questions
                else:
                    logger.warning("No questions parsed from AI response, using fallback")
                    raise Exception("Failed to parse AI response")
            
            elif response.status_code == 503:
                logger.warning("Hugging Face model is loading, waiting and retrying...")
                time.sleep(10)
                return self.generate_questions_huggingface(content, topic, difficulty, count)
            
            else:
                logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                raise Exception(f"API returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Hugging Face request failed: {e}")
            raise e
    
    def build_flashcard_prompt(self, content: str, topic: str, difficulty: str, count: int) -> str:
        """Build optimized prompt for flashcard generation"""
        difficulty_instructions = {
            'beginner': 'Focus on basic definitions and simple concepts. Use clear, simple language.',
            'intermediate': 'Include both definitions and applications. Mix conceptual and practical questions.',
            'advanced': 'Focus on complex relationships, analysis, and synthesis. Include challenging scenarios.'
        }
        
        return f"""
Task: Create {count} educational flashcards about {topic}.

Content to study: {content}

Instructions:
- {difficulty_instructions[difficulty]}
- Each flashcard should test understanding, not just memorization
- Questions should be clear and unambiguous
- Answers should be comprehensive but concise
- Cover different aspects of the topic

Format:
Q: [question]
A: [answer]
---

Generate {count} flashcards now:
"""
    
    def build_question_prompt(self, content: str, topic: str, difficulty: str, count: int) -> str:
        """Build optimized prompt for question generation"""
        difficulty_instructions = {
            'beginner': 'Simple multiple choice questions testing basic recall and understanding.',
            'intermediate': 'Questions requiring application and analysis of concepts.',
            'advanced': 'Complex questions involving synthesis, evaluation, and critical thinking.'
        }
        
        return f"""
Task: Create {count} multiple choice questions about {topic}.

Content: {content}

Requirements:
- {difficulty_instructions[difficulty]}
- Each question has exactly 4 options (A, B, C, D)
- Only one correct answer per question
- Distractors should be plausible but clearly wrong
- Questions should test understanding, not just memorization

Format:
Q: [question]
A) [option 1]
B) [option 2]
C) [option 3]
D) [option 4]
Correct: [A/B/C/D]
---

Generate {count} questions now:
"""
    
    def parse_flashcards_response(self, response_text: str) -> List[Dict]:
        """Parse AI response into flashcard format"""
        flashcards = []
        
        try:
            # Split by separator
            cards_text = response_text.split('---')
            
            for card_text in cards_text:
                card_text = card_text.strip()
                if not card_text:
                    continue
                
                # Extract question and answer
                lines = card_text.split('\n')
                question = ""
                answer = ""
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if line.startswith('Q:'):
                        current_section = 'question'
                        question = line[2:].strip()
                    elif line.startswith('A:'):
                        current_section = 'answer'
                        answer = line[2:].strip()
                    elif current_section == 'question' and line:
                        question += ' ' + line
                    elif current_section == 'answer' and line:
                        answer += ' ' + line
                
                if question and answer and len(question) > 5 and len(answer) > 10:
                    flashcards.append({
                        'question': question.strip(),
                        'answer': answer.strip()
                    })
            
            return flashcards
            
        except Exception as e:
            logger.error(f"Failed to parse flashcards response: {e}")
            return []
    
    def parse_questions_response(self, response_text: str) -> List[Dict]:
        """Parse AI response into quiz question format"""
        questions = []
        
        try:
            # Split by separator
            questions_text = response_text.split('---')
            
            for question_text in questions_text:
                question_text = question_text.strip()
                if not question_text:
                    continue
                
                lines = [line.strip() for line in question_text.split('\n') if line.strip()]
                
                if len(lines) < 6:  # Need Q + 4 options + Correct
                    continue
                
                # Extract question
                question_line = next((line for line in lines if line.startswith('Q:')), None)
                if not question_line:
                    continue
                
                question = question_line[2:].strip()
                
                # Extract options
                options = []
                correct_answer = 0
                
                for line in lines:
                    if line.startswith(('A)', 'B)', 'C)', 'D)')):
                        options.append(line[2:].strip())
                    elif line.startswith('Correct:'):
                        correct_letter = line.split(':')[1].strip()
                        correct_answer = ord(correct_letter.upper()) - ord('A')
                
                if len(options) == 4 and 0 <= correct_answer < 4 and question:
                    questions.append({
                        'question': question,
                        'options': options,
                        'correct_answer': correct_answer
                    })
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse questions response: {e}")
            return []
    
    def generate_flashcards_fallback(self, content: str, topic: str, difficulty: str, count: int, key_concepts: List[str] = None) -> List[Dict]:
        """Fallback flashcard generation using templates and content analysis"""
        logger.info("Using intelligent fallback flashcard generation")
        
        if not key_concepts:
            key_concepts = self.extract_key_concepts(content)
        
        # Enhanced templates based on difficulty
        templates = {
            'beginner': [
                "What is {concept}?",
                "Define {concept}.",
                "What does {concept} mean in the context of {topic}?",
                "Explain {concept} in simple terms.",
                "What is the purpose of {concept}?"
            ],
            'intermediate': [
                "How does {concept} relate to {topic}?",
                "What are the key features of {concept}?",
                "Why is {concept} important in {topic}?",
                "What are the main components of {concept}?",
                "How would you explain {concept} to someone learning {topic}?"
            ],
            'advanced': [
                "Analyze the relationship between {concept} and other elements in {topic}.",
                "Evaluate the significance of {concept} in the broader context of {topic}.",
                "What are the implications of {concept} for understanding {topic}?",
                "How might {concept} be applied in real-world scenarios related to {topic}?",
                "Compare and contrast {concept} with related concepts in {topic}."
            ]
        }
        
        flashcards = []
        used_concepts = set()
        
        # Generate flashcards from key concepts
        for i in range(min(count, len(key_concepts))):
            concept = key_concepts[i]
            if concept in used_concepts:
                continue
            
            used_concepts.add(concept)
            template = templates[difficulty][i % len(templates[difficulty])]
            
            question = template.format(concept=concept, topic=topic)
            answer = self.generate_contextual_answer(concept, topic, content, difficulty)
            
            flashcards.append({
                'question': question,
                'answer': answer
            })
        
        # Fill remaining slots with content-based questions
        sentences = sent_tokenize(content)
        important_sentences = self.rank_sentences_by_importance(sentences, topic)
        
        for i in range(len(flashcards), count):
            if i - len(key_concepts) < len(important_sentences):
                sentence = important_sentences[i - len(key_concepts)]
                question, answer = self.create_question_from_sentence(sentence, topic, difficulty)
                if question and answer:
                    flashcards.append({
                        'question': question,
                        'answer': answer
                    })
        
        return flashcards
    
    def generate_questions_fallback(self, content: str, topic: str, difficulty: str, count: int) -> List[Dict]:
        """Fallback question generation using intelligent templates"""
        logger.info("Using intelligent fallback question generation")
        
        key_concepts = self.extract_key_concepts(content)
        sentences = sent_tokenize(content)
        important_info = self.extract_factual_information(content)
        
        questions = []
        
        # Question templates based on difficulty
        templates = {
            'beginner': [
                self.create_definition_question,
                self.create_identification_question,
                self.create_true_false_question
            ],
            'intermediate': [
                self.create_application_question,
                self.create_comparison_question,
                self.create_cause_effect_question
            ],
            'advanced': [
                self.create_analysis_question,
                self.create_synthesis_question,
                self.create_evaluation_question
            ]
        }
        
        question_generators = templates[difficulty]
        
        for i in range(count):
            generator = question_generators[i % len(question_generators)]
            
            if i < len(key_concepts):
                concept = key_concepts[i]
                question_data = generator(concept, topic, content, important_info)
            elif i < len(sentences):
                sentence = sentences[i % len(sentences)]
                question_data = self.create_question_from_sentence_analysis(sentence, topic, difficulty)
            else:
                # Generate from remaining content
                question_data = generator(topic, topic, content, important_info)
            
            if question_data:
                questions.append(question_data)
        
        return questions
    
    def create_definition_question(self, concept: str, topic: str, content: str, info: Dict) -> Dict:
        """Create a definition-based question"""
        question = f"What is {concept} in the context of {topic}?"
        
        # Extract or generate answer from content
        correct_answer = self.extract_definition(concept, content)
        
        # Generate distractors
        distractors = [
            f"A method used primarily in other fields",
            f"An outdated concept no longer relevant to {topic}",
            f"A complex theory that applies only to advanced {topic}"
        ]
        
        options = [correct_answer] + distractors[:3]
        import random
        random.shuffle(options)
        correct_index = options.index(correct_answer)
        
        return {
            'question': question,
            'options': options,
            'correct_answer': correct_index
        }
    
    def create_application_question(self, concept: str, topic: str, content: str, info: Dict) -> Dict:
        """Create an application-based question"""
        question = f"How would {concept} be applied in a practical {topic} scenario?"
        
        scenarios = [
            f"When implementing {concept} in real-world {topic} applications",
            f"In theoretical discussions about {topic}",
            f"Only in academic research about {topic}",
            f"Never, as {concept} is purely theoretical"
        ]
        
        return {
            'question': question,
            'options': scenarios,
            'correct_answer': 0
        }
    
    def create_comparison_question(self, concept: str, topic: str, content: str, info: Dict) -> Dict:
        """Create a comparison-based question"""
        question = f"How does {concept} compare to other elements in {topic}?"
        
        options = [
            f"{concept} provides unique advantages in {topic} applications",
            f"{concept} is identical to all other {topic} concepts",
            f"{concept} is less important than any other {topic} element",
            f"{concept} has no relationship to other {topic} concepts"
        ]
        
        return {
            'question': question,
            'options': options,
            'correct_answer': 0
        }
    
    def preprocess_content(self, content: str) -> str:
        """Preprocess content for better AI generation"""
        if not content:
            return ""
        
        # Clean and normalize text
        content = re.sub(r'\s+', ' ', content.strip())
        content = re.sub(r'[^\w\s.,!?;:()\-\'\""]', '', content)
        
        # Limit content length for Hugging Face API
        max_length = 1500  # Conservative limit for free tier
        if len(content) > max_length:
            if HAS_NLTK:
                try:
                    sentences = sent_tokenize(content)
                except:
                    sentences = content.split('.')
            else:
                sentences = content.split('.')
                
            content = ""
            for sentence in sentences:
                if len(content + sentence) <= max_length:
                    content += sentence + " "
                else:
                    break
        
        return content.strip()
    
    def extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content using advanced NLP"""
        if not content:
            return []
        
        try:
            if self.nlp:
                # Use spaCy for better concept extraction
                doc = self.nlp(content)
                concepts = []
                
                # Extract named entities
                for ent in doc.ents:
                    if ent.label_ in ['PERSON', 'ORG', 'EVENT', 'LAW', 'LANGUAGE', 'NORP', 'PRODUCT']:
                        concepts.append(ent.text)
                
                # Extract important noun phrases
                for chunk in doc.noun_chunks:
                    if 2 <= len(chunk.text.split()) <= 4:  # Keep meaningful phrases
                        concepts.append(chunk.text)
                
                # Extract important single nouns
                for token in doc:
                    if (token.pos_ in ['NOUN', 'PROPN'] and 
                        len(token.text) > 3 and 
                        token.text.lower() not in self.stop_words):
                        concepts.append(token.text)
                
                # Remove duplicates and return top concepts
                unique_concepts = list(dict.fromkeys(concepts))  # Preserve order
                return unique_concepts[:25]
            else:
                # Fallback to NLTK-based extraction
                return self.extract_concepts_nltk(content)
                
        except Exception as e:
            logger.error(f"Concept extraction failed: {e}")
            return self.extract_concepts_simple(content)
    
    def extract_concepts_nltk(self, content: str) -> List[str]:
        """Extract concepts using NLTK"""
        if not HAS_NLTK:
            return self.extract_concepts_simple(content)
            
        try:
            tokens = word_tokenize(content.lower())
            tagged = nltk.pos_tag(tokens)
            
            # Extract nouns and proper nouns
            concepts = [word for word, pos in tagged 
                       if pos in ['NN', 'NNS', 'NNP', 'NNPS'] 
                       and word not in self.stop_words 
                       and len(word) > 3
                       and word.isalpha()]
            
            # Get frequency and return most common
            from collections import Counter
            concept_freq = Counter(concepts)
            return [concept for concept, freq in concept_freq.most_common(20)]
            
        except Exception as e:
            logger.error(f"NLTK concept extraction failed: {e}")
            return self.extract_concepts_simple(content)
    
    def extract_concepts_simple(self, content: str) -> List[str]:
        """Simple concept extraction fallback"""
        # Extract capitalized words (likely proper nouns/important terms)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', content)
        
        # Extract longer words (likely important terms)
        long_words = re.findall(r'\b[a-z]{6,}\b', content)
        
        # Combine and filter
        all_words = capitalized + long_words
        filtered_words = [word for word in all_words 
                         if word.lower() not in self.stop_words 
                         and len(word) > 3]
        
        # Remove duplicates while preserving order
        unique_words = list(dict.fromkeys(filtered_words))
        return unique_words[:15]
    
    def generate_contextual_answer(self, concept: str, topic: str, content: str, difficulty: str) -> str:
        """Generate contextual answer based on content"""
        # Find sentences containing the concept
        sentences = sent_tokenize(content)
        relevant_sentences = [s for s in sentences if concept.lower() in s.lower()]
        
        if relevant_sentences:
            # Use the most relevant sentence as base for answer
            base_sentence = max(relevant_sentences, key=len)
            
            # Enhance based on difficulty
            if difficulty == 'beginner':
                return f"{concept} refers to {base_sentence.lower()}"
            elif difficulty == 'intermediate':
                return f"{concept} is an important aspect of {topic}. {base_sentence} This concept helps in understanding the broader principles of {topic}."
            else:  # advanced
                return f"{concept} represents a complex element within {topic}. {base_sentence} Understanding {concept} is crucial for mastering advanced applications and theoretical frameworks in {topic}."
        else:
            # Generate generic but contextual answer
            return f"{concept} is a key concept in {topic} that plays an important role in understanding the fundamental principles and applications within this field."
    
    def validate_flashcards(self, flashcards: List[Dict], difficulty: str) -> List[Dict]:
        """Validate and improve generated flashcards"""
        validated_cards = []
        
        for card in flashcards:
            # Basic validation
            if not card.get('question') or not card.get('answer'):
                continue
            
            question = card['question'].strip()
            answer = card['answer'].strip()
            
            # Length validation
            if len(question) < 10 or len(answer) < 15:
                continue
            
            # Quality checks
            if question.lower() == answer.lower():
                continue
            
            # Ensure question ends with question mark
            if not question.endswith('?'):
                question += '?'
            
            # Improve answer quality based on difficulty
            answer = self.enhance_answer_quality(answer, difficulty)
            
            validated_cards.append({
                'question': question,
                'answer': answer
            })
        
        return validated_cards
    
    def validate_questions(self, questions: List[Dict], difficulty: str) -> List[Dict]:
        """Validate and improve generated quiz questions"""
        validated_questions = []
        
        for question in questions:
            # Basic validation
            if not all(key in question for key in ['question', 'options', 'correct_answer']):
                continue
            
            if len(question['options']) != 4:
                continue
            
            if not (0 <= question['correct_answer'] < 4):
                continue
            
            # Quality checks
            question_text = question['question'].strip()
            options = [opt.strip() for opt in question['options']]
            
            if len(question_text) < 10:
                continue
            
            # Check for option quality
            if any(len(opt) < 3 for opt in options):
                continue
            
            # Ensure question mark
            if not question_text.endswith('?'):
                question_text += '?'
            
            validated_questions.append({
                'question': question_text,
                'options': options,
                'correct_answer': question['correct_answer']
            })
        
        return validated_questions
    
    def enhance_answer_quality(self, answer: str, difficulty: str) -> str:
        """Enhance answer quality based on difficulty level"""
        if difficulty == 'beginner':
            # Keep answers simple and clear
            if len(answer) > 100:
                answer = answer[:100] + "..."
        elif difficulty == 'advanced':
            # Ensure comprehensive answers
            if len(answer) < 50:
                answer += " This concept involves multiple interconnected elements that require deeper understanding and analysis."
        
        return answer
    
    def rank_sentences_by_importance(self, sentences: List[str], topic: str) -> List[str]:
        """Rank sentences by importance for question generation"""
        scored_sentences = []
        
        for sentence in sentences:
            score = 0
            
            # Length score (prefer medium-length sentences)
            length = len(sentence.split())
            if 10 <= length <= 25:
                score += 2
            elif 8 <= length <= 30:
                score += 1
            
            # Topic relevance score
            if topic.lower() in sentence.lower():
                score += 3
            
            # Contains numbers or specific facts
            if re.search(r'\d+', sentence):
                score += 1
            
            # Contains key indicator words
            indicators = ['because', 'therefore', 'however', 'important', 'significant', 'main', 'primary']
            for indicator in indicators:
                if indicator in sentence.lower():
                    score += 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and return sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sentence for sentence, score in scored_sentences]
    
    def extract_factual_information(self, content: str) -> Dict:
        """Extract factual information for question generation"""
        facts = {
            'numbers': re.findall(r'\b\d+(?:\.\d+)?\b', content),
            'dates': re.findall(r'\b\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b', content),
            'names': [],
            'definitions': [],# BrainyPal AI Service
            }
