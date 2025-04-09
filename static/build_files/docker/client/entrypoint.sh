#!/bin/sh

USER_ID=${UID:-1000}
GROUP_ID=${GID:-1000}

echo "Executing entrypoint as: $(id)"
groupmod --gid "$GROUP_ID" hydrus
usermod --uid "$USER_ID" --gid "$GROUP_ID" hydrus
echo "Hydrus will start with UID/GID : $USER_ID/$GROUP_ID"

if [ $USER_ID !=  1000 ] && [ $GROUP_ID != 1000 ]; then
  echo "Modifying /opt/hydrus permissions, excluding /opt/hydrus/db/*"
  find /opt/hydrus/ -path "/opt/hydrus/db/*" -prune -o -exec chown hydrus:hydrus "{}" \;
  echo "Modifying /opt/noVNC permissions for consistency"
  find /opt/noVNC/ -exec chown hydrus:hydrus "{}" \;
  echo "Modifying /opt/venv permissions for consistency"
  find /opt/venv/ -exec chown hydrus:hydrus "{}" \;
fi

PYTHON_MAJOR_VERSION=$(/opt/venv/bin/python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR_VERSION=$(/opt/venv/bin/python3 -c "import sys; print(sys.version_info.minor)")

cd /opt/hydrus/

if [ -f "/opt/hydrus/static/build_files/docker/client/patch.patch" ]; then
  echo "Patching Hydrus"
  patch -f -p1 -i /opt/hydrus/static/build_files/docker/client/patch.patch
fi

# Determine which requests patch file to use and warn on unsupported python version
if [ "$PYTHON_MAJOR_VERSION" == "3" ]; then
  if [ "$PYTHON_MINOR_VERSION" -lt 11 ]; then
    PATCH_FILE="/opt/hydrus/static/build_files/docker/client/requests.patch"
    if [ -f "$PATCH_FILE" ]; then
      echo "Find and apply requests noproxy patch for py 3.10 and below"
      cd $(/opt/venv/bin/python3 -c "import sys; import requests; print(requests.__path__[0])")
      patch -f -p2 -i "$PATCH_FILE"
    fi
  elif [ "$PYTHON_MINOR_VERSION" -eq 11 ]; then
    PATCH_FILE="/opt/hydrus/static/build_files/docker/client/requests.311.patch"
    if [ -f "$PATCH_FILE" ]; then
      echo "Find and apply requests noproxy patch for py 3.11"
      cd $(/opt/venv/bin/python3 -c "import sys; import requests; print(requests.__path__[0])")
      patch -f -i "$PATCH_FILE"
    fi
  elif [ "$PYTHON_MINOR_VERSION" -eq 12 ]; then
    PATCH_FILE="/opt/hydrus/static/build_files/docker/client/requests.311.patch"
    if [ -f "$PATCH_FILE" ]; then
      echo "Find and apply requests noproxy patch for py 3.12"
      cd $(/opt/venv/bin/python3 -c "import sys; import requests; print(requests.__path__[0])")
      patch -f -i "$PATCH_FILE"
    fi
  else
    echo "Unsupported Python minor version: $PYTHON_MINOR_VERSION"
  fi
else
  echo "Unsupported Python major version: $PYTHON_MAJOR_VERSION"
fi
cd /opt/hydrus/

<<<<<<< HEAD
exec supervisord -c /etc/supervisord.conf
=======
#if [ $USER_ID !=  0 ] && [ $GROUP_ID != 0 ]; then
#  find /opt/hydrus/ -not -path "/opt/hydrus/db/*" -exec chown hydrus:hydrus "{}" \;
#fi

ENV_DB_DIR=${DB_DIR}
ENV_HYDRUS_EXTRA=${HYDRUS_EXTRA}

START_HYDRUS_CMD="python3 /opt/hydrus/hydrus_client.py --db_dir $ENV_DB_DIR $ENV_HYDRUS_EXTRA"

echo "Hydrus command is:\n$START_HYDRUS_CMD"

exec xpra start --start-child="$START_HYDRUS_CMD" --bind-tcp=0.0.0.0:2222 --no-daemon --exit-with-children
>>>>>>> 605b00d2 (remove sshd and supervisor use only tcp)
