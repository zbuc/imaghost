#!/usr/bin/env bash

rm -rf ssl
mkdir ssl
cd ssl

ssh-keygen -b 2048 -t rsa -N "imaghost" -f imag.host.key
echo -e "\n\n\n\n\n\n\n" | openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout imag.host.key -out imag.host.key.crt
