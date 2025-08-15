import requests
import socket
import subprocess
import re
import time
import platform

arduino_ip = ""


def get_ip_by_mac(mac_address):
    """Find IP address of a device by MAC address using ARP table."""
    try:
        output = subprocess.check_output(["arp", "-a"], text=True)
        
        if platform.system() == "Windows":
            # Windows ARP output: matches both colon and hyphen separated MAC addresses
            pattern = re.compile(r"\(?(\d+\.\d+\.\d+\.\d+)\)?\s+([\da-fA-F]{2}(?:[:-][\da-fA-F]{2}){5})")
        else:
            # macOS ARP output: expects MAC addresses with colons and the "at" keyword
            pattern = re.compile(r"\((.*?)\)\s+at\s+([0-9A-Fa-f:]{17})")

        for match in pattern.findall(output):
            ip, mac = match
            if mac.lower() == mac_address.lower():
                return ip  # Return the matching IP address

    except subprocess.CalledProcessError:
        return None

    return None  # If no match found


def ensure_arduino_connection(timeout=30, interval=5) -> str:
    """
    Ensures that the Arduino is connected before proceeding.

    :param timeout: Maximum time (seconds) to wait for a connection.
    :param interval: Time (seconds) between each retry.
    :return: The Arduino's IP address if found, otherwise None.
    """
    mac_address = "9c-9c-1f-c1-16-e4"  # Arduino MAC address
    start_time = time.time()
    ip_from_mac = None

    while (time.time() - start_time) < timeout:
        ip_from_mac = get_ip_by_mac(mac_address)
        if ip_from_mac:
            print(f"Arduino detected! IP Address: {ip_from_mac}")
            return ip_from_mac

        print(f"Waiting for Arduino to connect... (Retrying in {interval}s)")
        time.sleep(interval)

    print(f"Arduino not found within {timeout} seconds.")
    return ""


def sendCmdToArduinoCar(command: str = "") -> str:
    """
    Sends the command to the Arduino RC car via TCP.

    :param command: The command to send (jaw, brow, bite, blink, or empty for stop).
    :param arduino_ip: The IP address of the Arduino.
    """

    global arduino_ip
    # arduino_ip = "192.168.221.18"

    # Ensure connection to Arduino before accepting input
    if arduino_ip == "":
        print("\tChecking IP")
        arduino_ip = ensure_arduino_connection()
        if arduino_ip == "":
            print("No connection to Arduino. Cannot send command.")
            return

    # arduino_ip = ensure_arduino_connection()
    arduinoHTTPServerPort = 23

    if command in ["jaw", "brow", "bite", "blink", ""]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # 10-second timeout
                s.connect((arduino_ip, arduinoHTTPServerPort))
                s.sendall((command + "\n").encode())
                response = s.recv(2048).decode()
                print("Arduino Response:", response)
                return response

        except socket.timeout:
            print("Timeout: Connection to Arduino failed.")
            arduino_ip = ""
            return ""

        except Exception as e:
            print("Error sending command to Arduino:", e)
            arduino_ip = ""
            return ""

if __name__ == '__main__':
    userInput = ""

    while userInput != "stop":
        userInput = str(input("Enter jaw/brow/bite/blink/'" "': "))
        sendCmdToArduinoCar(command=userInput)
