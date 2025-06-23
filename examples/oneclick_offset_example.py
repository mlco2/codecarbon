#!/usr/bin/env python3
"""
Example demonstrating CodeCarbon integration with OneClickImpact for automatic carbon offsetting.

This example shows how to:
1. Track carbon emissions from code execution
2. Automatically offset emissions through OneClickImpact's carbon capture projects when thresholds are reached
3. Configure offset thresholds (minimum 1 kg CO2) and environments (sandbox or production)

Requirements:
- pip install codecarbon[offset]
- OneClickImpact API key (get from https://1clickimpact.com)

Note: Offset amounts are converted to pounds and rounded to whole numbers for the makeimpact SDK.
Emissions below 0.5 kg (~1.1 lbs) will not trigger API calls but will still accumulate.
"""

import time
from codecarbon import EmissionsTracker, track_emissions


def heavy_computation(duration_seconds: int = 3):
    """
    Simulate a CPU-intensive task that will generate emissions
    """
    print(f"Running heavy computation for {duration_seconds} seconds...")
    start_time = time.time()
    
    # Simulate CPU work
    while time.time() - start_time < duration_seconds:
        # Some CPU-intensive work
        _ = sum(i**2 for i in range(1000))
    
    print("Heavy computation completed!")


def example_with_tracker():
    """
    Example using EmissionsTracker object with OneClickImpact integration
    """
    print("\n=== Example 1: Using EmissionsTracker with OneClickImpact ===")
    
    # Initialize tracker with OneClickImpact settings
    tracker = EmissionsTracker(
        project_name="oneclick_demo",
        # OneClickImpact configuration
        offset_api_key="your_api_key_here",  # Replace with your actual API key
        offset_environment="sandbox",  # Use "production" for real offsetting
        offset_threshold=2.0,  # Offset when emissions reach 2 kg CO2 (minimum is 0.5 kg)
        auto_offset=True,  # Automatically offset emissions
        save_to_file=False,  # Disable file output for demo
    )
    
    print("Starting emissions tracking with automatic offsetting...")
    tracker.start()
    
    try:
        # Run some code that generates emissions
        heavy_computation(5)
        
        # Run more code
        heavy_computation(3)
        
    finally:
        emissions = tracker.stop()
        print(f"Total emissions: {emissions:.6f} kg CO2")
        print("Check logs above for offset operations!")


@track_emissions(
    project_name="oneclick_decorator_demo",
    offset_api_key="your_api_key_here",  # Replace with your actual API key
    offset_environment="sandbox",  # Use "production" for real offsetting
    offset_threshold=0.5,  # Offset when emissions reach 0.5 kg CO2 (minimum threshold)
    auto_offset=True,
    save_to_file=False,  # Disable file output for demo
)
def example_with_decorator():
    """
    Example using @track_emissions decorator with OneClickImpact integration
    """
    print("\n=== Example 2: Using @track_emissions decorator with OneClickImpact ===")
    print("Running computation with threshold-based offsetting...")
    
    heavy_computation(4)
    print("Computation with decorator completed!")


def example_manual_offset():
    """
    Example showing manual offset control
    """
    print("\n=== Example 3: Manual offset control ===")
    
    # Create tracker with auto-offset disabled
    tracker = EmissionsTracker(
        project_name="manual_offset_demo",
        offset_api_key="your_api_key_here",  # Replace with your actual API key
        offset_environment="sandbox",
        auto_offset=False,  # Disable automatic offsetting
        save_to_file=False,  # Disable file output for demo
    )
    
    tracker.start()
    
    try:
        heavy_computation(3)
        emissions = tracker.stop()
        
        print(f"Emissions generated: {emissions:.6f} kg CO2")
        
        # Access the OneClickImpact output handler for manual control
        from codecarbon.output_methods.offset import OneClickImpactOutput
        for handler in tracker._output_handlers:
            if isinstance(handler, OneClickImpactOutput):
                print(f"Accumulated emissions: {handler.accumulated_emissions_kg:.6f} kg CO2")
                
                # Manually trigger offset
                if handler.accumulated_emissions_kg > 0:
                    print("Manually triggering offset...")
                    success = handler.manual_offset()
                    if success:
                        print("Manual offset successful!")
                    else:
                        print("Manual offset failed or amount too small!")
                else:
                    print("No accumulated emissions to offset")
                break
        else:
            print("OneClickImpact handler not found - check API key configuration")
            
    except Exception as e:
        print(f"Error during manual offset example: {e}")
        tracker.stop()


def example_with_threshold():
    """
    Example showing threshold-based offsetting
    """
    print("\n=== Example 4: Threshold-based offsetting ===")
    
    tracker = EmissionsTracker(
        project_name="threshold_demo",
        offset_api_key="your_api_key_here",  # Replace with your actual API key
        offset_environment="sandbox",
        offset_threshold=3.0,  # Only offset when reaching 3 kg CO2 (minimum is 0.5 kg)
        auto_offset=True,
        save_to_file=False,  # Disable file output for demo
    )
    
    tracker.start()
    
    try:
        # First computation (might not reach threshold)
        print("First computation (small)...")
        heavy_computation(2)
        
        # Second computation (might reach threshold)
        print("Second computation (larger)...")
        heavy_computation(4)
        
    finally:
        emissions = tracker.stop()
        print(f"Total emissions: {emissions:.6f} kg CO2")


def example_environment_comparison():
    """
    Example showing the difference between sandbox and production environments
    """
    print("\n=== Example 5: Environment comparison ===")
    
    print("Sandbox environment (testing - no real offsets):")
    tracker_sandbox = EmissionsTracker(
        project_name="sandbox_demo",
        offset_api_key="your_api_key_here",
        offset_environment="sandbox",  # Testing environment
        offset_threshold=1.0,
        auto_offset=True,
        save_to_file=False,
    )
    
    tracker_sandbox.start()
    heavy_computation(2)
    emissions_sandbox = tracker_sandbox.stop()
    print(f"Sandbox emissions: {emissions_sandbox:.6f} kg CO2")
    
    print("\nProduction environment (real offsets - commented out for safety):")
    print("# tracker_production = EmissionsTracker(")
    print("#     project_name='production_demo',")
    print("#     offset_api_key='your_api_key_here',")
    print("#     offset_environment='production',  # Real carbon offsets!")
    print("#     offset_threshold=1.0,")
    print("#     auto_offset=True,")
    print("#     save_to_file=False,")
    print("# )")
    print("# Note: Production environment will create real carbon offsets!")


if __name__ == "__main__":
    print("OneClickImpact Carbon Offset Integration Examples")
    print("=" * 50)
    print("\nNOTE: These examples use 'sandbox' environment.")
    print("For real carbon offsetting, change 'offset_environment' to 'production'")
    print("and replace 'your_api_key_here' with your actual OneClickImpact API key.")
    print("\nTo get an API key, visit: https://1clickimpact.com")
    print("\nIMPORTANT: Emissions below 0.5 kg (~1.1 lbs) will accumulate but not trigger API calls.")
    print("This prevents excessive API requests for very small amounts.\n")
    
    try:
        # Run all examples
        example_with_tracker()
        example_with_decorator()
        example_manual_offset()
        example_with_threshold()
        example_environment_comparison()
        
        print("\n" + "=" * 50)
        print("All examples completed!")
        print("\nKey Features Demonstrated:")
        print("- Automatic carbon offsetting when thresholds are reached")
        print("- Configurable offset thresholds (minimum 0.5 kg CO2)")
        print("- Manual offset control for accumulated emissions")
        print("- Integration with both tracker objects and decorators")
        print("- Sandbox vs production environments")
        print("- Minimum 1 lb API call threshold to prevent excessive requests")
        
    except ImportError as e:
        if "makeimpact" in str(e):
            print("ERROR: OneClickImpact SDK not installed.")
            print("Please install it using: pip install makeimpact")
            print("Note: codecarbon[offset] may not be available yet")
        else:
            print(f"Import error: {e}")
    except Exception as e:
        print(f"Example error: {e}")
        print("\nNote: If you see API errors,")
        print("make sure to replace 'your_api_key_here' with a valid API key!")
