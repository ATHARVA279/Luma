import re
from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_into_sentences(self, text: str) -> List[str]:
        text = re.sub(r'(?<=Dr)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=Mr)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=Mrs)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=Ms)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=U\.S\.A)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=U\.S)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=e\.g)\.', '@@POINT@@', text)
        text = re.sub(r'(?<=i\.e)\.', '@@POINT@@', text)
        
        parts = re.split(r'(?<=[.!?])\s+', text)
        
        sentences = [p.replace('@@POINT@@', '.') for p in parts if p.strip()]
        
        return sentences

    def chunk_by_sentences(self, text: str) -> List[Dict[str, Any]]:
        sentences = self._split_into_sentences(text)
        chunks = []
        
        current_chunk_sentences = []
        current_chunk_word_count = 0
        
        start_idx = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            word_count = len(sentence.split())
            
            if current_chunk_word_count + word_count > self.chunk_size and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "text": chunk_text,
                    "start_sentence": start_idx,
                    "end_sentence": i - 1,
                    "chunk_index": len(chunks)
                })
                overlap_word_count = 0
                overlap_sentences = []
                
                j = i - 1
                while j >= start_idx:
                    s_len = len(sentences[j].split())
                    if overlap_word_count + s_len > self.overlap and overlap_sentences:
                        break
                    overlap_sentences.insert(0, sentences[j])
                    overlap_word_count += s_len
                    j -= 1
                
                current_chunk_sentences = overlap_sentences
                current_chunk_word_count = overlap_word_count
                start_idx = j + 1
                
                current_chunk_sentences.append(sentence)
                current_chunk_word_count += word_count
                i += 1
            else:
                current_chunk_sentences.append(sentence)
                current_chunk_word_count += word_count
                i += 1
        
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "text": chunk_text,
                "start_sentence": start_idx,
                "end_sentence": len(sentences) - 1,
                "chunk_index": len(chunks)
            })
            
        return chunks

    def chunk_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        
        current_chunk_paras = []
        current_chunk_word_count = 0
        
        for para in paragraphs:
            word_count = len(para.split())
            
            if current_chunk_word_count + word_count > self.chunk_size and current_chunk_paras:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunks.append({
                    "text": chunk_text,
                    "type": "paragraph_group",
                    "chunk_index": len(chunks)
                })
                
                last_para = current_chunk_paras[-1]
                last_para_len = len(last_para.split())
                
                if last_para_len <= self.overlap:
                    current_chunk_paras = [last_para]
                    current_chunk_word_count = last_para_len
                else:
                    current_chunk_paras = []
                    current_chunk_word_count = 0
            
            current_chunk_paras.append(para)
            current_chunk_word_count += word_count
            
        if current_chunk_paras:
            chunk_text = "\n\n".join(current_chunk_paras)
            chunks.append({
                "text": chunk_text,
                "type": "paragraph_group",
                "chunk_index": len(chunks)
            })
            
        return chunks

    def get_chunk_count(self, text: str) -> int:
        word_count = len(text.split())
        step = max(1, self.chunk_size - self.overlap)
        return max(1, word_count // step)
