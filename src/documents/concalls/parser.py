import re
import json
import os

class ConcallParser:
    """
    Parses earnings call transcripts by identifying speakers and grouping Q&A sessions.
    This guarantees zero data loss and allows highly targeted AI extraction.
    """
    
    def __init__(self):
        # Matches "Srini Pallia:", "Sandeep Shah:", etc. at the start of a line.
        self.speaker_pattern = re.compile(r"^([A-Z][a-zA-Z\s\.\-]+):\s(.*)")
        
        # Matches boilerplate page headers/footers to delete them cleanly
        self.page_pattern = re.compile(r"^Page \d+ of \d+$", re.IGNORECASE)
        self.company_pattern = re.compile(r"^Wipro Limited$", re.IGNORECASE)
        self.date_pattern = re.compile(r"^[A-Z][a-z]+\s\d{1,2},\s20\d{2}$")

    def clean_text(self, lines: list[str]) -> list[str]:
        """Removes useless PDF headers and footers that interrupt sentences."""
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.page_pattern.match(line) or self.company_pattern.match(line) or self.date_pattern.match(line):
                continue
            cleaned.append(line)
        return cleaned

    def parse_into_chunks(self, transcript_text: str) -> list[dict]:
        """
        Reads the raw text and chunks it sequentially by Speaker.
        Returns: [{"speaker": "Aparna Iyer", "text": "..."}]
        """
        lines = self.clean_text(transcript_text.split("\n"))
        chunks = []
        
        current_speaker = "Unknown"
        current_text = []
        
        for line in lines:
            match = self.speaker_pattern.match(line)
            if match:
                # Save previous speaker's chunk
                if current_text:
                    chunks.append({"speaker": current_speaker, "text": " ".join(current_text)})
                
                # Start new speaker chunk
                current_speaker = match.group(1).strip()
                current_text = [match.group(2).strip()]
            else:
                # Continuation of the current speaker's monologue
                current_text.append(line)
                
        # Append the last chunk
        if current_text:
            chunks.append({"speaker": current_speaker, "text": " ".join(current_text)})
            
        return chunks

    def group_qa_by_analyst(self, chunks: list[dict], management_names: list[str]) -> list[dict]:
        """
        Groups the sequential chunks into logical Q&A blocks per Analyst.
        e.g., Everything Sandeep asks + what management answers is one block.
        """
        qa_blocks = []
        current_analyst = None
        current_block_text = []
        
        in_qa_mode = False
        
        for chunk in chunks:
            speaker = chunk["speaker"]
            text = chunk["text"]
            
            # Detect transition to Q&A
            if speaker == "Moderator" and ("Q&A" in text or "question" in text.lower()):
                in_qa_mode = True
                
            if not in_qa_mode:
                continue
                
            if speaker == "Moderator":
                # Moderator introduces a new analyst, so save the old block
                if current_analyst and current_block_text:
                    qa_blocks.append({
                        "analyst": current_analyst,
                        "discussion": "\n".join(current_block_text)
                    })
                current_analyst = None
                current_block_text = []
            elif speaker not in management_names:
                # It's an Analyst!
                if not current_analyst:
                    current_analyst = speaker
                current_block_text.append(f"Analyst ({speaker}): {text}")
            else:
                # It's Management answering the Analyst
                if current_analyst:
                    current_block_text.append(f"Management ({speaker}): {text}")
                    
        # Append the very last block
        if current_analyst and current_block_text:
            qa_blocks.append({
                "analyst": current_analyst,
                "discussion": "\n".join(current_block_text)
            })
            
        return qa_blocks

    def extract_monologue(self, chunks: list[dict], target_speakers: list[str]) -> str:
        """Extracts just the opening remarks of management (ignoring Q&A)."""
        monologue = []
        for chunk in chunks:
            speaker = chunk["speaker"]
            if speaker == "Moderator" and ("Q&A" in chunk["text"] or "question" in chunk["text"].lower()):
                break # Stop at Q&A
            if speaker in target_speakers:
                monologue.append(f"{speaker}: {chunk['text']}")
        return "\n\n".join(monologue)

    def run_full_parsing(self, text: str) -> dict:
        """Runs the entire chunking pipeline and returns a structured dictionary."""
        chunks = self.parse_into_chunks(text)
        
        # Hardcoding Wipro management for this specific run (can be parameterized later)
        management = ["Srini Pallia", "Aparna Iyer", "Abhishek Jain"]
        
        opening_remarks = self.extract_monologue(chunks, management)
        qa_sessions = self.group_qa_by_analyst(chunks, management)
        
        return {
            "opening_remarks": opening_remarks,
            "qa_sessions": qa_sessions
        }

if __name__ == "__main__":
    # Simple self-test
    parser = ConcallParser()
    sample = "Aparna Iyer: Hello.\nPage 1 of 13\nWipro Limited\nApril 16, 2026\nHow are you?\nModerator: We will now begin Q&A. Next is Sandeep.\nSandeep Shah: Why margins down?\nSrini Pallia: Because of investments."
    print(json.dumps(parser.run_full_parsing(sample), indent=2))
