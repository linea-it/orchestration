#!/bin/bash --login

# if any of the commands in your code fails for any reason, the entire script fails
set -o errexit
# fail exit if one of your pipe command fails
set -o pipefail
# exits if any of your variables is not set
set -o nounset

echo "HOST: "$HOST
echo "LOG_DIR: "$LOG_DIR
echo "BASE_DIR: "$BASE_DIR

exec "$@"