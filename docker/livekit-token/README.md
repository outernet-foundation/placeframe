# placeframe-livekit-token

LiveKit token issuer sidecar. Mints short-lived participant JWTs for LiveKit rooms so XR clients can join the self-hosted LiveKit data-channel relay.

Standalone by design — no dependency on other placeframe Python packages — so it can be lifted into a MakeItSing-owned compose layer when compose composition lands.
