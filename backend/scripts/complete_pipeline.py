"""
Complete Thai Word Segmentation + POS Tagging Pipeline
Uses: MTU CRF + LST20 Dictionary + POS Tags

Usage:
    python complete_pipeline.py
"""

import pickle
import sys
from typing import List, Tuple
from utils.features import load_model
import sklearn_crfsuite

# Import components
try:
    from crf_mtu_inference import load_model, segment_text_to_mtus
    from word_segmentation import WordSegmenter, PatternRules
    from lst20_dictionary_builder import LST20Dictionary
except ImportError:
    print("Error: Make sure all required files are in the same directory:")
    print("  - crf_mtu_inference.py")
    print("  - word_segmentation.py")
    print("  - lst20_dictionary_builder.py")
    sys.exit(1)


class ThaiTextSegmenterWithPOS:
    """
    Complete Thai text segmentation + POS tagging pipeline.
    
    Pipeline:
    Text → MTU (CRF) → Words (LST20 Dictionary) → POS Tags (LST20)
    """
    
    def __init__(self, mtu_model_path: str, dictionary_path: str):
        """
        Initialize the segmenter with POS tagging.
        
        Args:
            mtu_model_path: Path to trained MTU CRF model
            dictionary_path: Path to LST20 dictionary pickle file
        """
        print("🔧 Initializing Thai Text Segmenter with POS Tagging...")
        
        # Load MTU CRF model
        print(f"   Loading MTU model from: {mtu_model_path}")
        self.mtu_crf = load_model(mtu_model_path)
        print("   ✓ MTU model loaded")
        
        # Load LST20 dictionary
        print(f"   Loading LST20 dictionary from: {dictionary_path}")
        self.dictionary = LST20Dictionary.load(dictionary_path)
        print(f"   ✓ Dictionary loaded ({len(self.dictionary.words):,} words)")
        
        # Initialize word segmenter
        self.word_segmenter = WordSegmenter(self.dictionary)
        
        print("✅ Segmenter ready!\n")
    
    def segment(self, text: str, show_mtus: bool = False) -> List[str]:
        """
        Segment Thai text into words.
        
        Args:
            text: Input Thai text
            show_mtus: If True, also print MTU segmentation
        
        Returns:
            List of segmented words
        """
        # Step 1: Segment into MTUs
        # mtus_nested = segment_text_to_mtus(text, self.mtu_crf)
        mtus_nested, _, _ = segment_text_to_mtus(text, self.mtu_crf)
        mtus = ["".join(mtu) for mtu in mtus_nested]
        
        if show_mtus:
            print(f"   MTUs: {' | '.join(mtus)}")
        
        # Step 2: Segment MTUs into words using LST20 dictionary
        words = self.word_segmenter.segment_from_mtus(mtus)
        # words = self.word_segmenter.segment_from_mtus(mtus)
        # words = self.merge_compounds(words)
        return words
    
    def segment_with_pos(self, text: str, show_mtus: bool = False) -> List[Tuple[str, str]]:
        """
        Segment text and assign POS tags.
        
        Args:
            text: Input Thai text
            show_mtus: If True, also print MTU segmentation
        
        Returns:
            List of (word, pos_tag) tuples
        """
        # Get words
        words = self.segment(text, show_mtus=show_mtus)
        
        # Assign POS tags
        words_with_pos = []
        for word in words:
            pos = self.dictionary.get_most_likely_pos(word)
            words_with_pos.append((word, pos))
        
        return words_with_pos
        


def main():
    """Main function to demonstrate the complete pipeline"""
    
    print("=" * 80)
    print("Thai Word Segmentation + POS Tagging - Complete Pipeline")
    print("MTU (CRF) → Words (LST20 Dictionary) → POS Tags")
    print("=" * 80)
    print()
    
    # Configuration
    # MODEL_PATH = r"D:\project\word_wrapping\script\data\text_dataset\train_silver\mtu_crf_model.pkl"
    # DICT_PATH = r"D:\project\word_wrapping\script\data\text_dataset\train_silver\lst20_dictionary.pkl"
    # Get the directory where this script is located
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Build path relative to script location
    # Go up one level from scripts/ to backend/, then into models/
    MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "models", "mtu_crf_model.pkl")
    DICT_PATH =  os.path.join(SCRIPT_DIR, "..", "models", "lst20_dictionary.pkl")

    # Or normalize the path
    MODEL_PATH = os.path.normpath(MODEL_PATH)
    DICT_PATH = os.path.normpath(DICT_PATH)
    
    try:
        # Initialize segmenter
        segmenter = ThaiTextSegmenterWithPOS(MODEL_PATH, DICT_PATH)
        
        # Test cases
        test_texts = [
            "สวัสดี",
            "กาแฟ",
            "การเชื่อมต่อ",
            "สิทธิลงมติรับหรือไม่รับร่างรัฐธรรมนูญฉบับปี",
            "นั่นมือถืออะไร",
            "คนไทยเลิกหวาน",
        ]
        
        print("=" * 80)
        print("Testing Word Segmentation + POS Tagging:")
        print("=" * 80)
        
        for text in test_texts:
            print(f"\n📝 Input: {text}")
            
            # Get words with POS tags
            words_with_pos = segmenter.segment_with_pos(text, show_mtus=True)
            
            # Format output
            word_str = " | ".join([word for word, pos in words_with_pos])
            pos_str = " | ".join([f"{word}/{pos}" for word, pos in words_with_pos])
            
            print(f"   Words: {word_str}")
            print(f"   W/POS: {pos_str}")
        
        print("\n" + "=" * 80)
        print("✅ Pipeline Complete!")
        print("=" * 80)
        
        # Interactive mode
        print("\n" + "=" * 80)
        print("Interactive Mode - Options:")
        print("  1. Type Thai text for segmentation + POS tagging")
        print("  2. Type 'stats' to see dictionary statistics")
        print("  3. Type 'quit' to exit")
        print("=" * 80)
        
        while True:
            try:
                user_input = input("\n👉 Enter command or text: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                if user_input.lower() == 'stats':
                    segmenter.dictionary.print_stats()
                    continue
                
                if not user_input:
                    continue
                
                # Segment with POS
                words_with_pos = segmenter.segment_with_pos(user_input, show_mtus=True)
                
                # Format output
                word_str = " | ".join([word for word, pos in words_with_pos])
                pos_str = " | ".join([f"{word}/{pos}" for word, pos in words_with_pos])
                
                print(f"   📤 Words: {word_str}")
                print(f"   🏷️  W/POS: {pos_str}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    except FileNotFoundError as e:
        print(f"❌ Error: Required file not found")
        print(f"   {e}")
        print("\n📋 Required files:")
        print(f"   1. MTU model: {MODEL_PATH}")
        print(f"   2. Dictionary: {DICT_PATH}")
        print("\n🔧 Setup steps:")
        print("   1. Run: python crf_mtu_trainer.py (to train MTU model)")
        print("   2. Run: python lst20_dictionary_builder.py (to build dictionary)")
        print("   3. Run: python complete_pipeline.py (this file)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    
    # In complete_pipeline.py, add this test:
    def test_compound_words():
        """Test that compound words are kept together"""
        
        test_cases = [
            ("รัฐธรรมนูญ", ["รัฐธรรมนูญ"]),  # Should stay as ONE word
            ("แม่น้ำ", ["แม่น้ำ"]),            # Another compound
            ("นายกรัฐมนตรี", ["นายก", "รัฐมนตรี"]),  # Could be 1 or 2 words
        ]
        
        for text, expected in test_cases:
            mtus_nested, _, _ = segment_text_to_mtus(text, segmenter.mtu_crf)
            mtus = ["".join(mtu) for mtu in mtus_nested]
            words = segmenter.word_segmenter.segment_from_mtus(mtus)
            
            print(f"Text: {text}")
            print(f"  MTUs: {' | '.join(mtus)}")
            print(f"  Words: {' | '.join(words)}")
            print(f"  Expected: {' | '.join(expected)}")
            print(f"  Match: {'✅' if words == expected else '❌'}")
            print()


if __name__ == "__main__":
    main()