# Unity logging package omits required NuGet deps from asmdef / package.json

**Severity**: low — silent footgun for a fresh consumer of the package.

**Location**: `packages/unity/Logging/Assets/Package/Runtime/Outernet.Logging.asmdef` (precompiledReferences) and `packages/unity/Logging/Assets/Package/package.json` (no dependency list).

**Symptom**: A new Unity project that adds the file-pathed UPM dep on `org.outernet.logging` fails to compile because `Serilog`, `Newtonsoft.Json`, and `Microsoft.Extensions.Logging.Abstractions` are not on the consumer's NuGetForUnity `packages.config`. The Logging asmdef has `autoReferenced: true` and an empty `precompiledReferences`, so it relies on the consumer happening to have already installed every Serilog / Microsoft.Extensions dep locally.

**Mechanism**: NuGetForUnity does not transitively resolve via UPM. `Log.cs:240-291` uses `Microsoft.Extensions.Logging.Abstractions`; `LokiSink.cs` uses `Newtonsoft.Json` and `Serilog`. None are declared in the package's asmdef or `package.json`. Today it works because `placeframe` apps already list these in their own `packages.config`.

**Fix sketch**: Document the required `packages.config` entries in the package README and (a) add `precompiledReferences` entries naming each Serilog/Newtonsoft DLL the package needs so a missing dep produces an asmdef-level error instead of a generic CS0246, or (b) ship a `packages.config` fragment under `Samples~/` for one-shot install.

**Verification**: Create a fresh Unity 6 project, add the UPM dep on `org.outernet.logging`, build. Assert the build fails with a clear "missing NuGet package X" diagnostic, not 50 random `error CS0246`s.
