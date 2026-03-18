#!/usr/bin/env bash
#
# agent-vm.setup.sh: Package installation script that runs inside the base VM
# Inspired by https://github.com/sylvinus/agent-vm
# And https://github.com/anthropics/claude-code/blob/main/.devcontainer/Dockerfile
#
# This script is executed inside the VM.
#

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Disable needrestart's interactive prompts
sudo mkdir -p /etc/needrestart/conf.d
echo '$nrconf{restart} = '"'"'a'"'"';' | sudo tee /etc/needrestart/conf.d/no-prompt.conf > /dev/null

echo "Installing base packages..."
sudo apt-get update
sudo apt-get install -y \
  git curl jq zsh \
  wget build-essential \
  python3 python3-pip python3-venv \
  ripgrep fd-find htop \
  unzip zip \
  ca-certificates \
  iptables && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

sudo apt-get install -y --no-install-recommends \
  less \
  procps \
  fzf \
  man-db \
  gnupg2 \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  nano \
  vim \
  && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

# Github CLI
sudo mkdir -p -m 755 /etc/apt/keyrings \
	&& out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
	&& cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& sudo mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y

GIT_DELTA_VERSION=0.18.2
ARCH=$(dpkg --print-architecture)
wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"
sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"
rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"


# Set zsh as default shell
sudo rm -rf $HOME/.oh-my-zsh
sudo chsh -s /usr/bin/zsh "$(whoami)"

# Set the default shell to zsh rather than sh
export SHELL=/bin/zsh

# Set the default editor and visual
export EDITOR=nano
export VISUAL=nano

# Default powerline10k theme
export  ZSH_IN_DOCKER_VERSION=1.2.0
sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install OpenCode
echo "Installing OpenCode..."
sudo snap install node --classic
sudo npm install -g opencode-ai
# curl -fsSL https://opencode.ai/install | bash
echo 'export PATH=$HOME/.opencode/bin:$PATH' >> ~/.zshrc

# Add PATH to .zshenv so non-interactive shells (limactl shell vmname cmd) also find the tools
echo 'export PATH=$HOME/.local/bin:$HOME/.opencode/bin:$PATH' >> ~/.zshenv

echo "VM setup complete."
