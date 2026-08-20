using Newtonsoft.Json;
using PlaceframeApiClient.Model;

namespace Placeframe.Client
{
    public static class ManifestHelpers
    {
        // The reconstructions.manifest column is a jsonb whose shape is owned by the repo
        // Pydantic class core.reconstruction_manifest.Manifest ({options, metrics}). The
        // OpenAPI generator surfaces it as Dictionary<string, Object> here, so we round-trip
        // through JSON to recover the typed sub-payloads for the inspector views.
        public static ReconstructionOptions ExtractOptions(ReconstructionReadWithQueue reconstruction) =>
            ExtractTyped<ReconstructionOptions>(reconstruction, "options") ?? new ReconstructionOptions();

        public static ReconstructionMetrics ExtractMetrics(ReconstructionReadWithQueue reconstruction) =>
            ExtractTyped<ReconstructionMetrics>(reconstruction, "metrics") ?? new ReconstructionMetrics();

        private static T ExtractTyped<T>(ReconstructionReadWithQueue reconstruction, string key)
            where T : class
        {
            if (reconstruction == null || reconstruction.Manifest == null)
                return null;
            if (!reconstruction.Manifest.TryGetValue(key, out var raw) || raw == null)
                return null;
            return JsonConvert.DeserializeObject<T>(JsonConvert.SerializeObject(raw));
        }
    }
}
