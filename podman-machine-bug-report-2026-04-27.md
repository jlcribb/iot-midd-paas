## Title

macOS arm64: `podman machine start` reports success, but machine is not usable with either `applehv` or `libkrun`

## Environment

- Podman: `5.8.2`
- Install method: official macOS ARM64 pkg installer
- OS: `macOS 26.4.1 (25E253)`
- Arch: `arm64`
- Host model seen in local diagnostic report: `Mac15,3`

## Summary

On this Mac, `podman machine init` completes successfully, and `podman machine start` also reports success, but the machine is not actually usable afterward.

I reproduced this with both providers:

- `applehv`: guest falls into early boot/emergency mode; `podman ps` and `podman machine ssh` fail afterward.
- `libkrun`: guest reaches `multi-user.target` and `ready.service` in the serial log, but the machine still never becomes usable from the host side; SSH handshake resets and the Podman socket never becomes reachable.

In both cases, Podman ends up with a machine entry that looks started or "currently starting", but the connection is unusable.

## Reproduction

### Clean reinstall

```bash
rm -rf ~/.config/containers
rm -rf ~/.local/share/containers
rm -rf ~/.cache/containers
rm -rf ~/.ssh/podman*
```

Reinstalled with the official pkg:

```bash
sudo installer -pkg /tmp/podman-installer-macos-arm64.pkg -target /
/opt/podman/bin/podman --version
# podman version 5.8.2
```

### Provider 1: `applehv`

```bash
/opt/podman/bin/podman machine init
/opt/podman/bin/podman machine start
/opt/podman/bin/podman machine list
/opt/podman/bin/podman machine ssh echo ok
/opt/podman/bin/podman ps
```

Observed behavior:

- `podman machine init` completes
- `podman machine start` prints:

```text
Machine "podman-machine-default" started successfully
```

- But then:

```text
$ /opt/podman/bin/podman machine list
NAME                     VM TYPE     CREATED        LAST UP     CPUS  MEMORY  DISK SIZE
podman-machine-default*  applehv     ...            Never       4     2GiB    100GiB

$ /opt/podman/bin/podman machine ssh echo ok
Error: vm "podman-machine-default" is not running

$ /opt/podman/bin/podman ps
Error: unable to connect to Podman socket: failed to connect: dial tcp 127.0.0.1:51449: connect: connection refused
```

Important serial log evidence from the guest:

- `Ignition has failed`
- `systemd-fsck-root.service`
- `Failed to stat /dev/disk/by-uuid/...`
- guest drops into emergency mode

### Provider 2: `libkrun`

```bash
CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman machine init podman-machine-libkrun
CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman machine start podman-machine-libkrun
CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman machine list
CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman machine ssh podman-machine-libkrun echo ok
CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman --connection podman-machine-libkrun ps
```

Observed behavior:

- `init` completes
- `start` prints:

```text
Machine "podman-machine-libkrun" started successfully
```

- During debug start, `machine list` can show:

```text
NAME                     VM TYPE   CREATED   LAST UP             CPUS  MEMORY  DISK SIZE
podman-machine-libkrun*  libkrun   ...       Currently starting  4     2GiB    100GiB
```

- But connectivity still fails:

```text
$ CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman machine ssh podman-machine-libkrun echo ok
kex_exchange_identification: read: Connection reset by peer

$ CONTAINERS_MACHINE_PROVIDER=libkrun /opt/podman/bin/podman --connection podman-machine-libkrun ps
Error: unable to connect to Podman socket: failed to connect: ssh: handshake failed: read tcp 127.0.0.1:51643->127.0.0.1:51571: read: connection reset by peer
```

## Expected behavior

- `podman machine start` should only report success if the machine is actually usable
- after start, `podman machine ssh ...` should work
- after start, `podman ps` should connect successfully to the machine socket

## Actual behavior

- `podman machine start` reports success
- machine either ends in `Never` / `stopped` (`applehv`) or remains `Currently starting` / resets the SSH handshake (`libkrun`)
- daemon socket is unreachable from the host

## Additional debug observations

### `applehv`

`podman machine inspect podman-machine-default` ends with:

```json
"State": "stopped",
"LastUp": "0001-01-01T00:00:00Z"
```

`podman --log-level=debug machine start` shows the host launching `vfkit`, then waiting, but the guest serial log clearly shows the boot failure in early userspace.

### `libkrun`

`podman --log-level=debug machine start podman-machine-libkrun` shows:

- helper binary is `krunkit`
- Podman waits for ready notification
- guest serial log reaches `multi-user.target` and `ready.service`
- but host-side connectivity never becomes stable, and SSH ends up resetting

This suggests a different failure mode than `applehv`: the guest appears to boot, but the host/provider integration still fails.

## Local artifacts

Useful local logs from this reproduction:

- `/var/folders/_r/y_t7n03d4ssfxjfj1v0w4rqr0000gn/T/podman/podman-machine-default.log`
- `/var/folders/_r/y_t7n03d4ssfxjfj1v0w4rqr0000gn/T/podman/podman-machine-libkrun.log`
- `/Library/Logs/DiagnosticReports/podman_2026-04-27-211326_MacBook-Pro-de-Jose.diag`

If needed, I can attach the exact logs.

## Possibly related

The `applehv` serial failure matches a recent public log that shows the same `Ignition has failed` and `systemd-fsck-root.service` pattern:

- https://gist.github.com/leozhengliu-pixel/3bd314784e9f344b6f8badac5b70ddc0
