# Validation

Validation in this repository means conformance to explicit, versioned rules for a deterministic toy scenario. It does not establish clinical correctness, safe real-world practice, or EMT/firefighter protocol authority.

The future validator should return structured `pass`, `warning`, or `fail` findings. A failed transition should leave authoritative scenario state unchanged while the attempt and result remain loggable.
