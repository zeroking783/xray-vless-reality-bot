Vagrant.configure("2") do |config|
  config.vm.box = "custom-box"

  config.vm.define "hiplet20025" do |test_server|
    test_server.vm.hostname = "hiplet20025"
    test_server.vm.network "private_network", type: "dhcp"

    config.vm.network "forwarded_port", guest: 22, host: 2200
    
    config.vm.provision "shell", inline: <<-SHELL
        echo -e "vagrant\nvagrant" | passwd root
        sed -in 's/PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
        sed -in 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
        service ssh restart
    SHELL
  end
end
