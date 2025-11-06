import os 
import json
import subprocess
import tempfile 
from glob import glob 
from pathlib import Path
from dotenv import load_dotenv
import time
load_dotenv()

class FolderProcessor:
    """Simple class to process all videos and images in a folder using video-analyzer and image-analyzer."""
    
    def __init__(self, model=None, prompt=None, whisper_model="medium"):
        """
        Initialize the folder processor.
        
        Args:
            model: Model to use (e.g., "gpt-4o-mini" or "gemma3:latest")
            prompt: Custom prompt for analysis
            whisper_model: Whisper model for audio transcription
        """
        self.model = model or "gemma3:latest"
        self.prompt = prompt
        self.whisper_model = whisper_model
        self.video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm', '*.m4v']
        self.image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.bmp']

    def process_image(self, image_path: str, output_dir: str = None):
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
            cmd = ["image-analyzer", str(image_path)]
            
            if self.prompt is not None:
                cmd.extend(["--prompt", self.prompt])
            
            if self.model is not None:
                if "gpt" in self.model:  # use openai api
                    cmd.extend(["--client", "openai_api"])
                    cmd.extend(["--api-url","https://api.openai.com/v1"])
                    if "OPENAI_API_KEY" in os.environ:
                        cmd.extend(["--api-key", os.environ["OPENAI_API_KEY"]])
                # add model
                cmd.extend(["--model", self.model])
            
            # output directory
            cmd.extend(["--output-dir", output_dir])
            
            # Hide API key in output
            display_cmd = ' '.join(cmd)
            if "OPENAI_API_KEY" in os.environ:
                display_cmd = display_cmd.replace(os.environ["OPENAI_API_KEY"], '*****')
            print(f"Running command: {display_cmd}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {"error": f"Return code {result.returncode}: {result.stderr}"}
            else: 
                return {"success": True, "output_dir": output_dir}
        
        except subprocess.TimeoutExpired:
            return {"error": "Timeout processing image"}
            
        except Exception as e:
            return {"error": str(e)}

    def process_video(self, video_path: str, output_dir: str = None):
        """Process a single video using video-analyzer."""
        temp_dir = None 
        if output_dir is None:
            temp_dir = tempfile.mkdtemp()
            output_dir = temp_dir
        else:
            output_dir = str(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Build command as separate arguments
            cmd = ["video-analyzer", str(video_path)]
            
            if self.prompt is not None:
                cmd.extend(["--prompt", self.prompt])
            
            if self.model is not None:
                if "gpt" in self.model.lower():  # use openai api
                    cmd.extend(["--client", "openai_api"])
                    cmd.extend(["--api-url","https://api.openai.com/v1"])
                    if "OPENAI_API_KEY" in os.environ:
                        cmd.extend(["--api-key", os.environ["OPENAI_API_KEY"]])
                    
                # add model
                cmd.extend(["--model", self.model])
                # add whisper model
                cmd.extend(["--whisper-model", self.whisper_model])

            # output directory
            cmd.extend(["--output", output_dir])
            
            # Hide API key in output
            display_cmd = ' '.join(cmd)
            if "OPENAI_API_KEY" in os.environ:
                display_cmd = display_cmd.replace(os.environ["OPENAI_API_KEY"], '*****')
            print(f"Running command: {display_cmd}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {"error": f"Return code {result.returncode}: {result.stderr}"}
            else: 
                return {"success": True, "output_dir": output_dir}
        
        except subprocess.TimeoutExpired:
            return {"error": "Timeout processing video"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def find_videos(self, folder_path: str):
        """Find all video files in the specified folder."""
        process_video_queue = []
        folder_path = str(folder_path).rstrip('/')  # Remove trailing slash
        
        for extension in self.video_extensions: 
            # Use os.path.join for proper path construction
            pattern = os.path.join(folder_path, extension)
            process_video_queue.extend(glob(pattern))
            
            # Also check uppercase
            #pattern_upper = os.path.join(folder_path, extension.upper())
            #process_video_queue.extend(glob(pattern_upper))
        
        return process_video_queue
    
    def find_images(self, folder_path: str):
        """Find all image files in the specified folder."""
        process_image_queue = []
        folder_path = str(folder_path).rstrip('/')  # Remove trailing slash
        
        for extension in self.image_extensions:
            # Use os.path.join for proper path construction
            pattern = os.path.join(folder_path, extension)
            process_image_queue.extend(glob(pattern))
            
            # Also check uppercase
            #pattern_upper = os.path.join(folder_path, extension.upper())
            #process_image_queue.extend(glob(pattern_upper))
        
        return process_image_queue
    
    def find_all_media(self, folder_path: str):
        """Find all video and image files in the specified folder."""
        videos = self.find_videos(folder_path)
        images = self.find_images(folder_path)
        return videos, images
    
    def process_folder(self, folder_path: str, output_dir: str = None):
        """Process all videos and images in a folder and return results dictionary."""
        # Find both videos and images
        video_files, image_files = self.find_all_media(folder_path)
        #video_files=[]
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
                start_time=time.time()
                result = self.process_video(abs_path, output_dir=media_output_dir)
                run_time=time.time()-start_time
                if "error" in result:
                    print(f"Error: {result['error']}")
                    results[clean_filename] = {"error": result['error'], "type": "video"}
                    continue
                
                # Look for the analysis JSON file
                #json_file = "output/analysis.json"
                json_file = os.path.join(result.get('output_dir', 'output'), "analysis.json")
                if not os.path.exists(json_file):
                    # Try to find any JSON file
                    json_files = glob("output/*.json")
                    if json_files:
                        json_file = json_files[0]
                    else:
                        print(f"No JSON output found in output directory")
                        results[clean_filename] = {"error": "No JSON output found", "type": "video"}
                        continue
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                
                # Try different possible keys for the description
                description = (analysis_data.get('final_description') or 
                              analysis_data.get('video_description') or 
                              analysis_data.get('description') or 
                              'No description available')
                transcript  =  (analysis_data.get("transcript")["text"] or "No transcript available")
                processing_time = run_time
                results[clean_filename] = {
                "description": description["response"],
                 "type": "video",
                 "processing_time":processing_time,
                 "transcript":transcript,
                 "file_path":abs_path}
                self.save_results(results,output_dir)
                preview = description[:100] + "..." if len(description) > 100 else description
                print(f"{preview}")
                
            except Exception as e:
                print(f"Error processing {clean_filename}: {str(e)}")
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
                start_time=time.time()
                result = self.process_image(abs_path, output_dir=media_output_dir)
                run_time=time.time() - start_time
                if "error" in result:
                    print(f"Error: {result['error']}")
                    results[clean_filename] = {"error": result['error'], "type": "image"}
                    continue
                
                # Look for the image analysis JSON file
                json_file = os.path.join(result.get('output_dir', 'output'), "image_analysis.json")
                if not os.path.exists(json_file):
                    # Try default output directory
                    json_file = "output/image_analysis.json"
                    if not os.path.exists(json_file):
                        print(f"No JSON output found for image")
                        results[clean_filename] = {"error": "No JSON output found", "type": "image"}
                        continue
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    analysis_data = json.load(f)
                
                # Extract description from image analysis structure
                analysis_response = (analysis_data.get('analysis', {}).get('description') or
                              analysis_data.get('description') or
                              'No description available')
                description=analysis_response["response"]
                processing_time =run_time
                results[clean_filename] = {
                "description": description, 
                "type": "image",
                "processing_time":processing_time,
                "file_path":abs_path}
                
                self.save_results(results,output_dir)
                preview = description[:100] + "..." if len(description) > 100 else description
                print(f" {preview}")
                
            except Exception as e:
                print(f"Error processing {clean_filename}: {str(e)}")
                results[clean_filename] = {"error": str(e), "type": "image"}

        return results
    
    def save_results(self, results: dict, output_dir: str, filename: str = "media_descriptions.json"):
        """Save results to a JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        results_file = os.path.join(output_dir, filename)
        
        with open(results_file, "w", encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results_file
    
    def print_summary(self, results: dict, results_file: str = None):
        """Print a summary of the processing results."""
        print(f"\n{'='*50}")
        print("RESULTS:")
        print('='*50)

        successful_videos = 0
        successful_images = 0
        failed = 0
        
        for file_name, data in results.items():
            file_type = data.get('type', 'unknown')
          
            print(f"\n {file_name} ({file_type.upper()}):")
            if isinstance(data, dict) and "error" in data:
                print(f"   Error: {data['error']}")
                failed += 1
            else:
                description = data.get('description', 'No description')
                print(f"  {description}")
                if file_type == "video":
                    successful_videos += 1
                elif file_type == "image":
                    successful_images += 1
                
        total_successful = successful_videos + successful_images
        print(f"Successfully processed {total_successful} out of {len(results)} files")
        print(f"Videos: {successful_videos}")
        print(f"Images: {successful_images}")
        print(f"Failed: {failed}")
        if results_file:
            
            print(f"Results saved to: {os.path.abspath(results_file)}")


def main():
    """Example usage of the FolderProcessor class."""
    # Create processor with desired settings
    processor = FolderProcessor(
        model="gpt-4.1-nano", #"gemma3:latest",
        whisper_model="medium"
    )
    
    # Process folder
    test_path = "C:/Users/jarvi/Documents/GIT/file_manger_ai/test_data/VideoRecording20251026"
    output_dir = "video-analyzer/VideoRecording_20251026/gpt/"
    
    results = processor.process_folder(test_path, output_dir=output_dir)
    
    if len(results) > 0:
        # Save results
        results_file = processor.save_results(results, output_dir)
        
        # Print summary
        processor.print_summary(results, results_file)


if __name__ == "__main__":
    main()