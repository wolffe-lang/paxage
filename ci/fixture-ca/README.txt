Public TLS roots used only to bootstrap the isolated producer's package downloads.

Source: https://curl.se/ca/cacert-2026-10-20.pem
SHA-256: 796f1389bfea13c0ed78f663b765baaff54a508e5483786bd6ece73c5e3e3cbe
118 public CA certificates, extracted by curl from Mozilla's root store.
License: Mozilla Public License 2.0; https://curl.se/docs/caextract.html

This is not a package-repository root, a signing key, or the guest's TLS configuration.
The workflow checks these exact bytes before bootstrapping authenticated HTTPS APT
metadata from the fixed Ubuntu snapshot. The fixture bundle never exports this file.
