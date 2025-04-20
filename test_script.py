# test_script.py

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arguments = sys.argv[1:]
        print(f"Script was called with the following arguments: {arguments}")
        # You can process the arguments here if needed
    else:
        print("Script was called successfully!")