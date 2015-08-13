#!/bin/bash 

while [[ true ]]; do
	sudo kill -SIGUSR1 $(pidof swave2)
done
