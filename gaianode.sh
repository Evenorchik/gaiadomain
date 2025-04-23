#!/bin/bash

# Text color
CYAN='\033[0;36m'
NC='\033[0m'

# Clear screen
clear

# Check if curl is installed and install if missing
if ! command -v curl &> /dev/null; then
    sudo apt update
    sudo apt install -y curl
fi

# Display logo
curl -s https://raw.githubusercontent.com/Evenorchik/evenorlogo/main/evenorlogo.sh | bash

# Function to display the menu
print_menu() {
    echo -e "${CYAN}Available actions:\n"
    echo -e "${CYAN}[1] -> Install Gaia node${NC}"
    echo -e "${CYAN}[2] -> Start farming script (Gaia bot)${NC}"
    echo -e "${CYAN}[3] -> Update Gaia node${NC}"
    echo -e "${CYAN}[4] -> Gaia node info${NC}"
    echo -e "${CYAN}[5] -> Delete Gaia node${NC}"
    echo -e "${CYAN}[6] -> View farming script logs${NC}"
    echo -e "${CYAN}[7] -> Delete farming script${NC}\n"
}

# Display menu
print_menu

# Prompt user for choice
echo -e "${CYAN}Enter action number [1-7]:${NC}"
read -p "-> " choice

case $choice in
    1)
        echo -e "\n${CYAN}Installing Gaia node...${NC}\n"

        echo -e "${CYAN}[1/6] -> Updating system...${NC}"
        sudo apt update && sudo apt upgrade -y
        sudo apt install -y python3-pip python3-dev python3-venv curl git build-essential
        pip3 install aiohttp

        echo -e "${CYAN}[2/6] -> Freeing port 8080...${NC}"
        sudo fuser -k 8080/tcp
        sleep 3

        echo -e "${CYAN}[3/6] -> Installing Gaianet...${NC}"
        curl -sSfL 'https://github.com/GaiaNet-AI/gaianet-node/releases/latest/download/install.sh' | bash
        sleep 2

        echo -e "${CYAN}[4/6] -> Setting PATH...${NC}"
        echo "export PATH=\$PATH:$HOME/gaianet/bin" >> "$HOME/.bashrc"
        export PATH="$PATH:$HOME/gaianet/bin"
        # Load PATH immediately in this script
        source "$HOME/.bashrc"
        sleep 2

        if ! command -v gaianet &> /dev/null; then
            echo -e "${CYAN}Error: gaianet not found!${NC}"
            exit 1
        fi

        echo -e "${CYAN}[5/6] -> Initializing node...${NC}"
        gaianet init --config https://raw.githubusercontent.com/GaiaNet-AI/node-configs/main/qwen2-0.5b-instruct/config.json  

        echo -e "${CYAN}[6/6] -> Starting node...${NC}"
        gaianet start

        # Create symlink for immediate access in all sessions
        echo -e "${CYAN}Linking gaianet to /usr/local/bin for immediate access...${NC}"
        sudo ln -sf "$HOME/gaianet/bin/gaianet" /usr/local/bin/gaianet

        # Show node info right away
        echo -e "\n${CYAN}Gaia node info:${NC}"
        gaianet info

        echo -e "\n${CYAN}Gaia node installed and started successfully!${NC}\n"
        ;;

    2)
        echo -e "\n${CYAN}Installing and starting farming script (Gaia bot)...${NC}\n"

        echo -e "${CYAN}Installing prerequisites...${NC}"
        sudo apt update
        sudo apt install -y git python3-pip
        pip3 install --user aiohttp

        echo -e "${CYAN}[1/5] -> Preparing directory...${NC}"
        BOT_DIR="$HOME/gaiabot"
        mkdir -p "$BOT_DIR"
        cd "$BOT_DIR"

        echo -e "${CYAN}[2/5] -> Cloning repository...${NC}"
        if [ -d ".git" ]; then
            git pull
        else
            git clone https://github.com/Evenorchik/gaiadomain.git .
        fi

        echo -e "${CYAN}[3/5] -> Configuring environment variables...${NC}"
        read -p "Enter your domain (e.g. mydomain.gaia.domains): " DOMAIN
        read -p "Enter your API key: " API_KEY
        if [ -z "$DOMAIN" ] || [ -z "$API_KEY" ]; then
            echo -e "${CYAN}Error: DOMAIN and API_KEY cannot be empty.${NC}"
            exit 1
        fi
        cat > env <<EOF
DOMAIN=$DOMAIN
API_KEY=$API_KEY
EOF

        echo -e "${CYAN}[4/5] -> Creating systemd service...${NC}"
        USERNAME=$(whoami)
        SERVICE_FILE="/etc/systemd/system/gaiabot.service"
        sudo bash -c "cat > $SERVICE_FILE <<EOF
[Unit]
Description=Gaia Bot
After=network.target

[Service]
EnvironmentFile=$BOT_DIR/env
ExecStart=/usr/bin/python3 $BOT_DIR/autobot.py
Restart=always
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$BOT_DIR

[Install]
WantedBy=multi-user.target
EOF"

        echo -e "${CYAN}[5/5] -> Enabling and starting service...${NC}"
        sudo systemctl daemon-reload
        sudo systemctl enable gaiabot.service
        sudo systemctl start gaiabot.service

        echo -e "\n${CYAN}Gaia bot service started successfully!${NC}"
        echo -e "${CYAN}To view logs:${NC} sudo journalctl -u gaiabot.service -f\n"
        ;;

    3)
        echo -e "\n${CYAN}Updating Gaia node...${NC}\n"
        sudo apt update && sudo apt upgrade -y
        echo -e "${CYAN}Gaia node packages updated.${NC}\n"
        ;;

    4)
        echo -e "\n${CYAN}Gaia node information:${NC}\n"
        gaianet info
        ;;

    5)
        echo -e "\n${CYAN}Deleting Gaia node...${NC}\n"
        gaianet stop
        rm -rf "$HOME/gaianet"
        echo -e "\n${CYAN}Gaia node deleted successfully.${NC}\n"
        ;;

    6)
        echo -e "\n${CYAN}Tailing Gaia bot logs...${NC}\n"
        sudo journalctl -u gaiabot.service -f
        ;;

    7)
        echo -e "\n${CYAN}Deleting farming script (Gaia bot)...${NC}\n"
        sudo systemctl stop gaiabot.service
        sudo systemctl disable gaiabot.service
        sudo rm /etc/systemd/system/gaiabot.service
        sudo systemctl daemon-reload
        rm -rf "$HOME/gaiabot"
        echo -e "\n${CYAN}Gaia bot removed successfully.${NC}\n"
        ;;

    *)
        echo -e "\n${CYAN}Error: Invalid choice!${NC}\n"
        ;;
esac
