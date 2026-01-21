#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/uint2.h>

namespace DotNet::Unity::Mathematics {
struct uint2;
}
namespace DotNet::Unity::Mathematics {
struct uint2x2;
}

namespace DotNet::Unity::Mathematics {

struct uint2x2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_P1cAnApbSLA3Xc3DztNMzw)(const ::DotNet::Unity::Mathematics::uint2* c0, const ::DotNet::Unity::Mathematics::uint2* c1, ::DotNet::Unity::Mathematics::uint2x2* pReturnValue, void** reinteropException);
  public: static uint2x2 Construct(const ::DotNet::Unity::Mathematics::uint2& c0, const ::DotNet::Unity::Mathematics::uint2& c1);
  public: ::DotNet::Unity::Mathematics::uint2 c0;
  public: ::DotNet::Unity::Mathematics::uint2 c1;
};

} // namespace DotNet::Unity::Mathematics


