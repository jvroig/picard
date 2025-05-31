"""
QwenSense Configuration File

This file contains configuration settings for the QwenSense LLM benchmarking tool.
You can modify these settings to customize the behavior for your environment.
"""
import os
from pathlib import Path

# =============================================================================
# ARTIFACTS DIRECTORY CONFIGURATION
# =============================================================================

# Default artifacts directory - relative to this config file
DEFAULT_ARTIFACTS_DIR = "/Users/jvroig/Dev/sandbox/test_artifacts"

# You can override this by setting the QWENSENSE_ARTIFACTS_DIR environment variable
# or by modifying the ARTIFACTS_DIR setting below

# Primary artifacts directory configuration
# This is where all test files will be generated and stored
ARTIFACTS_DIR = os.environ.get('QWENSENSE_ARTIFACTS_DIR', DEFAULT_ARTIFACTS_DIR)

# Convert to Path object and resolve to absolute path
ARTIFACTS_DIR = Path(ARTIFACTS_DIR).resolve()

# =============================================================================
# OTHER CONFIGURATION OPTIONS
# =============================================================================

# Entity pool file location (relative to config directory)
ENTITY_POOL_FILE = Path(__file__).parent / "config" / "entity_pool.txt"

# Test definitions file location (relative to config directory)  
TEST_DEFINITIONS_FILE = Path(__file__).parent / "config" / "test_definitions.yaml"

# Maximum number of clutter files to generate
MAX_CLUTTER_FILES = 10

# Default file generation settings
DEFAULT_LOREM_LINES = 5
DEFAULT_CSV_ROWS = 5

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_artifacts_dir() -> str:
    """
    Get the configured artifacts directory path as a string.
    
    Returns:
        Absolute path to the artifacts directory
    """
    return str(ARTIFACTS_DIR)

def ensure_artifacts_dir() -> str:
    """
    Ensure the artifacts directory exists and return its path.
    
    Returns:
        Absolute path to the artifacts directory
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return str(ARTIFACTS_DIR)

def get_config_summary() -> dict:
    """
    Get a summary of current configuration settings.
    
    Returns:
        Dictionary with configuration information
    """
    return {
        'artifacts_dir': str(ARTIFACTS_DIR),
        'artifacts_exists': ARTIFACTS_DIR.exists(),
        'entity_pool_file': str(ENTITY_POOL_FILE),
        'test_definitions_file': str(TEST_DEFINITIONS_FILE),
        'config_file': __file__
    }

# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration settings and show warnings if needed."""
    issues = []
    
    # Check if artifacts directory is writable
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        test_file = ARTIFACTS_DIR / ".qwensense_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append(f"Artifacts directory not writable: {e}")
    
    # Check if entity pool exists
    if not ENTITY_POOL_FILE.exists():
        issues.append(f"Entity pool file not found: {ENTITY_POOL_FILE}")
    
    # Check if test definitions exist
    if not TEST_DEFINITIONS_FILE.exists():
        issues.append(f"Test definitions file not found: {TEST_DEFINITIONS_FILE}")
    
    return issues

if __name__ == "__main__":
    # Print configuration summary when run directly
    print("🔧 QwenSense Configuration")
    print("=" * 40)
    
    config = get_config_summary()
    for key, value in config.items():
        print(f"{key:20}: {value}")
    
    print("\n📋 Validation:")
    issues = validate_config()
    if issues:
        for issue in issues:
            print(f"⚠️  {issue}")
    else:
        print("✅ Configuration looks good!")
    
    print(f"\n📁 Artifacts directory: {get_artifacts_dir()}")
    print(f"🏗️  Creating artifacts directory: {ensure_artifacts_dir()}")
