import json
from backend.schemas.models import Node
# Import Kabilan's normalizer (adjust the import path based on exactly what he named his function)
from backend.ingestion.normalizer import run_all_parsers

def run_lead_smoke_test():
    print("🚨 Initiating Pod 1 Data Pipeline Test...")
    
    try:
        # 1. Fire Kabilan's master function which should trigger Ajay and Santosh's code
        raw_nodes = run_all_parsers()
        print(f"✅ Ingestion successful. Generated {len(raw_nodes)} raw nodes.")

        # 2. The Pydantic Crucible (This proves if the code is actually correct)
        validated_nodes = []
        for item in raw_nodes:
            # If they missed 'source_tool' or misspelled 'label', Pydantic will crash the script right here
            valid_node = Node(**item)
            validated_nodes.append(valid_node.model_dump())
            
        print("✅ Schema Validation Passed. No contract violations found.")
        
        # 3. Output the result so you can visually inspect it
        with open("test_output.json", "w") as f:
            json.dump(validated_nodes, f, indent=2)
            
        print("✅ Success! Check test_output.json. Pod 1 is cleared to hand off to Pod 2.")

    except Exception as e:
        print(f"❌ PIPELINE FAILURE: {e}")
        print("Tell the responsible Pod to fix their dictionary output.")

if __name__ == "__main__":
    run_lead_smoke_test()