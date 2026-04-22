import os
import base64
import tarfile
import io

def generate_deployment_script():
    print("--- AWS One-Click Deployment Generator ---")
    
    # 1. Files to include
    files_to_include = [
        "main.py", "config.py", "scraper.py", "database.py", "utils.py", 
        "ai_content.py", "discovery.py", "requirements.txt", ".env", "bot.py"
    ]
    
    # 2. Create a tarball in memory
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for f in files_to_include:
            if os.path.exists(f):
                tar.add(f)
            else:
                print(f"⚠️ Warning: {f} not found, skipping...")
    
    # 3. Encode to Base64
    b64_project = base64.b64encode(tar_buffer.getvalue()).decode('utf-8')
    
    # 4. Define the CloudShell Bash Script
    # This script will be pasted into AWS CloudShell
    cloudshell_script = f"""
# --- START OF AWS MAGIC SCRIPT ---
# 1. Setup Variables
INSTANCE_NAME="Loot-Deal-Agent"
REGION="us-east-1" 

echo "Checking for existing Key Pair..."
if ! aws ec2 describe-key-pairs --key-names "loot-key" --region $REGION > /dev/null 2>&1; then
    echo "Creating new key pair: loot-key"
    aws ec2 create-key-pair --key-name "loot-key" --region $REGION --query 'KeyMaterial' --output text > loot-key.pem
    chmod 400 loot-key.pem
fi

echo "Setting up Security Group..."
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=loot-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group --group-name "loot-sg" --description "Security group for Loot Bot" --region $REGION --query 'GroupId' --output text)
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $REGION
fi

# 5. EC2 UserData (The script that runs inside the server)
cat << 'EOF_UD' > user_data.sh
#!/bin/bash
sudo apt update -y
sudo apt install -y python3-pip python3-venv git nodejs npm
sudo npm install -g pm2

# Setup Project
mkdir -p /home/ubuntu/loot_bot
cd /home/ubuntu/loot_bot

# Decode the project code
echo "{b64_project}" | base64 -d > project.tar.gz
tar -xzf project.tar.gz

# Install Python deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start with PM2
pm2 start main.py --name "loot-bot" --interpreter ./venv/bin/python
pm2 save
pm2 startup
EOF_UD

echo "Launching EC2 Instance (Free Tier)..."
aws ec2 run-instances \\
    --image-id ami-0e2c8ccd4e0269736 \\
    --count 1 \\
    --instance-type t2.micro \\
    --key-name loot-key \\
    --security-group-ids $SG_ID \\
    --user-data file://user_data.sh \\
    --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=$INSTANCE_NAME}}]" \\
    --region $REGION

echo "--- DEPLOYMENT COMMAND SENT! ---"
echo "Your bot will be live in ~2-3 minutes."
echo "You can check the status in the EC2 Console."
# --- END OF AWS MAGIC SCRIPT ---
"""

    output_file = "aws_magic_script.sh"
    with open(output_file, "w") as f:
        f.write(cloudshell_script)
    
    print(f"\nSUCCESS! I have generated '{output_file}'.")
    print("1. Open 'aws_magic_script.sh' in your editor.")
    print("2. Copy ALL the text inside.")
    print("3. Go to AWS Console -> Open CloudShell (icon at top right).")
    print("4. Paste the text and press Enter.")

if __name__ == "__main__":
    generate_deployment_script()
