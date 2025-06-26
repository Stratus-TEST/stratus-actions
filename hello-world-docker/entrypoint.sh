#!/bin/sh
who=${1:-World}
echo "Hello, $who!"
echo "time=$(date)" >> $GITHUB_OUTPUT
