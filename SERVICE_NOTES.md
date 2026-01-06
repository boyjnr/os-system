# Como instalar o service (systemd --user recomendado no WSL2)

mkdir -p ~/.config/systemd/user
cp os-system.service ~/.config/systemd/user/os-system.service

systemctl --user daemon-reload
systemctl --user enable --now os-system.service

journalctl --user -u os-system.service -f
systemctl --user status os-system.service

# Para parar:
# systemctl --user stop os-system.service
