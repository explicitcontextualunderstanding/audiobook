#!/bin/bash
# verification-script.sh
# This script verifies the directory structure and runtime assumptions 
# before building the Sesame CSM Docker container for Jetson Orin

set -e  # Exit on any error
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Sesame CSM Docker Environment Verification ===${NC}"
echo "This script will check if your environment meets all requirements"
echo "for building the Sesame CSM container for Jetson Orin."
echo

# Define the expected directory structure
REPO_ROOT=$(pwd)
REQUIREMENTS_FILE="${REPO_ROOT}/requirements.in"
UTILS_DIR="${REPO_ROOT}/docker/sesame-tts/utils"
ENTRYPOINT_FILE="${REPO_ROOT}/docker/sesame-tts/entrypoint.sh"

# Check for required files and directories
echo -e "${YELLOW}Checking directory structure...${NC}"

# Check requirements.in
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${GREEN}✓ Found requirements.in${NC}"
else
    echo -e "${RED}✗ Missing requirements.in at repository root${NC}"
    echo "  Please create this file with your Python dependencies"
    exit 1
fi

# Check utils directory
if [ -d "$UTILS_DIR" ]; then
    echo -e "${GREEN}✓ Found utils directory${NC}"
else
    echo -e "${RED}✗ Missing utils directory at docker/sesame-tts/utils/${NC}"
    echo "  Please create this directory and add your utility scripts"
    mkdir -p "$UTILS_DIR"
    echo "  Created directory for you. Please add required utilities."
fi

# Check entrypoint.sh
if [ -f "$ENTRYPOINT_FILE" ]; then
    if [ -x "$ENTRYPOINT_FILE" ]; then
        echo -e "${GREEN}✓ Found executable entrypoint.sh${NC}"
    else
        echo -e "${YELLOW}⚠ Found entrypoint.sh but it's not executable${NC}"
        echo "  Making it executable..."
        chmod +x "$ENTRYPOINT_FILE"
        echo -e "${GREEN}✓ Made entrypoint.sh executable${NC}"
    fi
else
    echo -e "${RED}✗ Missing entrypoint.sh at docker/sesame-tts/entrypoint.sh${NC}"
    mkdir -p "$(dirname "$ENTRYPOINT_FILE")"
    cat > "$ENTRYPOINT_FILE" << 'EOF'
#!/bin/bash
# Default entrypoint script
set -e

# Activate conda environment
source /opt/conda/bin/activate tts

# Run whatever command was passed
exec "$@"
EOF
    chmod +x "$ENTRYPOINT_FILE"
    echo -e "${GREEN}✓ Created a basic entrypoint.sh for you${NC}"
fi

# Check for required files in utils
REQUIRED_FILES=(
    "audiobook_generator.py"
    "watermarking.py"
)

echo -e "${YELLOW}Checking for utility scripts...${NC}"
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${UTILS_DIR}/${file}" ]; then
        echo -e "${GREEN}✓ Found ${file}${NC}"
    else
        echo -e "${YELLOW}⚠ Missing ${file} in utils directory${NC}"
        echo "  You may need to create this file before building"
    fi
done

# Check PyTorch version in requirements.in
echo -e "${YELLOW}Checking PyTorch version constraints in requirements.in...${NC}"
TORCH_VERSION=$(grep -E "^torch" "$REQUIREMENTS_FILE" || echo "")

if [[ "$TORCH_VERSION" == *">=2.6.0"* && "$TORCH_VERSION" == *"<2.7.0"* ]]; then
    echo -e "${GREEN}✓ PyTorch version correctly constrained to >=2.6.0,<2.7.0${NC}"
else
    echo -e "${RED}✗ PyTorch version not correctly constrained in requirements.in${NC}"
    echo "  Current entry: $TORCH_VERSION"
    echo "  Required: torch>=2.6.0,<2.7.0"
    echo "  Please update your requirements.in file"
fi

# Check Docker installation and BuildKit
echo -e "${YELLOW}Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    
    # Check Docker version
    DOCKER_VERSION=$(docker --version)
    echo "  Docker version: $DOCKER_VERSION"
    
    # Check if BuildKit is available
    if docker buildx version &> /dev/null; then
        echo -e "${GREEN}✓ Docker BuildKit is available${NC}"
    else
        echo -e "${YELLOW}⚠ Docker BuildKit not found${NC}"
        echo "  BuildKit is recommended for faster builds"
        echo "  You can still build with: DOCKER_BUILDKIT=1 docker build ..."
    fi
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Please install Docker before proceeding"
    exit 1
fi

# Check NVIDIA runtime
echo -e "${YELLOW}Checking NVIDIA Docker runtime...${NC}"
if docker info | grep -i nvidia &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA Docker runtime is installed${NC}"
else
    echo -e "${YELLOW}⚠ NVIDIA Docker runtime not detected${NC}"
    echo "  This is required for GPU access inside the container"
    echo "  See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
fi

# Check GPU availability
echo -e "${YELLOW}Checking GPU availability...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
else
    echo -e "${YELLOW}⚠ nvidia-smi command not available${NC}"
    echo "  Cannot verify GPU availability"
    echo "  If this is a Jetson device, this may be normal"
    
    # Try Jetson-specific command
    if command -v tegrastats &> /dev/null; then
        echo -e "${GREEN}✓ Jetson device detected (tegrastats available)${NC}"
    else
        echo -e "${YELLOW}⚠ Cannot confirm if this is a Jetson device${NC}"
    fi
fi

# Check network connectivity (for downloading models)
echo -e "${YELLOW}Checking network connectivity...${NC}"
if ping -c 1 huggingface.co &> /dev/null; then
    echo -e "${GREEN}✓ Network connectivity to Hugging Face confirmed${NC}"
else
    echo -e "${YELLOW}⚠ Cannot reach huggingface.co${NC}"
    echo "  This is required for downloading the CSM model"
    echo "  Please check your internet connection"
fi

# Check disk space
echo -e "${YELLOW}Checking available disk space...${NC}"
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo "  Available space: $AVAILABLE_SPACE"
AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [[ $AVAILABLE_GB -lt 20 ]]; then
    echo -e "${YELLOW}⚠ Less than 20GB of free space available${NC}"
    echo "  The build process and model download require significant disk space"
else
    echo -e "${GREEN}✓ Sufficient disk space available${NC}"
fi

# Final report
echo
echo -e "${YELLOW}=== Verification Summary ===${NC}"
echo "Your environment is now ready for building the Sesame CSM container."
echo "Use the following command to build:"
echo -e "${GREEN}DOCKER_BUILDKIT=1 docker build -t sesame-tts-jetson -f Dockerfile .${NC}"
echo
echo "After building, test the container with:"
echo -e "${GREEN}docker run --rm --gpus all sesame-tts-jetson python -c 'import torch; print(f\"CUDA available: {torch.cuda.is_available()}\"); import moshi; print(\"Moshi available\")'${NC}"
echo

exit 0