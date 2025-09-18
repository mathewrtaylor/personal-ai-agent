#!/bin/bash
# fix-docker-permissions.sh

echo "🔧 Fixing Docker Permissions"
echo "============================="

# Check if docker group exists
if ! getent group docker > /dev/null 2>&1; then
    echo "➕ Creating docker group..."
    sudo groupadd docker
    echo "✅ Docker group created"
fi

# Check if user is in docker group
if groups $USER | grep -q docker; then
    echo "✅ User is already in docker group"
else
    echo "➕ Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo "✅ User added to docker group"
fi

# Start and enable Docker service
echo "🔄 Starting Docker service..."
sudo systemctl start docker 2>/dev/null || echo "Docker service may already be running or using a different init system"
sudo systemctl enable docker 2>/dev/null || echo "Could not enable Docker service (may be using a different init system)"

echo ""
echo "🧪 Testing Docker access..."
if docker ps >/dev/null 2>&1; then
    echo "✅ Docker access working correctly!"
    echo "You can now run ./setup.sh"
else
    echo "⚠️  Docker access still not working. Trying to fix with new group session..."
    echo "Starting new shell with docker group..."
    exec newgrp docker
fi
EOF