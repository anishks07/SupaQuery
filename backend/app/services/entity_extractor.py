"""
Entity Extractor Service using spaCy NER
Extracts named entities from text chunks
"""

import spacy
from typing import List, Dict, Any
import os


class EntityExtractor:
    """Extract named entities from text using spaCy"""
    
    def __init__(self):
        """Initialize spaCy model"""
        try:
            # Try to load the model
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ Entity Extractor initialized (spaCy en_core_web_sm)")
            
        except OSError:
            print("⚠️  spaCy model not found. Downloading en_core_web_sm...")
            print("   Run: python -m spacy download en_core_web_sm")
            print("   For now, entity extraction will be disabled")
            self.nlp = None
    
    def extract_entities(self, text: str, min_length: int = 2) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            min_length: Minimum entity length to keep
            
        Returns:
            List of entity dictionaries with text, type, start, end
        """
        if not self.nlp:
            return []
        
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            # Process text with spaCy
            doc = self.nlp(text[:100000])  # Limit text length to avoid memory issues
            
            entities = []
            for ent in doc.ents:
                # Filter out very short entities
                if len(ent.text) >= min_length:
                    entities.append({
                        "text": ent.text.strip(),
                        "type": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
            
            return entities
            
        except Exception as e:
            print(f"Warning: Entity extraction failed: {e}")
            return []
    
    def extract_concepts(self, text: str, min_freq: int = 2) -> List[str]:
        """
        Extract key concepts/noun phrases from text
        
        Args:
            text: Input text
            min_freq: Minimum frequency to consider a concept
            
        Returns:
            List of concept strings
        """
        if not self.nlp:
            return []
        
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            doc = self.nlp(text[:100000])
            
            # Extract noun chunks as concepts
            concepts = {}
            for chunk in doc.noun_chunks:
                concept = chunk.text.lower().strip()
                if len(concept) > 3:  # Filter short concepts
                    concepts[concept] = concepts.get(concept, 0) + 1
            
            # Return concepts that appear at least min_freq times
            key_concepts = [c for c, freq in concepts.items() if freq >= min_freq]
            
            return key_concepts[:20]  # Limit to top 20
            
        except Exception as e:
            print(f"Warning: Concept extraction failed: {e}")
            return []
    
    def extract_entities_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Extract entities from multiple texts efficiently
        
        Args:
            texts: List of text strings
            
        Returns:
            List of entity lists (one per input text)
        """
        if not self.nlp:
            return [[] for _ in texts]
        
        try:
            # Use spaCy's pipe for efficient batch processing
            all_entities = []
            
            for doc in self.nlp.pipe(texts, batch_size=50):
                entities = []
                for ent in doc.ents:
                    if len(ent.text) >= 2:
                        entities.append({
                            "text": ent.text.strip(),
                            "type": ent.label_,
                            "start": ent.start_char,
                            "end": ent.end_char
                        })
                all_entities.append(entities)
            
            return all_entities
            
        except Exception as e:
            print(f"Warning: Batch entity extraction failed: {e}")
            return [[] for _ in texts]
    
    def get_entity_types(self) -> List[str]:
        """Get list of supported entity types"""
        if not self.nlp:
            return []
        
        # spaCy's default entity types
        return [
            "PERSON",      # People, including fictional
            "NORP",        # Nationalities or religious or political groups
            "FAC",         # Buildings, airports, highways, bridges, etc.
            "ORG",         # Companies, agencies, institutions, etc.
            "GPE",         # Countries, cities, states
            "LOC",         # Non-GPE locations, mountain ranges, bodies of water
            "PRODUCT",     # Objects, vehicles, foods, etc.
            "EVENT",       # Named hurricanes, battles, wars, sports events, etc.
            "WORK_OF_ART", # Titles of books, songs, etc.
            "LAW",         # Named documents made into laws
            "LANGUAGE",    # Any named language
            "DATE",        # Absolute or relative dates or periods
            "TIME",        # Times smaller than a day
            "PERCENT",     # Percentage, including "%"
            "MONEY",       # Monetary values, including unit
            "QUANTITY",    # Measurements, as of weight or distance
            "ORDINAL",     # "first", "second", etc.
            "CARDINAL"     # Numerals that do not fall under another type
        ]


# Global instance
_entity_extractor = None

def get_entity_extractor() -> EntityExtractor:
    """Get or create EntityExtractor instance"""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
