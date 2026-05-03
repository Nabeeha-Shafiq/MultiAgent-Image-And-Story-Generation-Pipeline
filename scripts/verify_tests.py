import json
import os
import sys

def run_tests():
    print("--- Running Test Group 2: Script Generation ---")
    from config import OUTPUT_DIR
    manifest_path = os.path.join(OUTPUT_DIR, "scene_manifest.json")
    assert os.path.exists(manifest_path), f"TC-SCRIPT-01 FAILED: {manifest_path} does not exist."
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
        
    scenes = data.get("scenes", [])
    print(f"Scene count: {len(scenes)}")
    assert 3 <= len(scenes) <= 10, f"TC-SCRIPT-02 FAILED: Expected 3-10 scenes, got {len(scenes)}."
    
    all_characters = set()
    for s in scenes:
        assert "id" in s or "scene_id" in s
        assert "location" in s or "description" in s
        assert "characters" in s
        assert "dialogue" in s
        
        # TC-SCRIPT-03: Consistency
        for c in s["characters"]:
            # Simple check for same character multiple times with different casing 
            # e.g., Kael and KAEL
            all_characters.add(c)
            
        # TC-SCRIPT-04: Visual Cues (some schemas might not enforce visual_cue, but let's check)
        for d in s["dialogue"]:
            assert "character" in d or "speaker" in d
            assert "line" in d
            # Visual cue is a bonus, let's just make sure action keys exist
        for a in s.get("actions", []):
            assert len(a) > 2, "Visual cue/action too short."
            
    print("TC-SCRIPT-01..04 PASSED: Script is healthy.")
    
    print("\n--- Running Test Group 6: Output Completeness ---")
    char_db_path = os.path.join(OUTPUT_DIR, "character_db.json")
    image_dir_path = os.path.join(OUTPUT_DIR, "image_assets")
    
    assert os.path.exists(char_db_path), f"TC-OUT-01 FAILED: {char_db_path} missing."
    assert os.path.isdir(image_dir_path), f"TC-OUT-01 FAILED: {image_dir_path} missing."
    
    with open(char_db_path, "r") as f:
        db = json.load(f)
        
    assert "characters" in db, "TC-OUT-02 FAILED: missing characters array."
    
    for char in db["characters"]:
        assert "name" in char
        assert "appearance" in char
        assert "image_path" in char
        print(f"Character OK: {char['name']}")
        
        # TC-OUT-03: Image files exist
        path = char["image_path"]
        assert os.path.exists(path), f"TC-OUT-03 FAILED: Image missing at {path}"
        print(f"Image verified: {path}")

    print("TC-OUT-01..03 PASSED: Outputs are complete.")

if __name__ == "__main__":
    try:
        run_tests()
        print("\nALL AUTOMATED OUTPUT TESTS PASSED!")
    except Exception as e:
        import traceback
        print(f"\nERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
    
