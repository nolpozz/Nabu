"""
Main entry point for the AI Language Tutor application.
Initializes the application and starts the main window.
"""

import sys
import traceback
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import get_logger, setup_logging
from data.database import DatabaseManager
from data.migrations import run_migrations
from core.application import TutorApplication


def initialize_application() -> bool:
    """Initialize the application and return success status."""
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting AI Language Tutor application")
        logger.info(f"Configuration loaded: {config.to_dict()}")
        
        # Set up logging
        setup_logging()
        
        # Initialize database
        logger.info("Initializing database...")
        db_manager = DatabaseManager()
        
        # Run migrations
        logger.info("Running database migrations...")
        run_migrations(db_manager, create_sample_data=True)
        
        logger.info("Application initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Application initialization failed: {e}", exc_info=True)
        print(f"❌ Initialization Error: {e}")
        print("Please check your configuration and try again.")
        return False


def main():
    """Main application entry point."""
    try:
        # Initialize the application
        if not initialize_application():
            sys.exit(1)
        
        # Create and run the application
        app = TutorApplication()
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Application crashed: {e}", exc_info=True)
        
        print(f"❌ Application Error: {e}")
        print("Check the logs for more details.")
        
        # Print traceback for debugging
        if config.performance.enable_profiling:
            traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    main()


