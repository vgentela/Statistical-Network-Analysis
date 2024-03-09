import os
import subprocess
import time

# Define the path to your local repository
repo_path = 'C:\\Users\\Varshney\\Documents\\GitHub\\Statistical-Network-Analysis'

# Set up the Git configuration
os.chdir(repo_path)
subprocess.run(['git', 'config', 'user.email', input('Enter your email')])
subprocess.run(['git', 'config', 'user.name', input('Enter Your Name')])

# Loop indefinitely and check for changes every minute
while True:
    # Pull changes from the remote repository
    subprocess.run(['git', 'pull'])
    
    # Add all changes to the staging area
    subprocess.run(['git', 'add', '.'])
    
    # Commit the changes
    subprocess.run(['git', 'commit', '-m', 'Automated push from local machine'])
    
    # Push changes to the remote repository
    subprocess.run(['git', 'push'])
    
    # Wait for 1 minute before checking for changes again
    time.sleep(300)
