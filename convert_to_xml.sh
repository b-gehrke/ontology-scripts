#!/usr/bin/env bash

DIR=${1:-.}

find "$DIR" -name "*.owl" -exec bash -c 'echo Converting "$0" && robot convert --input {} --output "$(dirname $0)/$(basename $0 .owl).owx"' {} \;