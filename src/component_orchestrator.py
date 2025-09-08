"""
Component Orchestrator for PICARD Multi-Component Sandbox Setup

Handles creation of multiple sandbox components with dependency resolution.
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import logging

from .test_definition_parser import ComponentSpec

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ComponentResult:
    """Result of creating a single sandbox component."""
    component_name: str
    component_type: str
    target_file: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            'component_name': self.component_name,
            'component_type': self.component_type,
            'success': self.success
        }
        if self.target_file:
            result['target_file'] = self.target_file
        if self.error_message:
            result['error_message'] = self.error_message
        if self.metadata:
            result['metadata'] = self.metadata
        return result


class DependencyResolver:
    """Resolves component dependencies using topological sorting."""
    
    def resolve_dependencies(self, components: List[ComponentSpec]) -> List[ComponentSpec]:
        """Order components based on dependencies using topological sort."""
        
        # Create component lookup by name (all components MUST have names now)
        component_map = {}
        for comp in components:
            if not comp.name:
                raise ValueError(f"Component of type '{comp.type}' missing required 'name' field")
            if comp.name in component_map:
                raise ValueError(f"Duplicate component name: '{comp.name}'")
            component_map[comp.name] = comp
        
        # Build dependency graph
        graph = {name: set() for name in component_map.keys()}
        in_degree = {name: 0 for name in component_map.keys()}
        
        for name, comp in component_map.items():
            if comp.depends_on:
                for dep in comp.depends_on:
                    if dep not in component_map:
                        raise ValueError(f"Component '{name}' depends on unknown component '{dep}'")
                    graph[dep].add(name)
                    in_degree[name] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        ordered_names = []
        
        while queue:
            current = queue.pop(0)
            ordered_names.append(current)
            
            # Update dependencies
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(ordered_names) != len(components):
            remaining = [name for name, degree in in_degree.items() if degree > 0]
            raise ValueError(f"Circular dependency detected among components: {remaining}")
        
        # Return components in dependency order
        return [component_map[name] for name in ordered_names]


class ComponentOrchestrator:
    """Manages creation of multiple sandbox components."""
    
    def __init__(self, file_generator_factory=None):
        """Initialize with optional file generator factory."""
        self.dependency_resolver = DependencyResolver()
        self.file_generator_factory = file_generator_factory
    
    def create_components(self, components: List[ComponentSpec], 
                         question_id: int, sample_number: int,
                         artifacts_dir: str = None) -> List[ComponentResult]:
        """Create all components in dependency order."""
        
        if not components:
            return []
        
        # Resolve dependencies
        try:
            ordered_components = self.dependency_resolver.resolve_dependencies(components)
        except ValueError as e:
            logger.error(f"Dependency resolution failed: {e}")
            return [ComponentResult(
                component_name=f"component_{i}",
                component_type=comp.type,
                success=False,
                error_message=str(e)
            ) for i, comp in enumerate(components)]
        
        # Create components in order
        results = []
        created_files = {}  # Track created files for dependency references
        
        for comp in ordered_components:
            result = self._create_component(comp, question_id, sample_number, 
                                          artifacts_dir, created_files)
            results.append(result)
            
            # Track successful file creation
            if result.success and result.target_file:
                created_files[comp.name] = result.target_file
        
        return results
    
    def _create_component(self, component: ComponentSpec, question_id: int, 
                         sample_number: int, artifacts_dir: str = None,
                         created_files: Dict[str, str] = None) -> ComponentResult:
        """Create a single component."""
        
        component_name = component.name
        
        try:
            # Handle file generation components
            if component.type.startswith('create_'):
                return self._create_file_component(component, question_id, sample_number, 
                                                 artifacts_dir, component_name)
            
            # Handle infrastructure components (future)
            elif component.type.startswith('run_'):
                return self._create_infrastructure_component(component, component_name)
            
            else:
                raise ValueError(f"Unknown component type: {component.type}")
                
        except Exception as e:
            logger.exception(f"Failed to create component {component_name}")
            return ComponentResult(
                component_name=component_name,
                component_type=component.type,
                success=False,
                error_message=str(e)
            )
    
    def _create_file_component(self, component: ComponentSpec, question_id: int,
                              sample_number: int, artifacts_dir: str = None,
                              component_name: str = 'unknown') -> ComponentResult:
        """Create a file-based component (CSV, JSON, YAML, etc.)."""
        
        if not self.file_generator_factory:
            # For now, return a placeholder result
            # In real implementation, this would use the file generator factory
            return ComponentResult(
                component_name=component_name,
                component_type=component.type,
                target_file=component.target_file,
                success=True,
                metadata={"note": "File generator factory not configured"}
            )
        
        # Use the factory to create the appropriate generator
        try:
            generator = self.file_generator_factory.create_component(component, artifacts_dir)
            
            # Generate the file using the correct interface
            result_info = generator.generate(component.target_file, component.content, 
                                           component.config)  # Pass full config (includes clutter, etc.)
            
            return ComponentResult(
                component_name=component_name,
                component_type=component.type,
                target_file=component.target_file,  # Use the target file path
                success=True,
                metadata={
                    "generator_type": type(generator).__name__,
                    "generator_result": result_info
                }
            )
            
        except Exception as e:
            return ComponentResult(
                component_name=component_name,
                component_type=component.type,
                target_file=component.target_file,
                success=False,
                error_message=str(e)
            )
    
    def _create_infrastructure_component(self, component: ComponentSpec,
                                       component_name: str = 'unknown') -> ComponentResult:
        """Create an infrastructure component (Docker, services, etc.)."""
        
        # Placeholder for future infrastructure support
        return ComponentResult(
            component_name=component_name,
            component_type=component.type,
            success=True,
            metadata={"note": "Infrastructure components not yet implemented"}
        )


class EnhancedFileGeneratorFactory:
    """Extended factory supporting multi-component scenarios."""
    
    def __init__(self):
        """Initialize the factory."""
        # Import here to avoid circular imports
        self._generators = {}
        self._setup_generators()
    
    def _setup_generators(self):
        """Set up generator mappings."""
        try:
            from .file_generators import (
                TextFileGenerator, CSVFileGenerator, SQLiteFileGenerator,
                JSONFileGenerator, YAMLFileGenerator, XMLFileGenerator
            )
            
            self._generators = {
                'create_files': TextFileGenerator,
                'create_csv': CSVFileGenerator,
                'create_sqlite': SQLiteFileGenerator,
                'create_json': JSONFileGenerator,
                'create_yaml': YAMLFileGenerator,
                'create_xml': XMLFileGenerator
            }
        except ImportError as e:
            logger.warning(f"Could not import file generators: {e}")
            self._generators = {}
    
    def create_component(self, component_spec: ComponentSpec, artifacts_dir: str = None):
        """Create appropriate generator for component type."""
        
        if component_spec.type.startswith('create_'):
            return self._create_file_generator(component_spec, artifacts_dir)
        elif component_spec.type.startswith('run_'):
            return self._create_infrastructure_component(component_spec)
        else:
            raise ValueError(f"Unknown component type: {component_spec.type}")
    
    def _create_file_generator(self, component_spec: ComponentSpec, artifacts_dir: str = None):
        """Create file generator for component."""
        
        generator_class = self._generators.get(component_spec.type)
        if not generator_class:
            raise ValueError(f"No generator available for type: {component_spec.type}")
        
        return generator_class(base_dir=artifacts_dir)
    
    def _create_infrastructure_component(self, component_spec: ComponentSpec):
        """Create infrastructure component (future implementation)."""
        raise NotImplementedError(f"Infrastructure components not yet supported: {component_spec.type}")
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported component types."""
        return list(self._generators.keys())


# Convenience function for creating multi-component sandboxes
def create_multi_component_sandbox(components: List[ComponentSpec], 
                                 question_id: int, sample_number: int,
                                 artifacts_dir: str = None) -> List[ComponentResult]:
    """
    Convenience function to create a multi-component sandbox.
    
    Args:
        components: List of component specifications
        question_id: Question ID for the test
        sample_number: Sample number within the question
        artifacts_dir: Artifacts directory path (optional)
    
    Returns:
        List of ComponentResult objects indicating success/failure
    """
    
    factory = EnhancedFileGeneratorFactory()
    orchestrator = ComponentOrchestrator(factory)
    
    return orchestrator.create_components(components, question_id, sample_number, artifacts_dir)