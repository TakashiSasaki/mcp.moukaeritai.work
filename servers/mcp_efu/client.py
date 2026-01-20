import subprocess
import json
import time
import sys

command = [
    "poetry",
    "-q",
    "run",
    "mcp_efu",
    "--transport",
    "stdio"
]

print(f"Running command: {' '.join(command)}")

process = subprocess.Popen(
    command,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

# Give it a moment to start
time.sleep(1) 

request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": "client-test-1"
}

print("\n--- Sending request ---")
print(json.dumps(request))
print("-----------------------\n")

process.stdin.write(json.dumps(request) + '\n')
process.stdin.flush()

try:
    print("--- Reading stdout ---")
    stdout_output = process.stdout.readline()
    print(stdout_output.strip())
    print("----------------------\n")

    print("--- Reading stderr ---")
    # Reading stderr can be tricky, let's do it in a non-blocking way
    # This is simplified, for a real app, select/poll would be better
    time.sleep(0.5)
    stderr_output = process.stderr.read()
    print(stderr_output.strip())
    print("----------------------\n")

finally:
    process.stdin.close()
    process.terminate()
    process.wait(timeout=2)
    process.stdout.close()
    process.stderr.close()

print("Client finished.")
