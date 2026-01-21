#pragma once





namespace DotNet::Unity::Collections {

enum class Allocator {
  Invalid = 0,
  None = 1,
  Temp = 2,
  TempJob = 3,
  Persistent = 4,
  AudioKernel = 5,
  Domain = 6,
  FirstUserIndex = 64,
};

} // namespace DotNet::Unity::Collections


