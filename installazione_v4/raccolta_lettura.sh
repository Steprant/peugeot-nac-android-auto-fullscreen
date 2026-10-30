#!/bin/sh
# PREPARED, NOT RUN ON A NAC. Requires an independently authorized shell.
# Reads selected state to stdout. Does not grant access, install or write files.
# Capture stdout on the host PC; do not redirect it to an internal NAC path.
# No CAN/UDS, OTP/fuse access, remount, service control or reboot.

LC_ALL=C
export LC_ALL
printf '%s\n' 'NAC read-only collection; no hardware compatibility attestation'
uname -a
id
printf '\n%s\n' 'Mount table'
cat /proc/mounts
printf '\n%s\n' 'Chosen secure boot information, raw bytes without interpretation'
if [ -r /proc/device-tree/chosen/secure-boot_info ]; then
    od -An -tx1 /proc/device-tree/chosen/secure-boot_info
else
    printf '%s\n' 'Unavailable; secure boot state remains unknown'
fi
printf '\n%s\n' 'Original component hashes'
for nac_audit_path in \
    /usr/lib/ovip/Android/libAndroidAutoAppLogic.so \
    /usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0 \
    /usr/lib/ovip/HMIInternal/HMIInternalApplication/libHMIInternalApplication.so.1.0.0 \
    /usr/lib/libswlprodext.so \
    /usr/lib/libsecuUtils.so \
    /usr/bin/HABInfo \
    /usr/bin/sem_dm_server
do
    if [ -r "$nac_audit_path" ]; then
        sha256sum "$nac_audit_path"
    else
        printf 'Unavailable: %s\n' "$nac_audit_path"
    fi
done
printf '\n%s\n' 'Existing Android Auto configuration and effective HMI calibration'
for nac_audit_path in /home/root/cfg /opt/ui/UIFwkTelecoding/hmi-telecoding.ini
do
    printf '%s\n' "$nac_audit_path"
    if [ -r "$nac_audit_path" ]; then
        cat "$nac_audit_path"
    else
        printf '%s\n' 'Unavailable or absent'
    fi
done
