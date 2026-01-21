#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct uint2;
}

namespace DotNet::Unity::Mathematics {

struct uint2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_41DRfMZ91WmKUsGkzEnbPw)(::std::uint32_t x, ::std::uint32_t y, ::DotNet::Unity::Mathematics::uint2* pReturnValue, void** reinteropException);
  public: static uint2 Construct(::std::uint32_t x, ::std::uint32_t y);
  public: ::std::uint32_t x;
  public: ::std::uint32_t y;
};

} // namespace DotNet::Unity::Mathematics


