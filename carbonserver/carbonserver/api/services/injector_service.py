import libcst as cst
import tempfile
import os
import shutil
from typing import Dict, Optional

class Injector:
    """
    Unified injector for Python files using libcst.
    Handles both variable and function injection.
    All operations work on temp files automatically.
    """
    
    def __init__(self, python_file_path: str = None, code: str = None, 
                 module: cst.Module = None, filename: str = "script.py"):
        """
        Args:
            python_file_path: Path to original Python file (read-only, copied to temp)
            code: Python code as string (alternative to file_path)
            module: CST Module object (most efficient - no parsing needed)
            filename: Name for temp file (used when code/module is provided)
        """
        # Validate arguments
        provided = sum([bool(python_file_path), bool(code), bool(module)])
        if provided > 1:
            raise ValueError("Cannot provide multiple sources (python_file_path, code, or module)")
        if provided == 0:
            raise ValueError("Must provide either python_file_path, code, or module")
        
        # Get module from file, string, or use provided CST Module
        if python_file_path:
            self.python_file_path = python_file_path
            # Read original file (read-only)
            with open(python_file_path, 'r', encoding='utf-8') as f:
                self._original_code = f.read()
            temp_filename = os.path.basename(python_file_path)
            # Parse using libcst
            self._module = cst.parse_module(self._original_code)
        elif module:
            self.python_file_path = None
            # Use provided CST Module (no parsing needed!)
            self._module = module
            self._original_code = module.code
            temp_filename = filename
        else:  # code string
            self.python_file_path = None
            self._original_code = code
            # Parse using libcst
            self._module = cst.parse_module(code)
            temp_filename = filename
        
        # Create temp directory and file immediately
        self._temp_dir = tempfile.mkdtemp()
        self._temp_file_path = os.path.join(self._temp_dir, temp_filename)
        
        # Write initial copy to temp file
        with open(self._temp_file_path, 'w', encoding='utf-8') as f:
            f.write(self._original_code)
        
        # File pointer is closed, all future ops use temp file
    
    def _create_value_node(self, value):
        """Helper to create CST value node from Python value"""
        type_map = {
            str: lambda v: cst.SimpleString(f'"{v}"'),
            int: lambda v: cst.Integer(str(v)),
            float: lambda v: cst.Float(str(v)),
            bool: lambda v: cst.Name("True" if v else "False"),
            type(None): lambda v: cst.Name("None"),
        }
        return type_map.get(type(value), lambda v: cst.SimpleString(f'"{str(v)}"'))(value)
    
    def inject_variables(self, variables: Dict[str, any]):
        """
        Inject variable assignments into the file.
        
        Args:
            variables: Dictionary of variable names and values
            at_top: If True, injects at top of file; if False, at end
        
        Returns:
            self (for chaining)
        """
        assignments = [
            cst.SimpleStatementLine(body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name(var_name))],
                    value=self._create_value_node(var_value)
                )
            ])
            for var_name, var_value in variables.items()
        ]
        
        # Apply transformation directly by modifying module body
        new_body = list(self._module.body)
        # Insert at beginning
        new_body = assignments + new_body

        self._module = self._module.with_changes(body=new_body)
        self._save_to_temp()
        
        return self
    
    def add_dependency(self, packages: list):
        """
        Add pip install command at the top of the file using os.system.
        Also ensures 'import os' is present.
        
        Args:
            packages: List of package names to install
        
        Returns:
            self (for chaining)
        """
        if not packages:
            return self
        
        # Check if 'import os' already exists
        has_os_import = False
        for item in self._module.body:
            if isinstance(item, cst.SimpleStatementLine):
                for stmt in item.body:
                    if isinstance(stmt, cst.Import):
                        for alias in stmt.names:
                            if alias.name.value == 'os':
                                has_os_import = True
                                break
                    elif isinstance(stmt, cst.ImportFrom) and stmt.module and stmt.module.value == 'os':
                        has_os_import = True
                        break
        
        # Create pip install command
        packages_str = ' '.join(packages)
        pip_command = f'pip install {packages_str}'
        
        # Create os.system call
        os_system_call = cst.SimpleStatementLine(body=[
            cst.Expr(value=cst.Call(
                func=cst.Attribute(
                    value=cst.Name('os'),
                    attr=cst.Name('system')
                ),
                args=[cst.Arg(value=cst.SimpleString(f'"{pip_command}"'))]
            ))
        ])
        
        # Build new body
        new_body = list(self._module.body)
        
        # Add import os if not present
        if not has_os_import:
            os_import = cst.SimpleStatementLine(body=[
                cst.Import(names=[cst.ImportAlias(name=cst.Name('os'))])
            ])
            new_body.insert(0, os_import)
            # Insert os.system call after import
            new_body.insert(1, os_system_call)
        else:
            # Just insert os.system call at top
            new_body.insert(0, os_system_call)
        
        self._module = self._module.with_changes(body=new_body)
        self._save_to_temp()
        
        return self
    
    def inject_function(self, code: str, func_name: str):
        """
        Inject code into existing function's body by replacing its body content.
        
        Args:
            code: Python code string to inject into function body
            func_name: Name of the existing function to modify
        
        Returns:
            self (for chaining)
        """
        # Parse injected code as module to get statements
        injected_module = cst.parse_module(code)
        body_statements = list(injected_module.body)
        
        # Replace function body directly
        new_body = [
            item.with_changes(body=cst.IndentedBlock(body=body_statements))
            if isinstance(item, cst.FunctionDef) and item.name.value == func_name
            else item
            for item in self._module.body
        ]
        self._module = self._module.with_changes(body=new_body)
        
        self._save_to_temp()
        return self
    
    def _save_to_temp(self):
        """Internal: Save modified code to temp file"""
        with open(self._temp_file_path, 'w', encoding='utf-8') as f:
            f.write(self._module.code)
    
    def get_temp_file_path(self) -> str:
        """Get path to temporary file"""
        return self._temp_file_path
    
    def get_temp_dir(self) -> str:
        """Get path to temporary directory"""
        return self._temp_dir
    
    def get_code(self) -> str:
        """Get the modified code as string (for inspection)"""
        return self._module.code
    
    def destroy(self):
        """
        Destroy all temporary files and directory.
        Call this when done with temp files.
        """
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None
            self._temp_file_path = None
    
    def __del__(self):
        """Automatically clean up temp files when object is destroyed"""
        # Only destroy if temp_dir still exists (destroy() not already called)
        if hasattr(self, '_temp_dir') and self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except (OSError, AttributeError):
                # Ignore errors during destruction (temp files may already be cleaned up)
                pass
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.destroy()
