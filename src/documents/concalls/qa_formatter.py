import os
import json

class QADeepFormatter:
    def generate_markdown(self, json_path: str, output_path: str):
        abs_json_path = os.path.abspath(json_path)
        abs_output_path = os.path.abspath(output_path)
        
        with open(abs_json_path, 'r', encoding='utf-8') as f:
            interactions = json.load(f)
            
        md = []
        md.append("# Detailed Q&A Extraction\n")
        
        for interaction in interactions:
            analyst_name = interaction.get("analyst_name", "Unknown")
            firm = interaction.get("firm", "Unknown")
            
            md.append(f"📊 **{analyst_name}** ({firm})\n")
            
            for qa_pair in interaction.get("qa_pairs", []):
                question = qa_pair.get("question", "")
                answer = qa_pair.get("direct_answer", "")
                
                md.append(f"    Q: {question}")
                md.append(f"        {answer}\n")
                
            md.append("---\n")
            
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        with open(abs_output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
            
        print(f"[*] Generated standalone Q&A Report at: {abs_output_path}")
