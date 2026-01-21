#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/uint3.h>

namespace DotNet::Unity::Mathematics {
struct uint3;
}
namespace DotNet::Unity::Mathematics {
struct uint3x3;
}

namespace DotNet::Unity::Mathematics {

struct uint3x3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_ZtWpbr50zCN2kT2S7fwByQ)(const ::DotNet::Unity::Mathematics::uint3* c0, const ::DotNet::Unity::Mathematics::uint3* c1, const ::DotNet::Unity::Mathematics::uint3* c2, ::DotNet::Unity::Mathematics::uint3x3* pReturnValue, void** reinteropException);
  public: static uint3x3 Construct(const ::DotNet::Unity::Mathematics::uint3& c0, const ::DotNet::Unity::Mathematics::uint3& c1, const ::DotNet::Unity::Mathematics::uint3& c2);
  public: ::DotNet::Unity::Mathematics::uint3 c0;
  public: ::DotNet::Unity::Mathematics::uint3 c1;
  public: ::DotNet::Unity::Mathematics::uint3 c2;
};

} // namespace DotNet::Unity::Mathematics


