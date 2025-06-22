"""
Sandbox Reset System - Clean and restore artifacts directory

Provides functions to reset the artifacts sandbox to a known state
using zip file templates. Uses the configured artifacts directory
from qwen_sense_config.py instead of hardcoded paths.
"""
import zipfile
import shutil
import os
from pathlib import Path
from typing import Optional


class SandboxManager:
    """Manages the artifacts sandbox directory using configured location."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize sandbox manager.
        
        Args:
            base_dir: Base directory of the QwenSense project (optional)
        """
        if base_dir is None:
            # Default to parent directory of this script
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        
        # Use artifacts directory from config instead of hardcoded path
        try:
            import sys
            # Add project root to path to import config
            if str(self.base_dir) not in sys.path:
                sys.path.insert(0, str(self.base_dir))
            
            import qwen_sense_config
            self.test_artifacts_dir = Path(qwen_sense_config.get_artifacts_dir())
        except Exception as e:
            # Fallback to old behavior if config can't be loaded
            print(f"⚠️  Warning: Could not load artifacts directory from config ({e})")
            print(f"   Falling back to default: test_artifacts")
            self.test_artifacts_dir = self.base_dir / "test_artifacts"
        
        self.templates_dir = self.base_dir / "test_artifacts_templates"
    
    def list_templates(self) -> list:
        """List available sandbox templates."""
        if not self.templates_dir.exists():
            return []
        
        templates = []
        for zip_file in self.templates_dir.glob("*.zip"):
            templates.append(zip_file.stem)  # filename without .zip extension
        
        return sorted(templates)
    
    def reset_sandbox(self, template: str = "clean_sandbox", verbose: bool = True) -> bool:
        """
        Reset test_artifacts directory from a zip template.
        
        Args:
            template: Name of template (without .zip extension)
            verbose: Whether to print status messages
            
        Returns:
            True if successful, False otherwise
        """
        template_path = self.templates_dir / f"{template}.zip"
        
        if not template_path.exists():
            if verbose:
                print(f"❌ Template not found: {template_path}")
                available = self.list_templates()
                if available:
                    print(f"   Available templates: {available}")
            return False
        
        try:
            # Remove existing test_artifacts directory
            if self.test_artifacts_dir.exists():
                if verbose:
                    print(f"🧹 Removing existing sandbox: {self.test_artifacts_dir}")
                shutil.rmtree(self.test_artifacts_dir)
            
            # Create new directory
            self.test_artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract template
            if verbose:
                print(f"📦 Extracting template: {template}.zip")
            
            with zipfile.ZipFile(template_path, 'r') as zf:
                zf.extractall(self.test_artifacts_dir)
                if verbose:
                    extracted_files = zf.namelist()
                    print(f"📁 Extracted {len(extracted_files)} items")
            
            if verbose:
                print(f"✅ Sandbox reset complete using template: {template}")
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Failed to reset sandbox: {e}")
            return False
    
    def create_template(self, template_name: str, source_dir: Optional[str] = None, 
                       verbose: bool = True) -> bool:
        """
        Create a new template from the current test_artifacts directory.
        
        Args:
            template_name: Name for the new template (without .zip)
            source_dir: Source directory to zip (defaults to test_artifacts)
            verbose: Whether to print status messages
            
        Returns:
            True if successful, False otherwise
        """
        if source_dir is None:
            source_dir = self.test_artifacts_dir
        else:
            source_dir = Path(source_dir)
        
        if not source_dir.exists():
            if verbose:
                print(f"❌ Source directory not found: {source_dir}")
            return False
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_path = self.templates_dir / f"{template_name}.zip"
        
        try:
            if verbose:
                print(f"📦 Creating template: {template_name}.zip")
                print(f"   Source: {source_dir}")
            
            with zipfile.ZipFile(template_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                file_count = 0
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        # Calculate relative path from source directory
                        relative_path = file_path.relative_to(source_dir)
                        zf.write(file_path, relative_path)
                        file_count += 1
                
                if verbose:
                    print(f"📁 Added {file_count} files to template")
            
            if verbose:
                print(f"✅ Template created: {template_path}")
                print(f"📦 Template size: {template_path.stat().st_size} bytes")
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Failed to create template: {e}")
            return False
    
    def get_sandbox_status(self) -> dict:
        """Get current status of the sandbox directory."""
        status = {
            'exists': self.test_artifacts_dir.exists(),
            'path': str(self.test_artifacts_dir),
            'files': [],
            'directories': [],
            'total_items': 0
        }
        
        if status['exists']:
            try:
                for item in self.test_artifacts_dir.rglob('*'):
                    if item.is_file():
                        status['files'].append(str(item.relative_to(self.test_artifacts_dir)))
                    elif item.is_dir():
                        status['directories'].append(str(item.relative_to(self.test_artifacts_dir)))
                
                status['total_items'] = len(status['files']) + len(status['directories'])
            except Exception as e:
                status['error'] = str(e)
        
        return status


def main():
    """Test the sandbox manager."""
    print("🧪 Testing Sandbox Manager")
    print("=" * 30)
    
    manager = SandboxManager()
    
    # Show configuration
    print(f"🔧 Configuration:")
    print(f"   Base directory: {manager.base_dir}")
    print(f"   Artifacts directory: {manager.test_artifacts_dir}")
    print(f"   Templates directory: {manager.templates_dir}")
    print()
    
    # Show available templates
    templates = manager.list_templates()
    print(f"📦 Available templates: {templates}")
    print()
    
    # Show current sandbox status
    status = manager.get_sandbox_status()
    print(f"📁 Current sandbox status:")
    print(f"   Exists: {status['exists']}")
    print(f"   Path: {status['path']}")
    print(f"   Files: {len(status.get('files', []))}")
    print(f"   Directories: {len(status.get('directories', []))}")
    print()
    
    # Test reset
    if templates:
        print(f"🔄 Testing reset with template: {templates[0]}")
        success = manager.reset_sandbox(templates[0])
        
        if success:
            new_status = manager.get_sandbox_status()
            print(f"📊 After reset:")
            print(f"   Files: {len(new_status.get('files', []))}")
            print(f"   Directories: {len(new_status.get('directories', []))}")
    
    print("\n✅ Sandbox manager test completed!")


if __name__ == "__main__":
    main()
