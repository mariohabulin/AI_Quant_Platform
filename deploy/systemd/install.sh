#!/usr/bin/env bash
set -euo pipefail

repo_dir=/opt/ai-alpha
unit_source=/opt/ai-alpha/deploy/systemd
unit_target=/etc/systemd/system
config_target=/etc/ai-alpha
runtime_dir=/var/lib/ai-alpha
service_user=ai-alpha

if [[ ${EUID} -ne 0 ]]; then
    echo "Cloud supervision installation must run as root." >&2
    exit 1
fi

if [[ ! -x "${repo_dir}/.venv/bin/python" ]]; then
    echo "Validated Python environment is missing at ${repo_dir}/.venv." >&2
    exit 1
fi

if ! id -u "${service_user}" >/dev/null 2>&1; then
    useradd --system --user-group --home-dir "${runtime_dir}" --shell /usr/sbin/nologin "${service_user}"
fi

install -d -o "${service_user}" -g "${service_user}" -m 0700 "${runtime_dir}"
chown -R "${service_user}:${service_user}" "${runtime_dir}"
install -d -o root -g root -m 0755 "${config_target}"
install -o root -g root -m 0644 "${unit_source}/ai-alpha-paper.env" "${config_target}/ai-alpha-paper.env"

systemd-analyze verify \
    "${unit_source}/ai-alpha-paper.service" \
    "${unit_source}/ai-alpha-monitor.service" \
    "${unit_source}/ai-alpha-monitor.timer"

install -m 0644 "${unit_source}/ai-alpha-paper.service" "${unit_target}/ai-alpha-paper.service"
install -m 0644 "${unit_source}/ai-alpha-monitor.service" "${unit_target}/ai-alpha-monitor.service"
install -m 0644 "${unit_source}/ai-alpha-monitor.timer" "${unit_target}/ai-alpha-monitor.timer"
systemctl daemon-reload

echo "AI Alpha supervision units installed but not started or enabled."
echo "Review deploy/systemd/README.md before controlled activation."
