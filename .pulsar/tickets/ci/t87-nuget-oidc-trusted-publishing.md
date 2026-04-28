---
id: T87
title: Switch NuGet publishing from API key to OIDC trusted publishing
status: ready
depends_on: [T86]
---

# T87: Switch NuGet publishing from API key to OIDC trusted publishing

## Goal

Replace the long-lived `NUGET_API_KEY` secret with OIDC trusted publishing for NuGet.org, matching the npm OIDC pattern already in use for UPM packages. Eliminates a credential that needs rotation and reduces secret sprawl.

## Context

T86 implements the content-hash publish pipeline using a traditional NuGet API key (`NUGET_API_KEY` repository secret) because OIDC trusted publishing is still in gradual rollout on nuget.org and the account (`tylerhatch`) does not yet have access to the feature.

NuGet OIDC trusted publishing uses the `NuGet/login@v1` GitHub Action to exchange a GitHub OIDC token for a short-lived NuGet API key (~1 hour). Requires `id-token: write` permission (already present in the workflow) and a `NUGET_USER` secret (or hardcoded username). The trusted publishing policy is configured on nuget.org under Profile → Trusted Publishing.

The workflow already has `id-token: write` for npm provenance publishing, so the only changes are:
1. Add the `NuGet/login@v1` step
2. Replace `--api-key ${{ secrets.NUGET_API_KEY }}` with `--api-key ${{ steps.nuget-login.outputs.NUGET_API_KEY }}`
3. Remove the `NUGET_API_KEY` repository secret

## Key files

- `.github/workflows/publish-upm.yml` — publish workflow (swap API key for OIDC login step)

## Done when

- [ ] Workflow uses `NuGet/login@v1` instead of `NUGET_API_KEY` secret
- [ ] `NUGET_API_KEY` repository secret removed
- [ ] `NUGET_USER` secret (or hardcoded username) configured
- [ ] Trusted publishing policy configured on nuget.org for `PlaceframeApiClient`
- [ ] Successful publish via OIDC confirmed

## Next step

NuGet trusted publishing became generally available in late 2025. Log into nuget.org as `tylerhatch`, go to Profile → Trusted Publishing, and configure a policy for the Placeframe repository. Then apply the workflow changes described above.
