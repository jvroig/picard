"""
Test Component Orchestrator

Tests multi-component sandbox creation and dependency resolution.
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.component_orchestrator import (
    ComponentOrchestrator, DependencyResolver, ComponentResult,
    EnhancedFileGeneratorFactory, create_multi_component_sandbox
)
from src.test_definition_parser import ComponentSpec


class TestDependencyResolver:
    """Test dependency resolution logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = DependencyResolver()
    
    def test_no_dependencies(self):
        """Test components with no dependencies."""
        components = [
            ComponentSpec(type="create_csv", name="csv_comp", target_file="file1.csv"),
            ComponentSpec(type="create_json", name="json_comp", target_file="file2.json"),
            ComponentSpec(type="create_yaml", name="yaml_comp", target_file="file3.yaml")
        ]
        
        ordered = self.resolver.resolve_dependencies(components)
        
        assert len(ordered) == 3
        # Order should be preserved when no dependencies
        assert ordered[0].type == "create_csv"
        assert ordered[1].type == "create_json"
        assert ordered[2].type == "create_yaml"
    
    def test_simple_linear_dependencies(self):
        """Test linear dependency chain."""
        components = [
            ComponentSpec(type="create_json", name="json_config", target_file="config.json", depends_on=["csv_data"]),
            ComponentSpec(type="create_csv", name="csv_data", target_file="data.csv"),  # No dependencies
            ComponentSpec(type="create_yaml", name="yaml_output", target_file="output.yaml", depends_on=["json_config"])
        ]
        
        ordered = self.resolver.resolve_dependencies(components)
        
        assert len(ordered) == 3
        # csv_data should come first (no dependencies)
        assert ordered[0].type == "create_csv"
        # json_config should come second (depends on csv_data)
        assert ordered[1].type == "create_json"
        # yaml_output should come last (depends on json_config)
        assert ordered[2].type == "create_yaml"
    
    def test_complex_dependencies(self):
        """Test complex dependency graph."""
        components = [
            ComponentSpec(type="create_yaml", name="final_yaml", target_file="final.yaml", depends_on=["processed_json", "summary_csv"]),
            ComponentSpec(type="create_json", name="processed_json", target_file="processed.json", depends_on=["raw_csv"]),
            ComponentSpec(type="create_csv", name="raw_csv", target_file="raw.csv"),  # No dependencies
            ComponentSpec(type="create_csv", name="summary_csv", target_file="summary.csv", depends_on=["raw_csv"])
        ]
        
        ordered = self.resolver.resolve_dependencies(components)
        
        assert len(ordered) == 4
        # raw_csv should come first
        assert ordered[0].name == "raw_csv"
        # processed_json and summary_csv can come in any order (both depend only on raw_csv)
        middle_names = {ordered[1].name, ordered[2].name}
        assert middle_names == {"processed_json", "summary_csv"}
        # final_yaml should come last
        assert ordered[3].name == "final_yaml"
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        components = [
            ComponentSpec(type="create_csv", name="comp1", target_file="file1.csv", depends_on=["comp2"]),
            ComponentSpec(type="create_json", name="comp2", target_file="file2.json", depends_on=["comp1"])
        ]
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            self.resolver.resolve_dependencies(components)
    
    def test_missing_dependency(self):
        """Test error when component depends on non-existent component."""
        components = [
            ComponentSpec(type="create_csv", name="comp1", target_file="file1.csv", depends_on=["nonexistent"])
        ]
        
        with pytest.raises(ValueError, match="depends on unknown component 'nonexistent'"):
            self.resolver.resolve_dependencies(components)


class TestComponentOrchestrator:
    """Test component orchestration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = ComponentOrchestrator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_components_list(self):
        """Test handling of empty components list."""
        results = self.orchestrator.create_components([], 1, 1, artifacts_dir=self.temp_dir)
        assert results == []
    
    def test_single_component_creation(self):
        """Test creating a single component."""
        components = [
            ComponentSpec(type="create_csv", name="test_csv", target_file="test.csv",
                         content={"headers": ["id", "name"], "rows": 10})
        ]
        
        results = self.orchestrator.create_components(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 1
        result = results[0]
        assert result.component_type == "create_csv"
        assert result.target_file == "test.csv"
        assert result.success == True
        assert "File generator factory not configured" in result.metadata["note"]
    
    def test_multiple_components_no_dependencies(self):
        """Test creating multiple independent components."""
        components = [
            ComponentSpec(type="create_csv", name="data_csv", target_file="data.csv"),
            ComponentSpec(type="create_json", name="config_json", target_file="config.json"),
            ComponentSpec(type="create_yaml", name="settings_yaml", target_file="settings.yaml")
        ]
        
        results = self.orchestrator.create_components(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success == True
            assert result.component_type == components[i].type
            assert result.target_file == components[i].target_file
    
    def test_dependency_order_maintained(self):
        """Test that components are created in dependency order."""
        components = [
            ComponentSpec(type="create_json", name="config", target_file="config.json", depends_on=["data"]),
            ComponentSpec(type="create_csv", name="data", target_file="data.csv"),
            ComponentSpec(type="create_yaml", name="output", target_file="output.yaml", depends_on=["config"])
        ]
        
        results = self.orchestrator.create_components(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 3
        # Should be created in dependency order: data, config, output
        assert results[0].component_type == "create_csv"  # data first
        assert results[1].component_type == "create_json" # config second
        assert results[2].component_type == "create_yaml" # output last
    
    def test_error_propagation(self):
        """Test that dependency errors are properly handled."""
        components = [
            ComponentSpec(type="create_csv", name="csv_comp", target_file="file1.csv", depends_on=["missing"]),
            ComponentSpec(type="create_json", name="json_comp", target_file="file2.json")
        ]
        
        results = self.orchestrator.create_components(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 2
        # All components should fail due to dependency resolution error
        for result in results:
            assert result.success == False
            assert "depends on unknown component" in result.error_message
    
    def test_infrastructure_component_placeholder(self):
        """Test placeholder handling for infrastructure components."""
        components = [
            ComponentSpec(type="run_docker", name="postgres_db", config={"image": "postgres:13"})
        ]
        
        results = self.orchestrator.create_components(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 1
        result = results[0]
        assert result.component_type == "run_docker"
        assert result.success == True
        assert "Infrastructure components not yet implemented" in result.metadata["note"]


class TestEnhancedFileGeneratorFactory:
    """Test enhanced file generator factory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = EnhancedFileGeneratorFactory()
    
    def test_supported_types(self):
        """Test getting supported component types."""
        supported = self.factory.get_supported_types()
        
        # Should include standard file generators
        expected_types = ['create_files', 'create_csv', 'create_sqlite', 
                         'create_json', 'create_yaml', 'create_xml']
        
        for expected_type in expected_types:
            assert expected_type in supported
    
    def test_create_file_component(self):
        """Test creating file generator components."""
        component = ComponentSpec(type="create_csv", name="test_csv", target_file="test.csv")
        
        try:
            generator = self.factory.create_component(component)
            # Should return a generator instance
            assert generator is not None
            assert hasattr(generator, 'generate')
        except ImportError:
            # File generators might not be available in test environment
            pytest.skip("File generators not available in test environment")
    
    def test_infrastructure_component_not_implemented(self):
        """Test that infrastructure components raise NotImplementedError."""
        component = ComponentSpec(type="run_docker", name="docker_comp")
        
        with pytest.raises(NotImplementedError, match="Infrastructure components not yet supported"):
            self.factory.create_component(component)
    
    def test_unknown_component_type(self):
        """Test error handling for unknown component types."""
        component = ComponentSpec(type="unknown_type", name="unknown_comp")
        
        with pytest.raises(ValueError, match="Unknown component type"):
            self.factory.create_component(component)


class TestComponentResult:
    """Test component result data structure."""
    
    def test_successful_result_to_dict(self):
        """Test successful result serialization."""
        result = ComponentResult(
            component_name="test_comp",
            component_type="create_csv",
            target_file="test.csv",
            success=True,
            metadata={"rows": 100}
        )
        
        result_dict = result.to_dict()
        
        expected = {
            'component_name': 'test_comp',
            'component_type': 'create_csv',
            'target_file': 'test.csv',
            'success': True,
            'metadata': {'rows': 100}
        }
        
        assert result_dict == expected
    
    def test_failed_result_to_dict(self):
        """Test failed result serialization."""
        result = ComponentResult(
            component_name="failed_comp",
            component_type="create_json",
            success=False,
            error_message="Generation failed"
        )
        
        result_dict = result.to_dict()
        
        expected = {
            'component_name': 'failed_comp',
            'component_type': 'create_json',
            'success': False,
            'error_message': 'Generation failed'
        }
        
        assert result_dict == expected
    
    def test_minimal_result_to_dict(self):
        """Test minimal result serialization."""
        result = ComponentResult(
            component_name="minimal",
            component_type="run_service"
        )
        
        result_dict = result.to_dict()
        
        expected = {
            'component_name': 'minimal',
            'component_type': 'run_service',
            'success': True
        }
        
        assert result_dict == expected


class TestConvenienceFunction:
    """Test convenience function for multi-component sandbox creation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_multi_component_sandbox(self):
        """Test the convenience function."""
        components = [
            ComponentSpec(type="create_csv", name="data_csv", target_file="data.csv", 
                         content={"headers": ["id", "name"], "rows": 5}),
            ComponentSpec(type="create_json", name="config_json", target_file="config.json",
                         content={"schema": {"type": "object", "properties": {"test": {"type": "string"}}}})
        ]
        
        results = create_multi_component_sandbox(components, 1, 1, artifacts_dir=self.temp_dir)
        
        assert len(results) == 2
        for result in results:
            assert result.success == True
            assert result.component_type in ["create_csv", "create_json"]