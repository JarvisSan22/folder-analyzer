"""
Core image analysis functionality.
Reuses video-analyzer's client infrastructure and prompts.
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Initialize logger at module level
logger = logging.getLogger(__name__)

# Import existing video-analyzer components
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'video_analyzer'))
    from clients.ollama import OllamaClient
    from clients.generic_openai_api import GenericOpenAIAPIClient as OpenAIClient
    from config import Config as ConfigManager
except ImportError:
    try:
        # Fallback for development - adjust paths as needed
        import sys
        video_analyzer_path= os.path.join(os.path.dirname(__file__), '..', 'video_analyzer')
        sys.path.insert(0, video_analyzer_path)
        from clients.ollama import OllamaClient
        from clients.generic_openai_api import GenericOpenAIAPIClient as OpenAIClient
        from config import Config as ConfigManager
    except ImportError as e:
        logger.error(f"Error importing video-analyzer components: {e}")
        print(f"Error importing video-analyzer components: {e}")
        print("Make sure the video_analyzer directory is at the same level as image_analyzer")
        raise

class ImageAnalyzer:
    """Core image analysis class that reuses video-analyzer infrastructure."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize with configuration manager."""
        logger.debug("Initializing ImageAnalyzer")
        self.config_manager = config_manager
        self.clients = {}
        self._setup_clients()
        logger.info("ImageAnalyzer initialized successfully")
    
    def _setup_clients(self):
        """Setup vision model clients from config."""
        logger.debug("Setting up vision model clients")
        config = self.config_manager.get_config()
        
        # Setup Ollama client
        if 'ollama' in config.get('clients', {}):
            ollama_config = config['clients']['ollama']
            logger.debug(f"Configuring Ollama client with URL: {ollama_config.get('url', 'http://localhost:11434')}")
            self.clients['ollama'] = OllamaClient(
                base_url=ollama_config.get('url', 'http://localhost:11434')
            )
            logger.info("Ollama client configured")
        
        # Setup OpenAI API client  
        if 'openai_api' in config.get('clients', {}):
            openai_config = config['clients']['openai_api']
            logger.debug(f"Configuring OpenAI API client with URL: {openai_config.get('api_url')}")
            self.clients['openai_api'] = OpenAIClient(
                api_key=openai_config.get('api_key'),
                api_url=openai_config.get('api_url'),
            )
            logger.info("OpenAI API client configured")
        
        logger.info(f"Total clients configured: {len(self.clients)}")
    
    def _load_image_as_base64(self, image_path: str) -> str:
        """Load image file and convert to base64."""
        logger.debug(f"Loading image as base64: {image_path}")
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            logger.debug(f"Image loaded successfully, size: {len(image_data)} bytes")
            return base64_data
        except Exception as e:
            logger.error(f"Error loading image as base64: {e}")
            raise
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """Get MIME type for image file."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        logger.debug(f"Detected MIME type: {mime_type} for extension: {ext}")
        return mime_type
    
    def _load_frame_prompt(self, custom_prompt: Optional[str] = None) -> str:
        """Load the frame analysis prompt, with optional custom prompt injection."""
        logger.debug("Loading frame analysis prompt")
        
        # Try to load frame_analysis.txt from prompts directory
        prompt_paths = [
            os.path.join('prompts', 'image.txt'),
            os.path.join('..', 'prompts', 'image.txt'),
            os.path.join('..', '..', 'prompts', 'image.txt')
        ]
        
        frame_prompt = None
        for prompt_path in prompt_paths:
            if os.path.exists(prompt_path):
                logger.debug(f"Loading prompt from: {prompt_path}")
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    frame_prompt = f.read()
                logger.info(f"Prompt loaded from {prompt_path}")
                break
        
        if not frame_prompt:
            logger.warning("Prompt file not found, using fallback prompt")
            # Fallback prompt if file not found
            frame_prompt = """Analyze this image and provide a detailed description of what you see. 
Include information about:
- Objects and people in the image
- Actions or activities taking place
- Setting and environment
- Colors, lighting, and composition
- Any text or signs visible

{prompt}

Provide a clear, detailed description in paragraph form."""
        
        # Inject custom prompt if provided
        if custom_prompt:
            logger.debug(f"Injecting custom prompt: {custom_prompt[:50]}...")
            prompt_injection = f"I want to know: {custom_prompt}"
            frame_prompt = frame_prompt.replace('{prompt}', prompt_injection)
        else:
            frame_prompt = frame_prompt.replace('{prompt}', '')
        
        return frame_prompt
    
    def analyze_image(self, image_path: str, client_name: str = None, model: str = None, 
                     custom_prompt: str = None) -> Dict[str, Any]:
        """
        Analyze a single image using the specified client and model.
        
        Args:
            image_path: Path to the image file
            client_name: Client to use ('ollama' or 'openai_api')
            model: Model name to use
            custom_prompt: Optional custom prompt for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting image analysis for: {image_path}")
        
        try:
            # Validate image file exists
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get default client if not specified
            if not client_name:
                config = self.config_manager.get_config()
                client_name = config.get('clients', {}).get('default', 'ollama')
                logger.debug(f"Using default client: {client_name}")
            
            # Get client
            if client_name not in self.clients:
                logger.error(f"Client '{client_name}' not configured")
                raise ValueError(f"Client '{client_name}' not configured")
            
            client = self.clients[client_name]
            logger.info(f"Using client: {client_name}")
            
            # Override model if specified
            if model:
                logger.debug(f"Overriding model to: {model}")
                client.model = model
            
            logger.info(f"Using model: {client.model}")
            
            # Load image
            mime_type = self._get_image_mime_type(image_path)
            
            # Load prompt
            prompt = self._load_frame_prompt(custom_prompt)
            
            # Analyze image
            logger.info(f"Analyzing image with {client_name} using model {client.model}")
            analysis_result = client.generate(prompt, image_path=image_path)
            
            logger.debug(f"Analysis result length: {len(analysis_result)} characters")
            logger.info("Image analysis completed successfully")
            
            # Create result structure similar to video analyzer
            result = {
                'image_path': os.path.abspath(image_path),
                'image_filename': os.path.basename(image_path),
                'analysis': {
                    'client': client_name,
                    'model': client.model,
                    'prompt_used': prompt,
                    'description': analysis_result
                },
                'metadata': {
                    'file_size': os.path.getsize(image_path),
                    'mime_type': mime_type,
                    'analysis_successful': True
                }
            }
            
            logger.debug("Analysis result structure created")
            return result
            
        except Exception as e:
            logger.error(f"Error during image analysis: {e}", exc_info=True)
            return {
                'image_path': os.path.abspath(image_path) if os.path.exists(image_path) else image_path,
                'image_filename': os.path.basename(image_path),
                'error': str(e),
                'metadata': {
                    'analysis_successful': False
                }
            }
    
    def save_analysis(self, analysis_result: Dict[str, Any], output_dir: str = 'output') -> str:
        """
        Save analysis result to JSON file.
        
        Args:
            analysis_result: Analysis result dictionary
            output_dir: Output directory (default: 'output')
            
        Returns:
            Path to saved JSON file
        """
        logger.debug(f"Saving analysis to directory: {output_dir}")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'image_analysis.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis saved successfully to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            raise


def analyze_single_image(image_path: str, client: str = None, model: str = None, 
                        prompt: str = None, output_dir: str = 'output') -> Dict[str, Any]:
    """
    Convenience function to analyze a single image.
    
    Args:
        image_path: Path to image file
        client: Client name ('ollama' or 'openai_api')
        model: Model name
        prompt: Custom prompt
        output_dir: Output directory
        
    Returns:
        Analysis result dictionary
    """
    logger.info(f"analyze_single_image called for: {image_path}")
    logger.debug(f"Parameters - client: {client}, model: {model}, output_dir: {output_dir}")
    
    try:
        config_manager = ConfigManager()
        analyzer = ImageAnalyzer(config_manager)
        
        result = analyzer.analyze_image(image_path, client, model, prompt)
        
        if not result.get('error'):
            output_file = analyzer.save_analysis(result, output_dir)
            result['output_file'] = output_file
            logger.info(f"Analysis saved to: {output_file}")
            print(f"✓ Analysis saved to: {output_file}")
            
            # Print description preview
            description = result.get('analysis', {}).get('description', 'No description')
            preview = description[:100] + "..." if len(description) > 100 else description
            logger.debug(f"Description preview: {preview}")
            print(f"📝 Description: {preview}")
        else:
            logger.error(f"Analysis error: {result['error']}")
            print(f"❌ Error: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in analyze_single_image: {e}", exc_info=True)
        raise