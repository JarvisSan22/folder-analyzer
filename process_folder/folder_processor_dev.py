import os 
import shutil
import json
import subprocess
import tempfile 
from glob import glob 
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def process_video(video_path: str, model: str = None, prompt: str = None, output_dir: str = None):
    temp_dir = None 
    if output_dir is None:
        temp_dir = tempfile.mkdtemp()
        output_dir = temp_dir
    else:
        output_dir = str(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Build command as separate arguments (not f-strings)
        cmd = ["video-analyzer", str(video_path)]
        
        if prompt is not None:
            cmd.extend(["--prompt", prompt])
        
        if model is not None:
            if "gpt" in model:  # use openai api
                cmd.extend(["--client", "openai_api"])
                cmd.extend(["--api-key", os.environ["OPENAI_API_KEY"]])
            # add model
            cmd.extend(["--model", model])
            # add whisper model
            cmd.extend(["--whisper-model", "medium"])
        
        # output directory
        #cmd.extend(["--output", output_dir])

        print(f"Running VIDEO command: {' '.join(cmd).replace(os.environ.get('OPENAI_API_KEY', ''), '*****')}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {"error": f"Return code {result.returncode}: {result.stderr}"}
        else: 
            return {"success": True, "output_dir": output_dir, "type": "video"}
    
    except subprocess.TimeoutExpired:
        return {"error": "Timeout processing video"}
        
    except Exception as e:
        return {"error": str(e)}


def process_image(image_path: str, model: str = None, prompt: str = None, output_dir: str = None):
    """Process a single image using image-analyzer."""
    temp_dir = None 
    if output_dir is None:
        temp_dir = tempfile.mkdtemp()
        output_dir = temp_dir
    else:
        output_dir = str(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Build command as separate arguments
        # Assuming image-analyzer cli.py is in image-analyzer folder
        cmd = ["python", "image-analyzer/cli.py", str(image_path)]
        
        if prompt is not None:
            cmd.extend(["--prompt", prompt])
        
        if model is not None:
            if "gpt" in model:  # use openai api
                cmd.extend(["--client", "openai_api"])
                if "OPENAI_API_KEY" in os.environ:
                    cmd.extend(["--api-key", os.environ["OPENAI_API_KEY"]])
            # add model
            cmd.extend(["--model", model])
        
        # output directory
        cmd.extend(["--output-dir", output_dir])

        print(f"Running IMAGE command: {' '.join(cmd).replace(os.environ.get('OPENAI_API_KEY', ''), '*****')}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {"error": f"Return code {result.returncode}: {result.stderr}"}
        else: 
            return {"success": True, "output_dir": output_dir, "type": "image"}
    
    except subprocess.TimeoutExpired:
        return {"error": "Timeout processing image"}
        
    except Exception as e:
        return {"error": str(e)}


# File extensions
video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm', '*.m4v']
image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.bmp']


def find_media_files(folder_path: str):
    """Find all video and image files in the specified folder."""
    folder_path = str(folder_path).rstrip('/')  # Remove trailing slash
    
    video_files = []
    image_files = []
    
    # Find videos
    for extension in video_extensions: 
        pattern = os.path.join(folder_path, extension)
        video_files.extend(glob(pattern))
        
        pattern_upper = os.path.join(folder_path, extension.upper())
        video_files.extend(glob(pattern_upper))
    
    # Find images
    for extension in image_extensions:
        pattern = os.path.join(folder_path, extension)
        image_files.extend(glob(pattern))
        
        pattern_upper = os.path.join(folder_path, extension.upper())
        image_files.extend(glob(pattern_upper))
    
    return video_files, image_files


def process_folder(folder_path: str, output_dir: str = None):
    model = "gpt-4o-mini"  # Fixed model name
    model = "gemma3:latest"
    
    # Find both videos and images
    video_files, image_files = find_media_files(folder_path)
    
    total_files = len(video_files) + len(image_files)
    
    if total_files == 0:
        print("No video or image files found in directory")
        return {}

    print(f"[Found files: {len(video_files)} videos, {len(image_files)} images, {total_files} total]")

    results = {}
    file_count = 0
    
    # Process videos first
    for video_file in video_files:
        file_count += 1
        clean_filename = os.path.basename(video_file)
        print(f"\nProcessing VIDEO {file_count}/{total_files}: {clean_filename}")

        try:
            abs_path = os.path.abspath(video_file)
            
            # Create individual output directory for each video
            if output_dir:
                media_output_dir = os.path.join(output_dir, f"video_{os.path.splitext(clean_filename)[0]}")
            else:
                media_output_dir = None

            result = process_video(abs_path, model=model, output_dir=media_output_dir)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                results[clean_filename] = {"error": result['error'], "type": "video"}
                continue
            
            # Look for the analysis JSON file
            json_file = "output/analysis.json"
            if not os.path.exists(json_file):
                # Try to find any JSON file
                json_files = glob("output/*.json")
                if json_files:
                    json_file = json_files[0]
                else:
                    print(f"❌ No JSON output found in output directory")
                    results[clean_filename] = {"error": "No JSON output found", "type": "video"}
                    continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Try different possible keys for the description
            description = (analysis_data.get('final_description') or 
                          analysis_data.get('video_description') or 
                          analysis_data.get('description') or 
                          'No description available')
            
            results[clean_filename] = {"description": description, "type": "video"}
            preview = description[:100] + "..." if len(description) > 100 else description
            print(f"✅ {preview}")
            
        except Exception as e:
            print(f"❌ Error processing {clean_filename}: {str(e)}")
            results[clean_filename] = {"error": str(e), "type": "video"}
    
    # Process images
    for image_file in image_files:
        file_count += 1
        clean_filename = os.path.basename(image_file)
        print(f"\nProcessing IMAGE {file_count}/{total_files}: {clean_filename}")

        try:
            abs_path = os.path.abspath(image_file)
            
            # Create individual output directory for each image
            if output_dir:
                media_output_dir = os.path.join(output_dir, f"image_{os.path.splitext(clean_filename)[0]}")
            else:
                media_output_dir = None

            result = process_image(abs_path, model=model, output_dir=media_output_dir)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                results[clean_filename] = {"error": result['error'], "type": "image"}
                continue
            
            # Look for the image analysis JSON file
            json_file = os.path.join(result.get('output_dir', 'output'), "image_analysis.json")
            if not os.path.exists(json_file):
                # Try default output directory
                json_file = "output/image_analysis.json"
                if not os.path.exists(json_file):
                    print(f"❌ No JSON output found for image")
                    results[clean_filename] = {"error": "No JSON output found", "type": "image"}
                    continue
            
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
            
            # Extract description from image analysis structure
            description = (analysis_data.get('analysis', {}).get('description') or
                          analysis_data.get('description') or
                          'No description available')
            
            results[clean_filename] = {"description": description, "type": "image"}
            preview = description[:100] + "..." if len(description) > 100 else description
            print(f"✅ {preview}")
            
        except Exception as e:
            print(f"❌ Error processing {clean_filename}: {str(e)}")
            results[clean_filename] = {"error": str(e), "type": "image"}

    return results


def main():
    # Use forward slashes or os.path.join for cross-platform compatibility
    test_path = "C:/Users/jarvi/Documents/GIT/file_manger_ai/test_data/Trip"
    output_dir = "video-analyzer/test_output_t1"

    results = process_folder(test_path, output_dir=output_dir)
    
    if len(results) > 0:
        # Make sure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save results to JSON file
        results_file = os.path.join(output_dir, "media_descriptions.json")
        with open(results_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*50}")
        print("RESULTS:")
        print('='*50)

        successful_videos = 0
        successful_images = 0
        failed = 0
        
        for file_name, data in results.items():
            file_type = data.get('type', 'unknown')
            icon = "📹" if file_type == "video" else "🖼️" if file_type == "image" else "📄"
            
            print(f"\n{icon} {file_name} ({file_type.upper()}):")
            if isinstance(data, dict) and "error" in data:
                print(f"   ❌ Error: {data['error']}")
                failed += 1
            else:
                description = data.get('description', 'No description')
                print(f"   📝 {description}")
                if file_type == "video":
                    successful_videos += 1
                elif file_type == "image":
                    successful_images += 1
                
        total_successful = successful_videos + successful_images
        print(f"\n✅ Successfully processed {total_successful} out of {len(results)} files")
        print(f"   📹 Videos: {successful_videos}")
        print(f"   🖼️  Images: {successful_images}")
        print(f"   ❌ Failed: {failed}")
        print(f"💾 Results saved to: {os.path.abspath(results_file)}")


if __name__ == "__main__":
    main()