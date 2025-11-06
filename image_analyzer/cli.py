"""
Command line interface for image-analyzer.
Mimics video-analyzer CLI structure and arguments.
"""

import argparse
import os
import sys
from pathlib import Path
import traceback
import logging

# Import core functionality
from .core import ImageAnalyzer, analyze_single_image

# Initialize logger at module level
logger = logging.getLogger(__name__)

# Import existing video-analyzer components
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'video_analyzer'))
    from config import Config as ConfigManager
except ImportError:
    try:
        # Fallback for development - adjust paths as needed
        import sys
        video_analyzer_path= os.path.join(os.path.dirname(__file__), '..', 'video_analyzer')
        sys.path.insert(0, video_analyzer_path)
        from config import Config as ConfigManager
    except ImportError as e:
        logger.error(f"Error importing video-analyzer components: {e}")
        print(f"Error importing video-analyzer components: {e}")
        print("Make sure the video_analyzer directory is at the same level as image_analyzer")
        raise


def get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant."""
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return levels.get(level_str.upper(), logging.INFO)


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='Analyze images using LLM vision models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  image-analyzer photo.jpg
  image-analyzer photo.jpg --prompt "What objects are in this image?"
  image-analyzer photo.jpg --client openai_api --model gpt-4o
  image-analyzer photo.jpg --output-dir ./results
        """
    )
    
    # Positional argument
    parser.add_argument(
        'image_path',
        help='Path to the image file to analyze'
    )
    
    # Client and model options (same as video-analyzer)
    parser.add_argument(
        '--client',
        choices=['ollama', 'openai_api'],
        help='Client to use for analysis (default: from config)'
    )
    
    parser.add_argument(
        '--model',
        help='Model name to use (default: from config)'
    )
    
    parser.add_argument(
        '--api-key',
        help='API key for external services'
    )
    
    parser.add_argument(
        '--api-url',
        help='API URL for external services'
    )
    
    # Analysis options
    parser.add_argument(
        '--prompt',
        help='Custom prompt for image analysis'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for analysis results (default: output)'
    )
    
    # Config options
    parser.add_argument(
        '--config',
        help='Path to custom config file'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level (default: INFO)'
    )
    
    # Verbose output (for backward compatibility)
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output (equivalent to --log-level DEBUG)'
    )
    
    return parser


def validate_image_file(image_path: str) -> bool:
    """Validate that the file exists and is a supported image format."""
    
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False
    
    supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    file_ext = Path(image_path).suffix.lower()
    
    if file_ext not in supported_extensions:
        logger.error(f"Unsupported image format: {file_ext}")
        logger.info(f"Supported formats: {', '.join(supported_extensions)}")
        return False
    
    logger.debug(f"Image file validated: {image_path}")
    return True


def setup_config(args) -> ConfigManager:
    """Setup configuration manager with command line overrides."""
    logger.debug("Setting up configuration manager")
    config_manager = ConfigManager()
    config_manager.update_from_args(args)
    logger.debug("Configuration loaded successfully")
    return config_manager


def main():
    """Main entry point for image-analyzer CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging with specified level
    # If verbose flag is set, override log level to DEBUG
    log_level_str = 'DEBUG' if args.verbose else args.log_level
    log_level = get_log_level(log_level_str)
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True  # Force reconfiguration of the root logger
    )
    # Ensure our module logger has the correct level
    logger.setLevel(log_level)
    
    logger.info("Image Analyzer started")
    logger.debug(f"Image: {args.image_path}")
    logger.debug(f"Output: {args.output_dir}")
    if args.client:
        logger.debug(f"Client: {args.client}")
    if args.model:
        logger.debug(f"Model: {args.model}")
    if args.prompt:
        logger.debug(f"Prompt: {args.prompt}")
    
    # Validate input
    if not validate_image_file(args.image_path):
        logger.error("Image validation failed")
        sys.exit(1)
    
    try:
        # Setup configuration
        config_manager = setup_config(args)
        
        config = config_manager.get_config()
        logger.debug(f"Config loaded: {len(config.get('clients', {}))} client(s) configured")
        
        # Create analyzer
        logger.info("Creating image analyzer")
        analyzer = ImageAnalyzer(config_manager)
        
        # Analyze image
        logger.info(f"Analyzing image: {args.image_path}")
        result = analyzer.analyze_image(
            image_path=args.image_path,
            client_name=args.client,
            model=args.model,
            custom_prompt=args.prompt
        )
        
        # Handle results
        if result.get('error'):
            logger.error(f"Analysis failed: {result['error']}")
            print(f"Analysis failed: {result['error']}")
            sys.exit(1)
        
        # Save results
        logger.info(f"Saving results to {args.output_dir}")
        output_file = analyzer.save_analysis(result, args.output_dir)
        
        # Print results
        logger.info("Analysis complete!")
        print(f"✓ Analysis complete!")
        print(f"Results saved to: {os.path.abspath(output_file)}")
        
        # Show description preview
        description = result.get('analysis', {}).get('description', 'No description available')
        preview = description[:200] + "..." if len(description) > 200 else description
        print(f"\n📝 Description:")
        print(f"   {preview}")
        
        # Log detailed info
        analysis = result.get('analysis', {})
        logger.debug(f"Client used: {analysis.get('client', 'Unknown')}")
        logger.debug(f"Model used: {analysis.get('model', 'Unknown')}")
        logger.debug(f"File size: {result.get('metadata', {}).get('file_size', 0)} bytes")
        logger.debug(f"MIME type: {result.get('metadata', {}).get('mime_type', 'Unknown')}")
        
        logger.info(f"Results saved to {output_file}")
    
    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        print("\n⚠ Analysis interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        
        if log_level == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


def batch_analyze_images(image_dir: str, **kwargs):
    """
    Batch analyze all images in a directory.
    This function can be imported and used by other scripts.
    """
    logger.info(f"Starting batch analysis of directory: {image_dir}")
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    image_dir = Path(image_dir)
    
    if not image_dir.exists():
        logger.error(f"Directory not found: {image_dir}")
        raise ValueError(f"Directory not found: {image_dir}")
    
    # Find all image files
    logger.debug("Searching for image files")
    image_files = []
    for ext in image_extensions:
        image_files.extend(image_dir.glob(f"*{ext}"))
        image_files.extend(image_dir.glob(f"*{ext.upper()}"))
    
    if not image_files:
        logger.warning(f"No image files found in {image_dir}")
        print(f"No image files found in {image_dir}")
        return {}
    
    logger.info(f"Found {len(image_files)} image file(s)")
    print(f"Found {len(image_files)} image file(s)")
    
    results = {}
    config_manager = ConfigManager()
    analyzer = ImageAnalyzer(config_manager)
    
    for i, image_file in enumerate(image_files, 1):
        logger.info(f"Processing image {i}/{len(image_files)}: {image_file.name}")
        print(f"\nProcessing {i}/{len(image_files)}: {image_file.name}")
        
        result = analyzer.analyze_image(
            image_path=os.path.join(image_dir, str(image_file)),
            client_name=kwargs.get('client'),
            model=kwargs.get('model'),
            custom_prompt=kwargs.get('prompt')
        )
        
        if result.get('error'):
            logger.error(f"Error analyzing {image_file.name}: {result['error']}")
            print(f"Error: {result['error']}")
            results[image_file.name] = {"error": result['error']}
        else:
            description = result.get('analysis', {}).get('description', 'No description')
            results[image_file.name] = description
            
            preview = description[:100] + "..." if len(description) > 100 else description
            logger.debug(f"Analysis for {image_file.name}: {preview}")
            print(f"✓ {preview}")
    
    logger.info(f"Batch analysis complete. Processed {len(results)} images")
    return results


if __name__ == '__main__':
    main()