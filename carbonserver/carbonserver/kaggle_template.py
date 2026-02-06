"""
Template class for Kaggle script boilerplate.
Can be imported and used programmatically instead of reading from file.
Uses CST Module to avoid parsing on every use.
"""

import libcst as cst

class KaggleScriptTemplate:
    """Template for Kaggle script with codecarbon tracking"""
    
    # Store as CST Module (pre-parsed) for efficiency
    TEMPLATE_MODULE = cst.parse_module("""from codecarbon import EmissionsTracker
tracker = EmissionsTracker(api_endpoint=api_endpoint, api_key=api_key, experiment_id=experiment_id, output_dir='./', save_to_api=True)
def injected_kernel():
    #INJECTED KERNEL CODE
    print("Hello From Kaggle")
tracker.start()
try:
    injected_kernel()
finally:
    emissions = tracker.stop()
print(f'CO2 emissions: {emissions} kg')
""")
    
    # Kernel metadata configuration
    METADATA_CONFIG = {
        "id": "demo_user/test_notebook",  # username/kernel-slug
        "title": "test_notebook",
        "code_file": "test.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": []
    }
    
    @classmethod
    def get_template(cls) -> cst.Module:
        """Get the template as CST Module (no parsing needed)"""
        return cls.TEMPLATE_MODULE
    
    @classmethod
    def get_template_code(cls) -> str:
        """Get the template code as string (if needed for debugging)"""
        return cls.TEMPLATE_MODULE.code
    
    @classmethod
    def get_metadata(cls) -> dict:
        """Get the kernel metadata configuration"""
        return cls.METADATA_CONFIG.copy()  # Return copy to prevent accidental modification