import subprocess

def execute_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
        print(f"Executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e}")

commands = [
    "sudo ifconfig ens192 up",
    "sudo ifconfig ens224 up",
    "sudo ip link add br0 type bridge",
    "sudo ip link set br0 up",
    "sudo ip link set dev ens192 master br0",
    "sudo ip link set dev ens224 master br0",
    "sudo dhclient br0",
    "sudo brctl show",
    "sudo brctl addif br0 ens192",
    "sudo brctl addif br0 ens224",
    "sudo echo 1 > /proc/sys/net/ipv4/ip_forward",
    "sudo ip addr add 10.10.10.17/24 dev br0"
]

for cmd in commands:
    execute_command(cmd)
