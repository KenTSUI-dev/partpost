import argparse
import json
import os
import sys
from partpost.proc import ncTrk2pt, ncTrk2line

def process_task(task):
    """
    Process a single task dictionary from the config.
    """
    nc_file = task.get("input_nc")
    output_path = task.get("output_path")
    mode = task.get("mode", "point").lower()  # 'point' or 'line'
    downscale_hour = task.get("downscale_hour", 1.0)

    if not nc_file or not output_path:
        print(f"❌ Error: Task missing 'input_nc' or 'output_path'")
        return

    print(f"\n🚀 Starting Task: {mode.upper()} -> {os.path.basename(output_path)}")

    try:
        if mode == "line":
            ncTrk2line(nc_file, output_path, downscale_hours=downscale_hour)
        elif mode == "point":
            ncTrk2pt(nc_file, output_path, downscale_hours=downscale_hour)
        else:
            print(f"❌ Error: Unknown mode '{mode}'. Use 'point' or 'line'.")
    except Exception as e:
        print(f"❌ Error processing task: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(
        description="partpost: Delft3D FM Particle Tracking Post-processor"
    )
    parser.add_argument(
        "config",
        help="Path to the JSON configuration file."
    )

    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        sys.exit(1)

    # Support both a list of tasks or a single object
    tasks = []
    if isinstance(config, list):
        tasks = config
    elif isinstance(config, dict):
        # If it's a dict, check if it has a "tasks" key, or treat it as single task
        if "tasks" in config and isinstance(config["tasks"], list):
            tasks = config["tasks"]
        else:
            tasks = [config]

    print(f"📋 Found {len(tasks)} tasks to process.")

    for task in tasks:
        process_task(task)

    print("\n✨ All tasks completed.")

if __name__ == "__main__":
    main()