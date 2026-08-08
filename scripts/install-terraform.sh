#!/bin/sh
set -eu

# Exact CLI release; verify the official HashiCorp SHA-256 manifest.
version='1.15.8'
destination=${1:?usage: scripts/install-terraform.sh DESTINATION}
case "$(uname -s):$(uname -m)" in
  Linux:x86_64) artifact="terraform_${version}_linux_amd64.zip" ;;
  Darwin:arm64) artifact="terraform_${version}_darwin_arm64.zip" ;;
  Darwin:x86_64) artifact="terraform_${version}_darwin_amd64.zip" ;;
  *) echo "Unsupported Terraform platform" >&2; exit 2 ;;
esac
release_url="https://releases.hashicorp.com/terraform/${version}"
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT HUP INT TERM
curl --fail --location --silent --show-error "${release_url}/${artifact}" --output "${workdir}/${artifact}"
curl --fail --location --silent --show-error "${release_url}/terraform_${version}_SHA256SUMS" --output "${workdir}/SHA256SUMS"
grep "  ${artifact}\$" "${workdir}/SHA256SUMS" > "${workdir}/expected"
(
  cd "${workdir}"
  if command -v sha256sum >/dev/null 2>&1; then sha256sum --check expected; else shasum -a 256 --check expected; fi
)
unzip -q "${workdir}/${artifact}" -d "${workdir}"
install -m 0755 "${workdir}/terraform" "${destination}"
"${destination}" version
