Vagrant.configure("2") do |config|
  config.vm.box = "custom-box"

  # Первая машина
  config.vm.define "hiplet20025" do |test_server|
    test_server.vm.hostname = "hiplet20025"
    test_server.vm.network "private_network", ip: "192.168.56.101" # Статический IP

    test_server.vm.provision "shell", inline: <<-SHELL
        echo -e "vagrant\nvagrant" | passwd root
        sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
        sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
        service ssh restart
    SHELL
  end

  # Вторая машина
#   config.vm.define "hiplet20026" do |test_server2|
#     test_server2.vm.hostname = "hiplet20026"
#     test_server2.vm.network "private_network", ip: "192.168.56.102" # Статический IP
#
#     test_server2.vm.provision "shell", inline: <<-SHELL
#         echo -e "vagrant\nvagrant" | passwd root
#         sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
#         sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
#         service ssh restart
#     SHELL
#   end
end