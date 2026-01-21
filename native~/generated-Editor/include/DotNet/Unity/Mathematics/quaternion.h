#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/float4.h>



namespace DotNet::Unity::Mathematics {

struct quaternion {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: ::DotNet::Unity::Mathematics::float4 value;
};

} // namespace DotNet::Unity::Mathematics


