#!/bin/bash

set -e

if [ "$1" = 'splunk' ]; then
  shift
  sudo -HEu ${SPLUNK_USER} ${SPLUNK_HOME}/bin/splunk "$@"
elif [ "$1" = 'start-service' ]; then
  # If user changed SPLUNK_USER to root we want to change permission for SPLUNK_HOME
  if [[ "${SPLUNK_USER}:${SPLUNK_GROUP}" != "$(stat --format %U:%G ${SPLUNK_HOME})" ]]; then
    chown -R ${SPLUNK_USER}:${SPLUNK_GROUP} ${SPLUNK_HOME}
  fi

  # If version file exists already - this Splunk has been configured before
  __configured=false
  if [[ -f ${SPLUNK_HOME}/etc/splunk.version ]]; then
    __configured=true
  fi

  __license_ok=false
  # If these files are different override etc folder (possible that this is upgrade or first start cases)
  # Also override ownership of these files to splunk:splunk
  if ! $(cmp --silent /var/opt/splunk/etc/splunk.version ${SPLUNK_HOME}/etc/splunk.version); then
    cp -fR /var/opt/splunk/etc ${SPLUNK_HOME}
  else
    __license_ok=true
  fi

  chown -R ${SPLUNK_USER}:${SPLUNK_GROUP} ${SPLUNK_HOME}/etc
  chown -R ${SPLUNK_USER}:${SPLUNK_GROUP} ${SPLUNK_HOME}/var

  if tty -s; then
    __license_ok=true
  fi

  if [[ "$SPLUNK_START_ARGS" == *"--accept-license"* ]]; then
    __license_ok=true
  fi

  if [[ $__license_ok == "false" ]]; then
    cat << EOF
Splunk Enterprise
==============

  Available Options:

      - Launch container in Interactive mode "-it" to review and accept
        end user license agreement
      - If you have reviewed and accepted the license, start container
        with the environment variable:
            SPLUNK_START_ARGS=--accept-license

  Usage:

    docker run -it outcoldman/splunk:latest
    docker run --env SPLUNK_START_ARGS="--accept-license" outcoldman/splunk:latest

EOF
    exit 1
  fi

  if [[ $__configured == "false" ]]; then
    sudo -HEu ${SPLUNK_USER} ${SPLUNK_HOME}/bin/splunk version ${SPLUNK_START_ARGS}
    sudo -HEu ${SPLUNK_USER} sh -c "${SPLUNK_HOME}/bin/splunk cmd python /opt/splunk/bin/configure.py before_start"
  fi

  sudo -HEu ${SPLUNK_USER} ${SPLUNK_HOME}/bin/splunk start ${SPLUNK_START_ARGS}
  trap "sudo -HEu ${SPLUNK_USER} ${SPLUNK_HOME}/bin/splunk stop" SIGINT SIGTERM EXIT

  if [[ $__configured == "false" ]]; then
    sudo -HEu ${SPLUNK_USER} sh -c "${SPLUNK_HOME}/bin/splunk cmd python /opt/splunk/bin/configure.py after_start"
  fi

  sudo -HEu ${SPLUNK_USER} tail -n 0 -f ${SPLUNK_HOME}/var/log/splunk/splunkd_stderr.log &
  wait
else
  "$@"
fi
