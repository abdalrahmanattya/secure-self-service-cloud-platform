#!/bin/sh
set -eu

# The release is intentionally exact and the artifact is checked against the
# release's official SHA-256 manifest before it is used.
version='0.69.0'
destination=${1:?usage: scripts/install-conftest.sh DESTINATION}
os=$(uname -s)
arch=$(uname -m)

case "${os}:${arch}" in
  Linux:x86_64) artifact="conftest_${version}_Linux_x86_64.tar.gz" ;;
  Linux:aarch64|Linux:arm64) artifact="conftest_${version}_Linux_arm64.tar.gz" ;;
  Darwin:x86_64) artifact="conftest_${version}_Darwin_x86_64.tar.gz" ;;
  Darwin:arm64) artifact="conftest_${version}_Darwin_arm64.tar.gz" ;;
  *)
    echo "Unsupported Conftest platform: ${os}/${arch}" >&2
    exit 2
    ;;
esac

release_url="https://github.com/open-policy-agent/conftest/releases/download/v${version}"
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT HUP INT TERM

curl --fail --location --silent --show-error "${release_url}/${artifact}" --output "${workdir}/${artifact}"
curl --fail --location --silent --show-error "${release_url}/checksums.txt" --output "${workdir}/checksums.txt"
grep "  ${artifact}$" "${workdir}/checksums.txt" > "${workdir}/expected"
(
  cd "${workdir}"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum --check expected
  else
    shasum -a 256 --check expected
  fi
)
tar -xzf "${workdir}/${artifact}" -C "${workdir}"
install -m 0755 "${workdir}/conftest" "${destination}"
"${destination}" --version
