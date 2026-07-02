import json

input_file = '/mnt/f/zizo/GenAI/mini_RAG/src/scraping/islamweb_fatawa.jsonl'  # Change this to your filename
output_file = 'fatwas.txt'

with open(input_file, 'r', encoding='utf-8') as f_in, \
     open(output_file, 'w', encoding='utf-8-sig') as f_out:
    
    for line in f_in:
        # Load each line as a JSON object
        data = json.loads(line)
        
        # Extract question and answer from metadata
        question = data.get('metadata', {}).get('question', '').strip()
        answer = data.get('metadata', {}).get('answer', '').strip()
        
        # Write to TXT file with a clear separator
        f_out.write(f"السؤال: {question}\n")
        f_out.write(f"الإجابة: {answer}\n")
        f_out.write("\n")  # Adds a visual separator between fatwas

print(f"Done! Data saved to {output_file}")