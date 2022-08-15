#!/bin/bash --login
# The --login ensures the bash configuration is loaded,
# enabling Conda.


# Enable strict mode.
set -euo pipefail
# ... Run whatever commands ...

# Temporarily disable strict mode and activate conda:
set +euo pipefail
conda activate pyart_env

# Re-enable strict mode:
set -euo pipefail

# exec the final command:
exec FLASK_APP=server.py flask run -h 0.0.0.0 -p 5000

